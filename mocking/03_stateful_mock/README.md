# 03 · 状态化 mock：scenario 状态机，让替身记住「到哪一步了」

> 01/02 的替身每次应答都一样，但真实依赖有记忆——支付接口在订单创建前后必须
> 答得不一样。WireMock（业界标准的 HTTP 替身服务器，替身即代替真实依赖应答的
> 假服务）的 scenario 是它的场景状态机：多条共享一枚进度游标的 mapping 规则
> 组成的状态机，把「应答依赖历史」声明成状态×动作转换表。本实验实现订单
> 「创建→支付→发货」四态状态机，实测：三步流转每步应答不同、终态一切写操作
> 被拒、4 态 × 3 动作转换表的 9 个非法跳转格子全部 409 且状态不变、重置后
> 状态机可复用。

## Background

无状态替身有一个盲区：它答不出「现在是什么阶段」。支付接口在没有任何订单时
也返回 settled（01/02 的 stub——存根，一条写死「请求长什么样 → 答什么」的
固定规则——就会这样），前端拿着这个响应走完流程，测试全绿——这个绿是假的，
因为真实系统会在这里拒绝。

给替身加记忆的手写做法是在测试代码里维护顺序：先调创建、再调支付，替身里
用计数器或布尔值判断该答什么。顺序一变、用例一多，这些隐藏状态就成了
最难查的测试耦合。

把记忆从测试代码挪进替身，声明成一张状态×动作转换表——每个格子写明
「处于状态 S 时收到动作 A，答什么、状态变不变」。表是数据，引擎仍是
WireMock 那一套，这就是 scenario（场景状态机）。

## What

scenario 是 WireMock 的状态机机制：多条 mapping（一条「请求长什么样 → 答什么」
的规则记录，存于 `mappings/*.json`）声明同一个 `scenarioName`，共享一枚状态游标。

每条 mapping 用 `requiredScenarioState` 声明前置状态、`newScenarioState`
声明后继状态。

本实验的状态机有四个状态、三个动作，转换表共 12 格——3 格合法流转，
9 格非法跳转：

| 动作 \ 当前态 | Started（空） | CREATED | PAID | SHIPPED |
|:---|:---|:---|:---|:---|
| POST /orders | ✅ 201 →CREATED | 409 重复下单 | 409 已支付 | 409 已完结 |
| POST /orders/pay | 409 未创建 | ✅ 200 →PAID | 409 重复支付 | 409 已发货 |
| POST /orders/ship | 409 未创建 | 409 未支付 | ✅ 200 →SHIPPED | 409 重复发货 |

可以把 scenario 想成给 01 那本应答手册加了**进度书签**：翻到哪一页，
就答哪一页的话。但和真书签不同的是：一个场景只有一枚书签（全局单实例），
两个订单并发走同一条 URL 会互相踩状态——这是它最大的能力边界。

![订单状态机：四态主链，每态标注非法跳转的 409 拒绝](images/order_lifecycle.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/03_stateful_mock/images/order_lifecycle.html)
> （或本地打开 [`images/order_lifecycle.html`](images/order_lifecycle.html)）。

图里是主链四态与每个状态上标注的拒绝语义；完整 12 格对照以本节转换表为准。

## When to Use

典型场景：

- 多步业务流程的 E2E（end-to-end，端到端测试）：订单、审批、工单——每一步的合法请求取决于上一步。
- 时序敏感的验证：重试、幂等、防重——幂等指同一操作执行多次效果与一次相同；防重则要求同一请求打两次第二次必须被拒。
- 前端状态推进：骨架屏、进度条、禁用态，依赖后端「走到哪一步了」。

何时不用：应答与历史无关（查询类接口）→ 01/02 的无状态 stub 更简单；
同一接口要同时服务多个并发实体（多订单并行）→ scenario 单实例撑不住，
需要按实体命名场景或自研状态机。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 无状态 stub（01/02） | 问什么都答同一句 | 应答与历史无关的依赖 |
| scenario 状态机（本篇） | 应答随状态游标变化 | 单实例多步流程、时序敏感验证 |
| 测试代码维护顺序 | 隐藏状态散在用例里 | 只有一两个顺序依赖的临时场景 |

## Quick Start

前置条件：仓库根已建 venv（labs/00 体检通过，脚本经 `../../.venv/bin/python`
调用）；Docker 在跑，镜像已拉：`docker pull wiremock/wiremock:3.13.0`；
脚本另用 curl 与 lsof（macOS 自带，Linux 需自行安装）。

```bash
cd mocking/03_stateful_mock && ./stateful_mock.sh all
```

实测输出（节选）：

