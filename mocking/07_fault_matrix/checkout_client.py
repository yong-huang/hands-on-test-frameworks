#!/usr/bin/env python3
"""带降级分支的结账客户端——故障矩阵的被测对象。

分支策略（每个分支就是一种「客户端对故障的态度」）：
- DIRECT_SUCCESS   正常应答（快速返回）
- SUCCESS_SLOW     应答成功但明显偏慢（记录慢调用）
- PENDING_RETRY    超时：重试后仍超时 → 落离线队列等待补偿
- CIRCUIT_OPEN     5xx：重试后仍 5xx → 熔断器打开，停止打这个依赖
- RATE_LIMITED     429：立即进入限流排队，不重试打爆对方
- FAIL_FAST        连接层断裂（重置/拒连）：快速失败，不重试
- FALLBACK_DEFAULT 200 但 body 破损：用默认值兜底，业务不崩
"""
import json
import time

import httpx

TIMEOUT_S = 0.5      # 客户端超时：> 200ms 慢档、< 3s 超时档
RETRIES = 2          # 超时/5xx 的重试次数
SLOW_THRESHOLD_S = 0.2


def checkout(base: str, order: str = "ORDER-FIXED-001") -> str:
    """执行一次结账，返回进入的分支名（矩阵断言的就是它）。"""
    last_timeout = False
    for attempt in range(RETRIES + 1):
        start = time.monotonic()
        try:
            r = httpx.post(f"{base}/pay", json={"order": order, "amount": 4200},
                           timeout=TIMEOUT_S, trust_env=False)
        except (httpx.ConnectError, httpx.RemoteProtocolError):
            return "FAIL_FAST"                      # 连接层断裂：快速失败
        except httpx.ReadTimeout:
            last_timeout = True                     # 超时：重试
            continue

        if r.status_code == 503:
            continue                                # 5xx：重试，耗尽即熔断
        if r.status_code == 429:
            return "RATE_LIMITED"                   # 限流：立即排队，不打爆对方
        if r.status_code == 200:
            try:
                body = r.json()
            except json.JSONDecodeError:
                return "FALLBACK_DEFAULT"           # 破损应答：默认值兜底
            if not body.get("txn"):
                return "FALLBACK_DEFAULT"
            elapsed = time.monotonic() - start
            if elapsed > SLOW_THRESHOLD_S:
                return "SUCCESS_SLOW"               # 成功但慢：记录慢调用
            return "DIRECT_SUCCESS"

    return "PENDING_RETRY" if last_timeout else "CIRCUIT_OPEN"


if __name__ == "__main__":
    import sys
    print(checkout(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:9700"))
