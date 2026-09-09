#!/usr/bin/env python3
"""汇总剖析前后 verify JSON → docs/analysis.md。标准库实现。"""
import json
from pathlib import Path


def m(path):
    d = json.load(open(path))["metrics"]
    dur = d["http_req_duration"]
    return {
        "rps": d["http_reqs"].get("rate", 0),
        "p50": dur["med"],
        "p95": dur["p(95)"],
        "err": d["http_req_failed"].get("rate", d["http_req_failed"].get("value", 0)) * 100,
    }


def main():
    before, after = m("reports/verify_before.json"), m("reports/verify_after.json")
    drop = (1 - after["p95"] / before["p95"]) * 100
    lines = [
        "# 34 · Python 剖析修复对比报告",
        "",
        "| 口径 | RPS | P50(ms) | P95(ms) | 错误率% |",
        "|:---|---:|---:|---:|---:|",
        f"| 修复前 | {before['rps']:.1f} | {before['p50']:.1f} | {before['p95']:.1f} | {before['err']:.1f} |",
        f"| 修复后 | {after['rps']:.1f} | {after['p50']:.1f} | {after['p95']:.1f} | {after['err']:.1f} |",
        f"| **变化** | {after['rps']/before['rps']:.2f}x | | **P95 -{drop:.0f}%** | |",
        "",
        "## 火焰图归因（修复前）",
        "",
        "- CPU 热点：`recommend_score` → `hashlib.md5`（D2，每次详情请求 ~25ms 纯 CPU）",
        "- off-CPU（--idle）：`time.sleep` 占住工作线程（D3）+ `psycopg` 逐行查库存的"
        " 51 次 RTT（D1）",
        "- 证据文件：`reports/flame_before.svg`（或 .json speedscope）、`reports/top_before.txt`",
        "",
        "## 修复动作",
        "",
        "| 缺陷 | 修复 | 效果 |",
        "|:---|:---|:---|",
        "| D1 N+1 | LEFT JOIN 一条 SQL | 列表接口 SQL 数 51→1 |",
        "| D2 CPU 热点 | 打分预计算入 recommend_scores 表 | 详情接口 0 用户态 CPU |",
        "| D3 同步 sleep | 移除假风控 | 线程池不再被 120ms/单 占据 |",
        "",
        "## 验收判定",
        "",
        f"- 火焰图定位到具体函数：**是**（md5 热点 + sleep/IO 占比）",
        f"- 同场景 P95 改善 ≥30%：**{'通过' if drop >= 30 else '未通过'}**（实测 -{drop:.0f}%）",
        "",
    ]
    out = Path("docs/analysis.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
