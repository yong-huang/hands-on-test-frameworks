# 12 · gRPC mock：proto 驱动替身，双探针验收

> gRPC（跨语言的 RPC 框架：服务与方法定义在 proto 里，调用走二进制协议）
> 的替身（代替真实依赖应答的假服务）不需要手写应答规则——proto（接口的
> 强类型契约：服务、方法、消息结构一次声明）经 protoc 编译出桩代码，
> 替身实现方法体即可。本篇实现
> unary 查询与 server-streaming 事件流两个方法：grpcurl 探 unary 的 proto
> 合法 JSON 应答与字段校验（缺 order_id → INVALID_ARGUMENT 点名字段），
> Python 探针断言流式 5 条事件全收且 seq 严格递增 1..5。

## Background

REST 替身的规则是「路径 + 应答」，gRPC 的规则全部长在 proto（接口的
强类型契约：服务、方法、消息结构一次声明）里——方法签名、字段类型、
流式还是一问一答，编译器说了算。替身要做的只剩实现方法体，类型错误
在编译期就被拦下。

但 gRPC 是二进制协议，curl 看不懂帧里的内容，测试需要两件配套：
反射（server reflection，服务端自我描述的机制，grpcurl 靠它发现
「有什么服务和方法」）与双探针。

grpcurl 管一问一答的快速验证，程序化客户端管流式消息的顺序断言。

## What

gRPC 替身是 proto 驱动的应答服务：`grpc_tools.protoc` 把 order.proto
编译成桩模块（pb2 消息类 + pb2_grpc 服务骨架），替身继承骨架实现两个方法。

GetOrder 是 unary（查单个订单），StreamOrderEvents 是
server-streaming（按序推送 5 条生命周期事件）。

可以把替身想成按图纸施工的自助终端：proto 是图纸（接口与消息的形状
全在上面），protoc 把图纸变成零件，替身只负责「被问到时吐什么数据」。
但和自由发挥的终端不同的是：缺必填字段它当场拒收并点名字段——proto3
虽然废除了 required，必填语义由服务端显式校验补上。

![proto 编译出桩，替身实现方法体，grpcurl 与 Python 双探针验收](images/grpc.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/12_grpc_mock/images/grpc.html)
> （或本地打开 [`images/grpc.html`](images/grpc.html)）。

图里 proto 在左上、唯一的真源；双探针在下方——grpcurl 靠反射发现服务
（unary/字段校验），Python 探针专攻流式顺序断言。

## When to Use

典型场景：

- 前端/移动端等 gRPC 消费方在 provider（最终提供接口实现的一方）实现前
  开工：proto 已评审，替身按 proto 出数，消费方的 stub（由 proto 生成的
  客户端调用代码，与 01 里指「存根规则」的 stub 不是一回事）调用即
  最终调用。
- 流式语义的演练场：server-streaming 的推送顺序、条数、断连行为，
  都替身里可控可断言。
- 跨语言联调的公共锚点：proto 是语言中立契约，替身服务任何语言的
  消费方都能连。

何时不用：消费方只认 REST/JSON → gRPC 替身帮不上（grpc-JSON 转码——把 gRPC 调用翻译成 JSON 接口的网关层——是
另一层的事）；要真连接真延迟 → 故障矩阵（系列 07）的注入更适合。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| REST 路径匹配（01/02） | JSON 文本匹配 | REST 依赖 |
| GraphQL schema mock（11） | schema 感知、单端点 | GraphQL 依赖 |
| gRPC proto 替身（本篇） | proto 编译期类型 + 流式 | gRPC 依赖、流式演练 |

## Quick Start

前置条件：仓库根 venv 已装 `pip install grpcio grpcio-tools
grpcio-reflection`（本机 grpcio 1.84.1 ✅，arm64 有预编译包）；grpcurl
（brew install grpcurl，本机 1.9.4 ✅）；另用 lsof（macOS 自带）。

```bash
cd mocking/12_grpc_mock && ./grpc_mock.sh all
```

实测输出（节选）：

