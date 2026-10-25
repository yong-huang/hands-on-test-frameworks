#!/usr/bin/env python3
"""关卡 5 · E2E 测试 —— 完整用户路径：下单 → 查回执，校验用户可见文本。

与关卡 4 的分工：E2E 走完整旅程（下单成功 → 打开回执），断言的是
**用户肉眼看到的东西**——回执文本必须是「应付 ¥80.09」这种两位小数形态。
float 脏值在回执上变成 ¥80.08999999999999，用户可直接截图报障。

复现：python gates/gate5_e2e.py
"""
import argparse
import re

import requests

from _server import start, stop

ITEMS = [19.99, 80.10]
RECEIPT_RE = re.compile(r"应付 ¥\d+\.\d{2}$")  # 精确两位小数，多一位就算不合格


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=["good", "bad"], default="bad")
    ap.add_argument("--port", type=int, default=8932)
    args = ap.parse_args()

    proc, base = start(args.impl, args.port)
    print(f"[关卡5 · E2E 测试] 用户旅程：下单 → 查回执（impl={args.impl}）")
    try:
        oid = requests.post(f"{base}/api/orders",
                            json={"prices": ITEMS, "coupon": True},
                            timeout=5).json()["id"]
        text = requests.get(f"{base}/api/orders/{oid}/receipt",
                            timeout=5).json()["text"]
        print(f"  ① POST /api/orders → 订单 #{oid}")
        print(f"  ② GET  /api/orders/{oid}/receipt → 回执文本：{text!r}")
        if RECEIPT_RE.fullmatch(text):
            print("  → 回执金额两位小数，用户看到的账单是对的：无缺陷可拦")
            print("RESULT: CLEAN_PASS")
        else:
            print("  → 回执金额形态异常：用户会直接看到脏账单，"
                  "缺陷在 E2E 层被拦下（此时修复要横跨展示与计算两层）")
            print("RESULT: INTERCEPTED")
    finally:
        stop(proc)


if __name__ == "__main__":
    main()
