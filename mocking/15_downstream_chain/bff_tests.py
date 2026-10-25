#!/usr/bin/env python3
"""BFF 集成测试：同一套断言跑真模式与虚拟化模式。

三种预期形态：
  all-green   payment/risk/sms 三者正常值
  pay-fail    payment=PENDING_RETRY、其余正常（降级分支 1）
断言不看具体值来自谁——「BFF 在两种模式下行为一致」正是本实验的命题。
"""
import json
import sys

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9804"
EXPECT = sys.argv[2] if len(sys.argv) > 2 else "all-green"  # all-green | pay-fail
FAILURES = []


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


def main():
    r = httpx.post(f"{BASE}/checkout", json={"order_id": "ORD-AGG-001", "amount": 4200},
                   timeout=15, trust_env=False)
    body = r.json()
    print(f"  聚合应答：{json.dumps(body, ensure_ascii=False)}")

    if EXPECT == "all-green":
        check("payment 正常落账", body["payment"] not in (None, "PENDING_RETRY"),
              body["payment"])
        check("risk=approve", body["risk"] == "approve", body["risk"])
        check("sms 已发送", body["sms"] not in (None, "skipped"), body["sms"])
        check("无降级标记", body["degraded"] == [], str(body["degraded"]))
    elif EXPECT == "pay-fail":
        check("支付失败 → PENDING_RETRY（不崩）", body["payment"] == "PENDING_RETRY",
              body["payment"])
        check("risk 正常不受牵连", body["risk"] == "approve", body["risk"])
        check("sms 正常不受牵连", body["sms"] not in (None, "skipped"), body["sms"])
        check("降级标记恰好 1 项", body["degraded"] == ["pay"], str(body["degraded"]))

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项断言失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(f">>> [{EXPECT}] BFF 行为符合预期 ✅")


if __name__ == "__main__":
    main()
