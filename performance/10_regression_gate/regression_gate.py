#!/usr/bin/env python3
"""🏁 性能门禁：当前压测结果 vs 基线（01 号实验产物），按 budget.yaml 判定。

用法：regression_gate.py <当前结果.json> <服务名> [--baseline 01 基线.json]
退出码：0=通过（绿），1=预算被击穿（红）——CI 门禁语义。
"""
import json
import sys
import tomllib
from pathlib import Path

BUDGET = Path(__file__).parent / "budget.toml"
BASELINE_DIR = Path(__file__).parent / "reports" / "baseline"
METRIC_MAP = {  # budget 键 → (基线文件, 当前文件)
    "shop": ("smoke_shop.json", "reports/gate_shop.json"),
    "shorturl": ("smoke_shorturl.json", "reports/gate_shorturl.json"),
}


def m(path):
    d = json.load(open(path))["metrics"]
    dur = d["http_req_duration"]
    return {
        "p95": dur["p(95)"],
        "rps": d["http_reqs"].get("rate", 0),
        "err": d["http_req_failed"].get("rate", d["http_req_failed"].get("value", 0)) * 100,
        "reqs": d["http_reqs"]["count"],
    }


def load_budget():
    with open(BUDGET, "rb") as f:
        return tomllib.load(f)


def main():
    svc = sys.argv[1]
    budget = load_budget()[svc]
    bfile, cfile = METRIC_MAP[svc]
    base = m(BASELINE_DIR / bfile)
    cur = m(cfile)

    failures = []
    if base["reqs"] < 100 or cur["reqs"] < 100:
        print(f"❌ 样本量不足（基线 {base['reqs']:.0f} / 当前 {cur['reqs']:.0f}），拒绝判定")
        sys.exit(1)

    p95_reg = (cur["p95"] - base["p95"]) / base["p95"] if base["p95"] else 0
    if p95_reg > budget["p95_regression_max"]:
        failures.append(f"P95 退化 {p95_reg*100:.0f}% > 预算 {budget['p95_regression_max']*100:.0f}%")
    if cur["err"] > budget["error_rate_max"] * 100:
        failures.append(f"错误率 {cur['err']:.2f}% > 预算 {budget['error_rate_max']*100:.0f}%")

    print(f"[{svc}] 基线 P95={base['p95']:.1f}ms ↔ 当前 P95={cur['p95']:.1f}ms "
          f"(退化 {p95_reg*100:+.0f}%)，错误率 {cur['err']:.2f}%")
    if failures:
        for f in failures:
            print(f"  ❌ {f}")
        print(f"🔴 [{svc}] 门禁不通过")
        sys.exit(1)
    print(f"🟢 [{svc}] 门禁通过")


if __name__ == "__main__":
    main()
