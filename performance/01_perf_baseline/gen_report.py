#!/usr/bin/env python3
"""读取 k6 --summary-export 的两个 JSON，生成 docs/baseline.md 基线报告。

用法：python3 gen_report.py <smoke_shop.json> <smoke_shorturl.json>
报告口径：RPS / P50 / P95 / P99 / 错误率 五指标（清单验收标准）。
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def metrics(data: dict) -> dict:
    m = data["metrics"]
    dur = m["http_req_duration"]
    # 兼容 k6 各版本的导出格式：rate 有时叫 rate，有时叫 value
    failed = m["http_req_failed"].get("rate", m["http_req_failed"].get("value", 0))
    return {
        "rps": round(m["http_reqs"].get("rate", 0), 1),
        "p50": round(dur["med"], 1),
        "p95": round(dur["p(95)"], 1),
        "p99": round(dur["p(99)"], 1),
        "err_rate": round(failed * 100, 2),
        "checks": round(m["checks"].get("rate", m["checks"].get("value", 0)) * 100, 2),
    }


def git_rev() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def table(name: str, m: dict) -> str:
    return (
        f"| **{name}** | {m['rps']} | {m['p50']} | {m['p95']} | {m['p99']} "
        f"| {m['err_rate']}% | {m['checks']}% |"
    )


def main() -> None:
    shop = metrics(load(sys.argv[1]))
    short = metrics(load(sys.argv[2]))
    lines = [
        "# 01 · 优化前基线报告（项目 1 验收物）",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 代码版本：{git_rev()}",
        "- 场景：k6 smoke，5 VU × 30s；shop 读写≈2:1，shorturl 跳转:创建≈9:1",
        "- 口径：service 级聚合（k6 summary-export），后续每个调优项目跑同一场景对比",
        "",
        "| 服务 | RPS | P50(ms) | P95(ms) | P99(ms) | 错误率 | checks 通过 |",
        "|:---|---:|---:|---:|---:|---:|---:|",
        table("perf-shop (FastAPI :8931)", shop),
        table("shorturl (Go :8932)", short),
        "",
        "## 后续项目登记表",
        "",
        "| 项目 | 动作 | P95 变化 | 备注 |",
        "|:---|:---|:---|:---|",
        "| 4 | Python 剖析修复 | ________ | |",
        "| 5 | Go pprof 修复 | ________ | |",
        "| 6 | 慢 SQL + 连接池 | ________ | |",
        "| 7 | 缓存 | ________ | |",
        "| 8 | 并发调参 | ________ | |",
        "| 9 | 泄漏修复 | ________ | |",
        "",
        "> 本报告每次 `./perf_baseline.sh observe` 重新生成；"
        "基线数字只在本机这套 compose 拓扑内有意义。",
        "",
    ]
    out = Path(__file__).parent / "docs" / "baseline.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"报告已写入 {out}")


if __name__ == "__main__":
    main()
