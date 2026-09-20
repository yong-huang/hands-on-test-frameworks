#!/usr/bin/env python3
"""client.py — 结账流程客户端：结账要走「第三方支付网关」（经挡板）。

超时分支是本演示的灵魂：支付超时时不许报错崩溃，要走到「PENDING_RETRY 降级」——
这正是挡板磁带被手工编辑成超时后要验证的业务行为。
"""
from __future__ import annotations

import argparse
import sys
import uuid

import httpx


def checkout(base: str, timeout: float = 3.0, order: str | None = None) -> int:
    order = order or f"ORDER-{uuid.uuid4().hex[:6]}"
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.post(f"{base}/pay", json={"order": order, "amount": 9.9})
            r.raise_for_status()
            txn = r.json()["txn"]
            print(f"支付创建: 订单={order} txn={txn} status={r.json()['status']}")

            s = c.get(f"{base}/pay/status", params={"txn": txn})
            s.raise_for_status()
            print(f"状态查询: txn={txn} state={s.json()['state']}")
            print("结账完成")
            return 0
    except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
        detail = "网关超时" if isinstance(e, httpx.TimeoutException) else f"网关 {e.response.status_code}"
        print(f"支付创建: 订单={order} → {detail}")
        print(f"降级分支: {order} 标记 PENDING_RETRY（等待人工/定时补偿）")
        return 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="支付结账演示客户端")
    ap.add_argument("--mock", default="http://127.0.0.1:8901")
    ap.add_argument("--order", default=None, help="固定订单号（对比录制/回放输出时用）")
    args = ap.parse_args()
    sys.exit(checkout(args.mock, order=args.order))