```
=====> [apply] ① 清场（容器含上次的场景状态）+ 起 WireMock(:9300, order-lifecycle 状态机)
--- 场景初始状态 ---
  order-lifecycle: Started（映射 16 条）
    ……

① happy path：创建→支付→发货，同一 URL 每步应答随状态变化
  ✅ POST /orders → 201，场景状态 = created — order_id=ORD-SM-001
  ✅ POST /orders/pay → 200，场景状态 = paid — payment_id=PAY-SM-001
  ✅ POST /orders/ship → 200，场景状态 = shipped — tracking_no=TRK-SM-001

③ 非法跳转全表：4 态 × 3 动作里除 3 个合法转移外的 9 格
  ✅ POST /orders/ship @ created → 409 NOT_PAID — 前缀: POST /orders；拒绝后状态仍为 created
    ……

>>> 验收：状态流转 ✅ 终态拒绝 ✅ 9 格非法跳转全拒 ✅ 重置可复用 ✅
```

诚实预期：①②③④ 全部 ✅ 是验收线；③ 的 9 个格子除断言 409 与业务码外，
还断言「拒绝后状态不变」——替身被拒绝请求带跑偏，比直接崩溃更难查。
场景状态可随时 `GET /orders/state` 查看，那是转换表里 4 条查询映射在应答。

## How It Works

**状态游标如何翻页**。初始态叫 `Started`（隐式，不用声明）；合法转移的
mapping 带两个状态字段，例如支付那格：

```json
{"scenarioName": "order-lifecycle",
 "requiredScenarioState": "CREATED", "newScenarioState": "PAID",
 "request": {"method": "POST", "urlPath": "/orders/pay"},
 "response": {"status": 200, "jsonBody": {"payment_id": "PAY-SM-001", …}}}
```

同一 URL 的多条 mapping 里，WireMock 按「当前游标 + 前置状态匹配」选出
应答者——Quick Start 输出里的 `场景状态 = paid` 就是 `GET /orders/state`
命中了 `state-query-paid` 这条映射，状态本身也是转换表的一行。

**转换表必须写全，缺格子的报错形态是 404 不是 409**。12 个动作格在
`mappings/order_lifecycle.json` 里一条不落（外加 4 条状态查询，共 16 条）。

漏写的格子会落进 WireMock 默认行为：404 空 body——测试红了，但红得
让人先去查网络而不是查转换表。缺什么就声明什么，这是状态化替身的诚实。

**重置与容器生命周期**。`POST /__admin/scenarios/reset` 把游标拨回
`Started`；`apply` 重建容器则整体清零——场景状态活在 WireMock 进程内，
这既是约束（不能持久化）也是便利（干净状态一轮一取）。

## Pitfalls & Q&A

踩坑清单：

- **per-scenario 重置端点不存在**。现象：`POST /__admin/scenarios/{name}/reset`
  返回 404，场景卡在终态，后续格子全部错位。原因：3.13 只提供全量重置
  `POST /__admin/scenarios/reset`（单场景下语义等价）。解法：用全量端点，
  并在客户端里封装成 `reset()` 统一调用。
- **漏写转换表格子 = 404 假故障**。现象：某格期望 409 却收到 404。
  原因：没有声明该「状态×动作」组合的 mapping，落进默认 404。解法：
  转换表按矩阵写全（4×3 一格不缺），再用客户端逐格核对。
- **非法跳转忘了断言「状态不变」**。现象：拒绝生效但场景状态被翻页，
  后续用例连环错。原因：写了 `requiredScenarioState` 却手滑加了
  `newScenarioState`。解法：拒绝格只有前置态字段；客户端断言拒绝前后
  游标一致。

深入问答：

- **Q：拒绝为什么用 409 而不是 400/422？**
  409 Conflict 的语义就是「请求本身合法，但与资源当前状态冲突」——
  重复支付、未支付发货正是这个定义。参数错误才用 400，语义校验用 422。
- **Q：两个订单并发怎么扩展？**
  scenario 的书签是场景级单实例。多实体要么按实体 ID 建多个场景
  （`scenarioName: "order-<id>"`，动态生成 mappings），要么换自研状态机
  替身（把 01 的匹配引擎加上按实体键分桶的游标）。前者是配置技巧，
  后者是造轮子，按团队工具链选。
- **Q：状态化替身会不会更容易「假绿」？**
  会——转换表本身就是一仢单方面声明的契约：真实服务的状态流转若变了，
  替身还按旧表应答。防线与 01 相同：留痕（`__admin/requests` 的请求日志）
  加对账，系统化版本是本系列 10 的漂移门禁（自动比对替身应答与真实接口
  差异的 CI 关卡）。
