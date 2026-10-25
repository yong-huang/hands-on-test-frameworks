"""perf_budget.py —— 性能预算引擎：读预算、并发取样、统计断言、写报告。

「预算即测试」的核心：预算不是文档里的口头约定，而是可执行断言——
p95 超预算或错误率超标即红，报告带实测数字供审计。

用法：
    python perf_budget.py                # 对正常 SUT 跑预算检查
    python perf_budget.py --include-slow # 加上 1.5s 延迟端点（演示红路径）
产出：reports/perf_report.json / .md
"""
import argparse
import json
import subprocess
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
LABS_SUT = REPO / "labs/11_sut_app"
SUT_PORT = 8940
SUT_URL = f"http://127.0.0.1:{SUT_PORT}"


class Sut:
    """labs/11 SUT 生命周期：种子 + uvicorn + 健康等待，with 语法自动清理。"""

    def __init__(self):
        self.proc = None

    def __enter__(self):
        venv_py = str(REPO / ".venv/bin/python")
        app_dir = str(LABS_SUT / "app")
        db_path = LABS_SUT / "app" / "orders.db"
        subprocess.run([venv_py, "seed.py", "--db", str(db_path)],
                       cwd=app_dir, capture_output=True, timeout=10)
        self.proc = subprocess.Popen(
            [venv_py, "-m", "uvicorn", "main:app", "--host", "127.0.0.1",
             "--port", str(SUT_PORT), "--log-level", "warning"],
            cwd=app_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import httpx
        for _ in range(60):
            try:
                if httpx.get(f"{SUT_URL}/api/health", timeout=2).status_code == 200:
                    return self
            except Exception:
                pass
            time.sleep(0.25)
        self.proc.kill()
        raise RuntimeError("SUT 启动失败")

    def __exit__(self, *a):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()


def sample_endpoint(base_url: str, ep: dict, n: int, workers: int) -> list[dict]:
    """并发取样一个端点，返回 [{latency_ms, status}] 列表。"""
    url = base_url + ep["path"]
    method = ep.get("method", "GET")
    headers = ep.get("headers", {})

    def _one():
        t0 = time.perf_counter()
        try:
            r = httpx.request(method, url, headers=headers, timeout=10)
            return {"latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "status": r.status_code}
        except Exception:
            return {"latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                    "status": 0}

    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_one) for _ in range(n)]
        for f in as_completed(futures):
            results.append(f.result())
    return results


def p95(latencies: list[float]) -> float:
    """P95 = 排序后取第 95 百分位（最近邻法）。"""
    s = sorted(latencies)
    return s[min(int(len(s) * 0.95), len(s) - 1)]


def main():
    ap = argparse.ArgumentParser(description="性能预算检查器")
    ap.add_argument("--config", default=str(ROOT / "configs/budget.yaml"))
    ap.add_argument("--include-slow", action="store_true",
                    help="追加 /api/slow-config（1.5s 延迟）演示红路径")
    ap.add_argument("--base-url", default=None, help="覆盖 budget.yaml 的 base_url")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text())
    base_url = args.base_url or SUT_URL
    workers = cfg.get("concurrent", 10)
    n_per_ep = cfg.get("requests_per_endpoint", 20)
    endpoints = list(cfg["endpoints"])

    if args.include_slow:
        endpoints.append({"path": "/api/slow-config", "method": "GET",
                          "p95_ms": 200, "max_error_rate": 0.0,
                          "tag": "延迟注入"})

    print(f"性能预算检查（{len(endpoints)} 个接口 × {n_per_ep} 取样 × {workers} 并发）\n")

    sut = Sut()
    sut.__enter__()

    print(f"{'接口':<24}{'取样':>4}{'p95(ms)':>10}{'预算':>8}{'错误率':>8}{'预算':>8}  结果")
    print("-" * 78)

    report_rows = []
    all_pass = True
    for ep in endpoints:
        samples = sample_endpoint(base_url, ep, n_per_ep, workers)
        latencies = [s["latency_ms"] for s in samples]
        errors = sum(1 for s in samples if s["status"] >= 500)
        error_rate = errors / len(samples)
        p95_val = p95(latencies)
        p95_ok = p95_val <= ep["p95_ms"]
        err_ok = error_rate <= ep.get("max_error_rate", 0.05)
        ok = p95_ok and err_ok
        all_pass = all_pass and ok
        mark = "✅" if ok else "❌"
        tag = ep.get("tag", "")
        display = f"{ep['path']}{' [' + tag + ']' if tag else ''}"
        print(f"{display:<24}{len(samples):>4}{p95_val:>10.1f}{ep['p95_ms']:>8}"
              f"{error_rate:>7.1%}{ep.get('max_error_rate', 0):>7.0%}  {mark}")
        if not p95_ok:
            print(f"  ⛔ p95 {p95_val:.0f}ms 超预算 {ep['p95_ms']}ms（实测值 vs 预算值）")
        if not err_ok:
            print(f"  ⛔ 错误率 {error_rate:.1%} 超预算 {ep.get('max_error_rate', 0):.0%}")
        report_rows.append({"path": ep["path"], "method": ep.get("method", "GET"),
                            "samples": len(samples), "p95_ms": p95_val,
                            "budget_p95_ms": ep["p95_ms"],
                            "error_rate": round(error_rate, 4),
                            "budget_error_rate": ep.get("max_error_rate", 0),
                            "pass": ok})

    verdict = "✅ 全部达标" if all_pass else "❌ 存在超预算接口"
    print(f"\n{verdict}")

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    (out / "perf_report.json").write_text(json.dumps(
        {"generated_at": datetime.now().isoformat(timespec="seconds"),
         "endpoints": report_rows, "all_pass": all_pass},
        ensure_ascii=False, indent=2))
    (out / "perf_report.md").write_text(
        f"# 性能预算报告（{datetime.now().strftime('%Y-%m-%d %H:%M')}）\n\n"
        f"| 接口 | 取样 | p95(ms) | 预算(ms) | 错误率 | 结果 |\n"
        f"|:--|--:|--:|--:|--:|:--:|\n"
        + "\n".join(f"| {r['path']} | {r['samples']} | {r['p95_ms']:.1f} "
                     f"| {r['budget_p95_ms']} | {r['error_rate']:.1%} "
                     f"| {'✅' if r['pass'] else '❌'} |" for r in report_rows)
        + f"\n\n**{verdict}**\n")
    print(f"产物：reports/perf_report.json、reports/perf_report.md")
    sut.__exit__(None, None, None)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
