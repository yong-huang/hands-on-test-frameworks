#!/usr/bin/env python3
"""故障注入矩阵驱动器：逐格注入 WireMock 故障 → 跑客户端 → 断言分支 → 出报告。

矩阵定义 = 7 行（无故障基线 + 6 类故障），每行声明「注入什么」与「客户端
必须进入哪个分支」。错格即红；全部通过后输出覆盖率报告（矩阵 Markdown）。
"""
import json
import sys

import httpx

BASE = "http://127.0.0.1:9700"
ADMIN = "http://127.0.0.1:9700/__admin"

from checkout_client import checkout  # noqa: E402

# (格子名, WireMock 响应定义, 预期分支, 一句话语义)
CELLS = [
    ("无故障基线", {"status": 200, "jsonBody": {"txn": "TXN-OK", "status": "ok"}},
     "DIRECT_SUCCESS", "正常应答直达"),
    ("延迟 200ms", {"status": 200, "fixedDelayMilliseconds": 200,
                    "jsonBody": {"txn": "TXN-SLOW", "status": "ok"}},
     "SUCCESS_SLOW", "慢但可用：记录慢调用"),
    ("超时 3s", {"status": 200, "fixedDelayMilliseconds": 3000,
                 "jsonBody": {"txn": "TXN-TIMEOUT", "status": "ok"}},
     "PENDING_RETRY", "超时重试后落离线队列"),
    ("HTTP 503", {"status": 503, "body": "service unavailable"},
     "CIRCUIT_OPEN", "重试耗尽即熔断"),
    ("HTTP 429", {"status": 429, "body": "too many requests"},
     "RATE_LIMITED", "立即限流排队，不重试"),
    ("畸形 JSON", {"status": 200, "body": '{"txn": "TXN-BROKEN", '},
     "FALLBACK_DEFAULT", "破损应答默认值兜底"),
    ("断连", {"fault": "CONNECTION_RESET_BY_PEER"},
     "FAIL_FAST", "连接层断裂快速失败"),
]


def inject(cell_response):
    """清空全部映射，注入当前格的单条 stub。"""
    httpx.delete(f"{ADMIN}/mappings", trust_env=False)
    stub = {"request": {"method": "POST", "urlPath": "/pay"}, "response": cell_response}
    r = httpx.post(f"{ADMIN}/mappings", json=stub, trust_env=False)
    r.raise_for_status()


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else BASE
    rows, failures = [], []
    print("① 逐格执行：注入 → 跑客户端 → 断言分支")
    for name, resp, expected, semantic in CELLS:
        inject(resp)
        branch = checkout(base)
        ok = branch == expected
        rows.append((name, expected, branch, ok, semantic))
        print(f"  {'✅' if ok else '❌'} [{name}] 注入后客户端分支 = {branch}"
              f"（预期 {expected}）—— {semantic}")
        if not ok:
            failures.append(name)

    covered_cells = sum(1 for r in rows if r[3])
    branches_hit = {r[2] for r in rows}
    print(f"\n② 覆盖率报告：格子 {covered_cells}/{len(rows)}，"
          f"触发分支 {len(branches_hit)}/{len(rows)}（每格一个专属分支）")

    lines = [
        "# 故障注入矩阵覆盖率报告", "",
        "| 格子 | 预期分支 | 实际分支 | 结果 | 语义 |",
        "|:---|:---|:---|:---:|:---|",
    ]
    lines += [f"| {n} | {e} | {b} | {'✅' if ok else '❌'} | {sem} |"
              for n, e, b, ok, sem in rows]
    lines += ["", f"覆盖率：格子 {covered_cells}/{len(rows)}；"
              f"分支 {len(branches_hit)}/{len(rows)}（"
              + "、".join(sorted(branches_hit)) + "）"]
    with open("reports/matrix.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("   报告已写入 reports/matrix.md")

    print()
    if failures:
        print(f"❌ {len(failures)} 格错答：{'、'.join(failures)}")
        sys.exit(1)
    print(">>> 验收：7 格逐格执行 ✅ 分支全部符合预期 ✅ 覆盖率 100% ✅")


if __name__ == "__main__":
    main()
