#!/usr/bin/env python3
"""canary.py — 灰度发布质量评估器：canary vs baseline 双判定（绝对+相对）。

架构师视角的一句话：**右移的终极问题是「灰度期间质量谁兜底、怎么兜」**——
答案是数据说话：对 baseline 与 canary 采同样的流量（读多写少的生产形状），
逐指标对比，绝对红线 + 相对比率双判定，输出放量/回滚与判定依据。
两个阈值都不可省：只有绝对阈值 → 环境差一档就误杀；只有相对比率 →
baseline 自己已经烂透时相对「健康」毫无意义。
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

import httpx
import yaml


def sample(base_url: str, n: int, mix: dict) -> dict:
    """按流量形状采样：错误率 + 延迟样本。POST 会清理自己（下单即删，不污染数据）。"""
    errors, lat = 0, []
    reqs = [("GET", "/api/health", None, None)] * int(n * mix["health"]) + \
           [("GET", "/api/orders", {"limit": 5}, None)] * int(n * mix["list"])
    creates = n - len(reqs)
    reqs += [("POST", "/api/orders", None,
              {"customer": f"canary-{i}", "item": "探针商品", "qty": 1, "price": 1.0})
             for i in range(creates)]
    with httpx.Client(timeout=5, trust_env=False) as c:
        for method, path, params, js in reqs:
            t0 = time.perf_counter()
            try:
                r = c.request(method, base_url + path, params=params, json=js)
                ok = r.status_code < 400
                if method == "POST" and ok:
                    c.delete(f"{base_url}/api/orders/{r.json()['id']}")
            except Exception:
                r, ok = None, False
            lat.append((time.perf_counter() - t0) * 1000)
            errors += 0 if ok else 1
    lat.sort()
    return {"n": len(lat), "errors": errors,
            "error_rate": errors / len(lat),
            "p50_ms": round(statistics.median(lat), 1),
            "p95_ms": round(lat[int(len(lat) * 0.95) - 1], 1)}


def judge(base: dict, canary: dict, th: dict) -> tuple[str, list[str]]:
    reasons = []
    ab, rel = th["absolute"], th["relative"]
    checks = [
        ("canary 错误率绝对红线", canary["error_rate"] <= ab["error_rate_max"],
         f"{canary['error_rate']:.1%} ≤ {ab['error_rate_max']:.0%}"),
        ("canary P95 绝对红线", canary["p95_ms"] <= ab["p95_ms_max"],
         f"{canary['p95_ms']}ms ≤ {ab['p95_ms_max']}ms"),
        ("错误率相对比率", canary["error_rate"] <= max(base["error_rate"] * rel["error_rate_ratio_max"],
                     base["error_rate"] + rel["error_rate_slack"]),
         f"{canary['error_rate']:.1%} vs baseline {base['error_rate']:.1%}×{rel['error_rate_ratio_max']}"),
        ("P95 相对比率", canary["p95_ms"] <= base["p95_ms"] * rel["p95_ratio_max"],
         f"{canary['p95_ms']}ms vs baseline {base['p95_ms']}ms×{rel['p95_ratio_max']}"),
    ]
    verdict = "✅ 放量（promote）"
    for name, ok, evidence in checks:
        if not ok:
            verdict = "⛔ 回滚（rollback）"
        reasons.append(f"{'✅' if ok else '❌'} {name}：{evidence}")
    return verdict, reasons


def main() -> int:
    ap = argparse.ArgumentParser(description="灰度发布质量评估器")
    base = Path(__file__).parent
    ap.add_argument("--baseline", default="http://127.0.0.1:8899")
    ap.add_argument("--canary", default="http://127.0.0.1:8903")
    ap.add_argument("--out", default=str(base / "reports"))
    args = ap.parse_args()

    th = yaml.safe_load((base / "configs/thresholds.yaml").read_text(encoding="utf-8"))
    n, mix = th["sample"]["n_requests"], th["sample"]["mix"]
    print(f"# ⚖️ 灰度质量评估：baseline={args.baseline} vs canary={args.canary}（每侧 {n} 采样）")
    b = sample(args.baseline, n, mix)
    c = sample(args.canary, n, mix)
    print(f"baseline: 错误率 {b['error_rate']:.1%}，P95 {b['p95_ms']}ms")
    print(f"canary  : 错误率 {c['error_rate']:.1%}，P95 {c['p95_ms']}ms")

    verdict, reasons = judge(b, c, th)
    print(f"\n# 判定：{verdict}")
    for r in reasons:
        print(f"- {r}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "canary_verdict.json").write_text(json.dumps(
        {"baseline": b, "canary": c, "verdict": verdict, "checks": reasons},
        ensure_ascii=False, indent=2), encoding="utf-8")
    ok = verdict.startswith("✅")
    print(f"\n>>> {'验收通过' if ok else '按设计回滚'}（报告在 {out/'canary_verdict.json'}）")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
