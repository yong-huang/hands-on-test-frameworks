#!/usr/bin/env python3
"""关卡 4 · CI 接口测试 —— 黑盒 HTTP 断言：POST 下单，响应 total 必须精确到分。

本关不看代码，只打接口（这正是接口测试与单测的分工）：起 mini API
（注入被测实现）→ POST /api/orders → 断言响应 total 字符串 == "80.09"。
float 脏值会原样出现在 JSON 里（API 壳以字符串透传），此关拦下。

复现：python gates/gate4_api.py
"""
import argparse

import requests

from _server import start, stop

ITEMS = [19.99, 80.10]  # 与 configs/requirements.yaml 的下单场景一致


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=["good", "bad"], default="bad")
    ap.add_argument("--port", type=int, default=8931)
    args = ap.parse_args()

    proc, base = start(args.impl, args.port)
    print(f"[关卡4 · CI 接口测试] POST {base}/api/orders（impl={args.impl}）")
    try:
        resp = requests.post(f"{base}/api/orders",
                             json={"prices": ITEMS, "coupon": True}, timeout=5)
        body = resp.json()
        print(f"  HTTP {resp.status_code} 响应 total = {body['total']!r}")
        if body["total"] == "80.09":
            print("  → total 精确到分，断言通过：无缺陷可拦")
            print("RESULT: CLEAN_PASS")
        else:
            print("  → 断言 total == \"80.09\" 失败：缺陷在 CI 接口层被拦下，"
                  "需要进实现层定位数值类型问题")
            print("RESULT: INTERCEPTED")
    finally:
        stop(proc)


if __name__ == "__main__":
    main()
