# 13 · WebSocket 流式 mock：订阅/续传/心跳的三场景替身

> REST 替身答完即走，WebSocket 替身要「一直在线」：按预设序列推送、断线后
> 从断点续传、静默超时踢下线。本篇用 FastAPI WebSocket 实现三场景全断言的
> 流式替身，附 SSE（单向流）变体。实测：订阅后收满 5 条且 seq 递增 1..5、
> 收 2 条断线重连后恰好续传 3..5、静默超时被 close code 4000 踢下线。

## Background

06 的 cassette 能回放「一问一答」，但推送型交互（订单事件流、行情、通知）
没有「问」——客户端订阅后服务端持续推。测这类依赖的难点在三个时间维度：
推送顺序要对、断线后要能续、客户端不发心跳要被踢。

手写 WS mock server 是事件驱动的状态机：连接、订阅、断线、超时四种事件
交织，手写极易漏分支。把三场景做成协议内的显式动作（subscribe/resume/
心跳静默），替身才可能被稳定断言。

## What

WS 流式替身是双向往来的推送型 mock：客户端发 JSON 帧声明动作，服务端按
预设序列推数据，超时看门狗踢静默连接。三场景协议化：

| 帧/行为 | 语义 | 实测表现 |
|:---|:---|:---|
| `{"action":"subscribe"}` | 从头推 seq 1..5 | 收满 5 条，顺序断言通过 |
| `{"action":"resume","from_seq":k}` | 从 k+1 续传 | 收 2 条断线后恰好续 3..5 |
| 静默超过 2 秒 | 心跳超时踢线 | close code 4000 |

可以把替身想成按台本推送字幕的提词器：订阅是开机、resume 是从任意页
接着放、心跳是观众每两秒点一次头——不点头就关机。但和提词器不同的是：
字幕表写死在替身里（预设序列），没有真实业务的变化性。

![WS 替身三场景：全量接收、断点续传、心跳踢线](images/ws.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/13_ws_mock/images/ws.html)
> （或本地打开 [`images/ws.html`](images/ws.html)）。

图里三条泳道就是三个场景；SSE 变体（单向只读）作为对照列在 Quick Start。

## When to Use

典型场景：

- 前端订阅订单事件流：推送顺序、断线重连、心跳保活都要可断言。
- 移动端弱网演练：断线重连续传是强需求，替身里天然可测。
- SSE 通知流：单向只读场景用 /sse 变体即可。

何时不用：只需要一问一答 → REST 替身（01/02）；要按消费进度动态生成
内容（不只是重放）→ 真服务或更完整的 mock 框架。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 11 GraphQL mock | 请求-应答，无长连接 | 一问一答的 GraphQL |
| WS 流式替身（本篇） | 双向长连接 + 推送序列 | 订阅推送、断线续传、心跳 |
| 真服务 | 形状真实但不可控 | 验收前最终联调 |

## Quick Start

前置条件：仓库根 venv 已装 `pip install fastapi websockets uvicorn`
（本机 websockets 17.1 ✅）；另用 curl 与 lsof（macOS 自带）。

```bash
cd mocking/13_ws_mock && ./ws_mock.sh all
```

实测输出（节选）：

```
① 全量接收：订阅后按预设序列收满 5 条（内容 + 顺序断言）
  ✅ 收满 5 条且 seq 递增 1..5 — 实际 [1, 2, 3, 4, 5]

② 断线重连：已收到 2 条后断线，重连从 3 续传
  ✅ 续传恰好收到 seq 3..5 — 实际 [3, 4, 5]

③ 心跳踢线：连接后保持静默，超时被服务端以 4000 踢下线
  ✅ 静默超时被踢（close code 4000） — 实际 close code=4000

=====> [observe] ③ SSE 变体：同一预设序列的单向只读流（curl 可直接消费）
data: {"seq": 1, "order_id": "ORD-1", "stage": "created"}
    ……
```

诚实预期：③ 的断线是客户端主动断开模拟的；续传的「记忆」在客户端
（from_seq 由客户端声明），服务端不校验它是否真收过——真服务的续传
语义要靠服务端游标，本替身是给前端练重连逻辑用的。

## How It Works

**双协程模型**。一个推送协程按预设序列逐条 send，一个看门狗协程每
200ms 检查静默时长——两个 asyncio task 共享连接但职责分离，踢线时
各自 cancel：

```python
async def kicker():
    while True:
        await asyncio.sleep(0.2)
        if time.monotonic() - last_frame > HEARTBEAT_TIMEOUT_S:
            await ws.close(code=4000, reason="heartbeat timeout")
```

**续传是纯函数**。`sequence(order_id, start)` 返回 start 之后的序列——
同一张序列表，订阅取 start=0、续传取 start=客户端声明的值。状态只有
from_seq 一个数，这正是断点续传该有的形状。

**close code 是结构化信号**。4000（应用自定义段）标记「心跳超时」，
客户端凭 code 区分踢线与网络断开——比裸断开多了可断言的语义。

## Pitfalls & Q&A

踩坑清单：

- **curl 消费 SSE 会触发 SIGPIPE**。现象：`curl | head` 让脚本以
  exit 23 死掉。原因：head 截断后 curl 收到管道破裂信号，`set -o
  pipefail` 把它当失败。解法：SSE 演示段 `set +e` 并给 curl 加
  `--max-time 2`。
- **心跳看门狗与推送协程共享连接**。现象：踢线后推送协程仍在 send，
  抛「sent to closed」异常刷屏。解法：踢线时 cancel 两个协程任务，
  异常被 WebSocketDisconnect 分支吸收。
- **from_seq 由客户端声明**。现象：恶意客户端声明 from_seq=0 可重复
  收全部。解法：替身语义如此（给前端练重连）；真服务要用服务端游标。

深入问答：

- **Q：SSE 和 WebSocket 怎么选？**
  单向只读、走标准 HTTP、curl 就能测 → SSE；双向交互、要心跳/自定义
  关闭语义 → WebSocket。本篇两个端点都给了，同一张序列表驱动。
- **Q：close code 4000 是什么？**
  WebSocket 协议把 4000-4999 留给应用自定义。本替身用 4000 表「心跳
  超时」，客户端凭 code 区分踢线与网络故障——比裸断开可断言。
- **Q：和 03 的状态机什么关系？**
  03 管「请求序列改变服务端状态」，本篇管「服务端状态按时间推进并
  主动推送」。一个由客户端驱动、一个由服务端驱动，合并起来就是完整
  的事件驱动替身。
