# 14 · 消息事件虚拟化：毒丸进 DLQ，绝不阻塞

> 事件驱动依赖的替身难点不在「发消息」而在「发坏消息」：毒丸事件
> （payload 非法）会卡死天真的消费者。本篇用 testcontainers 拉起真
> Kafka，替身生产者按脚本注入 正常/乱序/毒丸 三类事件，消费 worker
> 验证：正常与乱序全处理、毒丸进 DLQ、毒丸之后的正常事件不被阻塞。

## Background

labs/14 的 testcontainers 已证「真依赖容器化」这条路——但只测了快乐
路径（Postgres 里正常读写）。事件驱动依赖的测试难点是坏消息：上游
一旦发出畸形 payload，天真的消费者会在错误处崩溃或死循环重试，队列
堆积，整条管线瘫痪。

与其等上游事故，不如自己当一回「恶意的上游」：替身生产者按脚本注入
毒丸，消费者验证「该处理的全处理、该进 DLQ 的进 DLQ、绝不阻塞」。
testcontainers 保证这是真 Kafka 语义（分区、offset、消费者组）而非
内存队列的模拟。

## What

事件虚拟化替身由两部分组成：testcontainers 拉起的 Kafka（KRaft 单节点，
arm64 原生镜像）与按脚本注入的替身生产者。本篇注入 6 条事件，消费
worker 以「处理/进 DLQ」两种行为应对：

| 事件 | 内容 | 消费者行为 |
|:---|:---|:---|
| 正常 ×3 | seq 1/2/3 合法 JSON | 处理并记录 |
| 乱序 ×1 | seq 3 重复到达 | 照常处理（幂等性在业务侧） |
| 毒丸 ×1 | `NOT-JSON-{{{`（非法原文） | 解析失败 → 写 DLQ → 继续下一条 |
| 毒丸后正常 ×1 | seq 4 | 处理（不被毒丸阻塞的证据） |

可以把替身生产者想成**压力测试里的恶意用户**：正常用户按文档发请求，
它专发残缺报文——但和真实攻击不同的是：注入是脚本化的、可重复的、
毒丸数量与位置都是断言的一部分。

## When to Use

典型场景：

- 消费服务的死信路径从未被测过：注入毒丸验证 DLQ 落盘与不阻塞。
- 乱序/重复事件语义（幂等、去重、补偿）要回归：脚本化注入精确序列。
- 消费方在 provider 上线前开发：先拿替身生产者把消费链路跑通。

何时不用：只想在无 broker 下测消费逻辑本身 → 把 handler 函数单测即可
（labs/04）；要测 Kafka 集群本身的容量 → 那是压测不是虚拟化。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 内存队列模拟 | 无 broker，纯函数 | 单测 handler 逻辑 |
| testcontainers 真 Kafka（本篇） | 真语义：分区/offset/组 | 消费链路集成与坏消息演练 |
| 共享测试集群 | 环境常驻 | 团队级联调（有互扰成本） |

## Quick Start

前置条件：Docker daemon 在跑（testcontainers 需要 DOCKER_HOST 可达，
脚本自动探测 OrbStack）；仓库根 venv 已装 `pip install
testcontainers[kafka] kafka-python-ng`；首次拉取镜像约数百 MB。

```bash
cd mocking/14_event_mock && ./event_mock.sh all
```

实测输出（节选）：

```
① testcontainers 拉起 Kafka（KRaft 单节点，arm64 原生镜像）
② 替身生产者注入脚本化事件序列
已注入 6 条事件（含 1 乱序 + 1 毒丸 + 1 毒丸后正常）
③ 消费 worker 处理（毒丸 → DLQ，其余记录）

④ 断言
  ✅ 正常与乱序事件全部被处理：5 条（seq 顺序 [1, 2, 3, 4]，乱序 dup 也在场）
  ✅ 毒丸进 DLQ：1 条（内容片段：NOT-JSON-{{{…）
  ✅ 毒丸之后的正常事件不被阻塞（seq 4 已处理）

>>> 验收：脚本化注入 ✅ 正常/乱序全处理 ✅ 毒丸进 DLQ ✅ 不阻塞后续 ✅
```

诚实预期：乱序事件的「乱序」指投递顺序（seq 3 的重复事件后到），不是
分区乱序——单分区 + 单 worker 下顺序本身是确定的；DLQ 在本篇是记录
清单，真 DLQ 主题的转发策略是消费代码的职责（worker 里留了接口）。

## How It Works

**替身生产者的关键是「不发序列化好的 JSON」**。毒丸必须以非法原文进
队列——如果用 `value_serializer=json.dumps`，毒丸字符串会被救成合法
JSON 转义串，毒丸就不是毒丸了：

```python
producer = KafkaProducer(bootstrap_servers=bootstrap)  # 无 serializer
for ev in events:
    payload = ev.encode() if isinstance(ev, str) else json.dumps(ev).encode()
    producer.send(TOPIC, value=payload)
```

**消费 worker 的行为就是被测契约**。合法 JSON → 记录进 processed；
`json.JSONDecodeError` → 写 DLQ 清单并继续下一条。断言三件套（全处理/
进 DLQ/不阻塞）全部对着这两份清单核对——「不阻塞」的判据是毒丸之后的
seq 4 出现在 processed 里。

**testcontainers 的生命周期即环境语义**。容器在 `with` 块内拉起、退出
即销毁——每次运行都是全新 broker，没有历史 offset 干扰；这也是它比
共享集群适合坏消息演练的原因：毒丸可以随便灌。

## Pitfalls & Q&A

踩坑清单：

- **value_serializer 会把毒丸救活**。现象：毒丸进队列后变成合法 JSON
  字符串，DLQ 断言失败。原因：serializer 对一切值做 dumps，毒丸原文被
  转义。解法：替身生产者不用 serializer，逐条手工编码。
- **testcontainers 找不到 Docker socket**。现象：
  `FileNotFoundError: /var/run/docker.sock`。原因：OrbStack 的 socket
  在 `~/.orbstack/run/docker.sock`。解法：export DOCKER_HOST 指向实际
  socket（脚本已自动探测）。
- **容器镜像未预拉**。现象：首次运行报 ImageNotFound。解法：先
  `docker pull confluentinc/cp-kafka:7.6.0`（脚本依赖该 tag，与
  testcontainers 默认值一致）。

深入问答：

- **Q：毒丸是怎么产生的，能从源头杜绝吗？**
  上游序列化 bug、schema 演进不兼容、人工运维写坏——源头无法完全
  杜绝。消费端「毒丸 → DLQ → 继续」是标准防御，而本篇的注入脚本
  保证这条防御每次提交都被演练。
- **Q：为什么断言「不阻塞」比「进 DLQ」更重要？**
  进 DLQ 只是单条消息的归宿；不阻塞才证明消费者的健壮性——真实事故
  中，一条毒丸卡死整条管线（head-of-line blocking）的破坏力远大于
  单条丢失。两者都断言才完整。
- **Q：和系列 07 的故障矩阵什么关系？**
  同构思路不同载体：07 用 HTTP 替身注入网络层故障，本篇用真 broker
  注入数据层毒丸。矩阵思想一致——穷举坏输入、逐格断言行为。
