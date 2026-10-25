#!/usr/bin/env python3
"""WS 替身演示客户端：全量接收 → 断线重连续传 → 心跳踢线，三场景全断言。"""
import asyncio
import json
import sys

import websockets

BASE = "ws://127.0.0.1:9751/ws"
FAILURES = []


def check(name, ok, detail=""):
    print(f"  {'✅' if ok else '❌'} {name}{(' — ' + detail) if detail else ''}")
    if not ok:
        FAILURES.append(name)


async def recv_until(ws, want_count, timeout=5.0):
    """收推送直到凑满 want_count 条（跳过服务端 ack 帧）。"""
    got = []
    while len(got) < want_count:
        raw = await asyncio.wait_for(ws.recv(), timeout)
        frame = json.loads(raw)
        if "push" in frame:
            got.append(frame["push"])
    return got


async def full_sequence():
    print("\n① 全量接收：订阅后按预设序列收满 5 条（内容 + 顺序断言）")
    async with websockets.connect(BASE) as ws:
        await ws.send(json.dumps({"action": "subscribe", "order_id": "ORD-1"}))
        events = await recv_until(ws, 5)
        seqs = [e["seq"] for e in events]
        stages = [e["stage"] for e in events]
        check("收满 5 条且 seq 递增 1..5", seqs == [1, 2, 3, 4, 5], f"实际 {seqs}")
        check("stage 按生命周期排列",
              stages == ["created", "paid", "reviewed", "shipped", "settled"],
              f"实际 {stages}")
    return 2  # 断点：假装收到第 2 条后断线


async def resume(from_seq):
    print(f"\n② 断线重连：已收到 {from_seq} 条后断线，重连从 {from_seq + 1} 续传")
    async with websockets.connect(BASE) as ws:
        await ws.send(json.dumps({"action": "resume", "order_id": "ORD-1",
                                  "from_seq": from_seq}))
        events = await recv_until(ws, 5 - from_seq)
        seqs = [e["seq"] for e in events]
        check(f"续传恰好收到 seq {from_seq + 1}..5", seqs == list(range(from_seq + 1, 6)),
              f"实际 {seqs}")


async def heartbeat_kick():
    print("\n③ 心跳踢线：连接后保持静默，超时被服务端以 4000 踢下线")
    code = None
    async with websockets.connect(BASE) as ws:
        await ws.send(json.dumps({"action": "subscribe", "order_id": "ORD-1"}))
        try:
            while True:
                await asyncio.wait_for(ws.recv(), timeout=10)
        except websockets.ConnectionClosed as e:
            code = e.rcvd.code if e.rcvd else None
        except asyncio.TimeoutError:
            pass
    check("静默超时被踢（close code 4000）", code == 4000, f"实际 close code={code}")


async def main():
    await full_sequence()
    await resume(2)
    await heartbeat_kick()
    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 项断言失败：{'、'.join(FAILURES)}")
        sys.exit(1)
    print(">>> 验收：预设序列全收 ✅ 断点续传 ✅ 心跳踢线 4000 ✅")


if __name__ == "__main__":
    asyncio.run(main())
