#!/usr/bin/env python3
"""WS 流式替身：预设序列推送 + 断点续传 + 心跳踢线（FastAPI WebSocket）。

协议（客户端 → 服务端的 JSON 帧）：
  {"action": "subscribe", "order_id": "..."}    开始推送 seq 1..5
  {"action": "resume", "from_seq": k}           从 k+1 续传（断线重连用）
  {"action": "ping"}                            心跳；超过 HEARTBEAT_TIMEOUT_S
                                                无任何帧 → 服务端踢下线（4000）

SSE 变体：GET /sse/orders/{order_id} 以 text/event-stream 推同一序列
（只读单向，无续传/心跳语义——对比用）。
"""
import asyncio
import json
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

HEARTBEAT_TIMEOUT_S = 2.0
STAGES = ["created", "paid", "reviewed", "shipped", "settled"]

app = FastAPI()


def sequence(order_id, start=0):
    """预设序列：seq 从 start 之后继续（start=0 → 1..5）。"""
    return [{"seq": i, "order_id": order_id, "stage": STAGES[i - 1]}
            for i in range(start + 1, len(STAGES) + 1)]


async def _ws_loop(ws: WebSocket):
    await ws.accept()
    last_frame = time.monotonic()
    from_seq, order_id, pushing = 0, None, False

    async def kicker():  # 心跳看门狗：静默超时 → 4000 踢下线
        nonlocal last_frame
        while True:
            await asyncio.sleep(0.2)
            if time.monotonic() - last_frame > HEARTBEAT_TIMEOUT_S:
                await ws.close(code=4000, reason="heartbeat timeout")
                return

    async def pusher():  # 推送协程：订阅后按预设序列逐条推
        nonlocal pushing, from_seq, order_id
        while True:
            await asyncio.sleep(0.2)
            if pushing and order_id is not None:
                for ev in sequence(order_id, from_seq):
                    await ws.send_json({"push": ev})
                    from_seq = ev["seq"]
                pushing = False

    kick_task = asyncio.create_task(kicker())
    push_task = asyncio.create_task(pusher())
    try:
        while True:
            raw = await ws.receive_text()
            last_frame = time.monotonic()
            frame = json.loads(raw)
            action = frame.get("action")
            if action == "subscribe":
                order_id = frame.get("order_id", "ORD-1")
                from_seq = 0
                pushing = True
            elif action == "resume":
                order_id = frame.get("order_id", "ORD-1")
                from_seq = int(frame.get("from_seq", 0))
                pushing = True
    except WebSocketDisconnect:
        pass
    finally:
        kick_task.cancel()
        push_task.cancel()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await _ws_loop(ws)


@app.get("/sse/orders/{order_id}")
async def sse_orders(order_id: str):
    """SSE 变体：同一预设序列的单向只读流。"""
    async def gen():
        for ev in sequence(order_id):
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.05)
    return StreamingResponse(gen(), media_type="text/event-stream")