```
=====> [apply] ① 依赖体检 + protoc 生成桩 + 起 gRPC 替身(:9850)
--- 已生成：proto/order_pb2.py proto/order_pb2_grpc.py  ---
--- 服务清单（反射）---
order.v1.OrderQuery.GetOrder
order.v1.OrderQuery.StreamOrderEvents

=====> [observe] ② grpcurl 探 unary：proto 合法 JSON 应答
{
  "order_id": "ORD-1",
  "customer": "alice",
  "amount": 123.5,
  "status": "created"
}
    ……

=====> [observe] ④ Python 探流式：5 条事件全收 + 顺序断言
    ……
  ✅ 收到 5 条事件 — 实际 5 条
  ✅ seq 严格递增 1..5（顺序断言） — 实际 [1, 2, 3, 4, 5]
    ……

>>> 验收：grpcurl unary 合法应答 ✅ 字段校验点名字段 ✅ 流式 5 条有序全收 ✅
```

诚实预期：③ 字段校验会让 grpcurl 以非零退出码结束（服务端返回
INVALID_ARGUMENT）——脚本把退出码与消息内容一起断言，红是验收的一部分；
proto3 没有 required 关键字，「必填」是服务端校验出来的语义，不是
schema 声明出来的。

## How It Works

**proto → 桩 → 替身，三级流水**。protoc 把 order.proto 编译成两个模块：
pb2（消息类，字段赋值即序列化）与 pb2_grpc（服务骨架与方法路由）。替身
继承骨架、实现两个方法，剩下的线程池与网络由 grpc.server 托管：

```python
def GetOrder(self, request, context):
    if not request.order_id:                      # proto3 无 required，
        context.abort(grpc.StatusCode.INVALID_ARGUMENT,   # 必填靠显式校验
                      "order_id is required（缺必填字段：order_id）")
    return order_pb2.OrderResponse(order_id=request.order_id, …)
```

**反射让 grpcurl 「认识」替身**。gRPC 是二进制协议，grpcurl 默认不知道
服务里有什么——开启 server reflection（服务端自我描述机制）后，grpcurl
从服务端拉取方法清单与消息定义，任意语言写的测试代码都能即连即调。

**流式顺序是断言的主语**。StreamOrderEvents 用生成器 yield 五条事件，
Python 探针把迭代收到的 seq 收集成列表断言 `[1, 2, 3, 4, 5]`——流式的
核心契约是「条数与顺序」，比单条内容更值得钉死。

## Pitfalls & Q&A

踩坑清单：

- **grpcurl 探活不带 -max-time，失败一次白等 10 秒**。现象：服务未就绪
  时，健康检查每轮探活都等满 10 秒才报 context deadline exceeded
  （grpcurl 默认连接超时 10 秒，连 connection refused 也要等满才报）。
  解法：探活加 `-max-time 2`，把单次失败等待压回 2 秒。
- **反射不开，grpcurl 就是瞎的**。现象：`grpcurl list` 报 server does
  not support reflection。原因：Python gRPC 服务默认不带反射。解法：
  `grpcio-reflection` 的 `enable_server_reflection` 显式开启。
- **DESCRIPTOR 在 pb2 不在 pb2_grpc**。现象：开反射时报
  `module 'order_pb2_grpc' has no attribute 'DESCRIPTOR'`。原因：文件
  描述符生在消息模块（pb2），服务骨架模块（pb2_grpc）只有方法路由。
  解法：从 `order_pb2.DESCRIPTOR` 取服务全名。
- **InvalidArgument ≠ INVALID_ARGUMENT**。现象：grep 校验输出漏报。
  原因：grpcurl 打印的是 CamelCase 的 `InvalidArgument`。解法：按
  grpcurl 的实际输出大小写匹配（或 -i 忽略大小写）。

深入问答：

- **Q：proto3 废除了 required，「必填」还算契约吗？**
  算，但要靠服务端校验来兑现：空 order_id 返回 INVALID_ARGUMENT 并在
  消息里点名字段，消费方拿到的错误是可编程的（gRPC status code）——
  这比 proto2 的 required 更啰嗦，但也更可控（可以加条件）。
- **Q：流式的价值只是「多条数据」吗？**
  顺序与终态是流式独有的契约：5 条事件按生命周期排列、发完即完
  （服务端不关流就永远不结束）。这些在 unary 里根本不存在，替身是
  唯一能稳定演练它们的场所。
- **Q：和 03 的状态机什么关系？**
  互补：本篇的事件流是「固定剧本的播放器」（顺序写死在 STAGES 表），
  03 的 scenario 是「按请求翻页的状态机」。把 STAGES 表换成按状态
  游标取值，流式替身就有了状态机语义——两篇的积木可以直接拼。
