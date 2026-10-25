# 09 · Pact 文件当 mock 数据源：一份契约，两个应答者

> labs/15 的 pact 文件记录着「前端期望 API 长什么样」——本篇把它倒过来用：
> 不拿契约去验证 provider，而是把它直接伺服成一个替身服务器（stub：代替真实依赖应答的假服务）。
> 实测：同一套
> 5 条消费方测试打 pact stub 全绿（契约外请求被 500
> `interaction_not_found` 拒绝）；跳过 stub 专属用例后打真 provider（labs/11 SUT——System Under Test，
> 被测系统）也全绿；逐交互对比，两个应答者的状态码与契约形状完全一致。

## Background

契约测试（labs/15）的验证方向是「consumer（消费方，接口的使用方）出题、provider（提供方，接口的实现方）答卷」——pact
文件在那种流程里是考卷。但这份文件里本来就写着每个请求的完整应答（状态码、
响应体结构、随机值生成器）：它同时是一份现成的替身数据源。

把考卷当替身有什么用？provider 没实现完的时候，消费方的测试本来要等；
有了 pact stub，消费方拿契约文件起一个替身就能进 CI（持续集成，提交后自动跑检查的服务）回归——这正是
labs/15 里 consumer 测试自带的 mock server（随测试用例起停的假服务）的
长期化形态。

本篇的自研 stub 只有一百多行，却刻意不用现成组件：pact-python 的 consumer
mock 是随测试用例起停的，没有「长期伺服一份 pact 文件」的形态——补上它
恰好证明一件事：**契约文件本身（不是任何工具）就是完整的应答数据源**。

## What

pact-as-stub 是把 pact 文件当应答数据源的替身形态：加载契约的
interactions（交互集合：请求匹配器 + 应答定义），按匹配规则应答，契约之外
的请求一律拒绝。labs/15 的契约里还有两样深水区资产，stub 必须读懂：

- `matchingRules`（匹配规则）：`match: type` 表示「类型一致即命中」——
  录制时 query `limit=10`，重放时来 `limit=5` 一样命中，因为都是数字串。
- `generators`（生成器）：响应体里的 null 占位在应答时才生成真值——
  `$.items[*].id` 是 RandomInt、`price` 是 RandomDecimal，每次应答
  都是新的随机值（mocking/04 动态响应实验的主题在契约世界里的对应物）。

可以把 pact 文件想成一份带自动阅卷说明的考卷：正常用法是拿它考
provider，本篇是让一位「标准答案员」（stub）照着考卷直接答题。但和照抄
答案不同的是：契约外的问题他一概拒答——替身的边界就是契约的边界。

![labs/15 契约文件两用：verify 视角考真 provider，stub 视角直接应答消费方](images/pact_stub.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/09_pact_stub/images/pact_stub.html)
> （或本地打开 [`images/pact_stub.html`](images/pact_stub.html)）。

图里一条契约喂出两个应答者：上面的真 provider 走 verify 视角（labs/15
的用法），下面的 stub 走数据源视角（本篇的用法）；同一套消费方测试双跑，
最后做形状一致性对比。

## When to Use

典型场景：

- provider 未就绪：契约已评审通过，消费方拿契约起 stub 先行开发与回归。
- 契约回归的轻量环境：不给 provider 建环境也能跑消费方测试——契约就是
  环境。
- 契约外请求的哨兵：stub 对契约外请求回 500，消费方误用未声明接口会
  立刻暴露。

何时不用：需要状态与顺序（创建→支付→发货）→ scenario（系列 03），
pact 交互是无记忆的请求-响应对；契约外的行为也要仿真 → 声明式 mock
（系列 01）补规则。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| labs/15 双向闭环 | 验证 provider 是否守约 | 契约测试的正向用途 |
| pact-as-stub（本篇） | 契约直接伺服消费方 | provider 未就绪/轻量契约回归 |
| 契约驱动（08 Prism） | 从 OpenAPI（接口规格）生成，非法 422 | 有 OpenAPI 契约的团队 |

## Quick Start

前置条件：仓库根 venv（labs/00 体检通过，含 httpx 与 pytest）；上游复用
labs/11 SUT 与 labs/15 的 pacts；另用 curl 与 lsof（macOS 自带）。

```bash
cd mocking/09_pact_stub && ./pact_stub.sh all
```

实测输出（节选）：

```
=====> [observe] ② 5 条消费方测试打 pact stub（含契约外 500）
5 passed in 0.41s
stub 全绿 ✅（契约外交互被 500 interaction_not_found 拒绝）

=====> [observe] ③ 同一套测试打真 provider（stub_only 用例跳过）
4 passed, 1 deselected in 0.26s
真 provider 全绿 ✅

=====> [observe] ④ 逐交互对比：双方应答都符合契约声明形状（多余键放行，叶子值不比）
① 逐交互对比：双方应答都符合契约声明形状（多余键放行）
  ✅ [a request for orders] status 200/200，契约形状：real ✅ / stub ✅
  ✅ [a request to create an order] status 201/201，契约形状：real ✅ / stub ✅
    ……

>>> 验收：stub 全绿 ✅ 契约外 500 ✅ 真 provider 全绿 ✅ 结构一致 ✅
```

诚实预期：④ 比的是「契约形状符合性」不是应答全等——真 provider 的应答
带着真实数据与多余键（`limit`/`offset`/`created_at`），stub 的应答带
生成器随机值；pact 的 like 语义本来就只锁声明部分，多余键放行。

这是「一致」的准确含义：同一份契约的两个忠实应答者，而不是两次相同的输出。

## How It Works

**stub 的三块积木**：匹配（method+path 精确，query 按 matchingRules 的
`match: type` 比类型，录制 limit=10、重放 limit=5 一样命中）、生成
（`apply_generators` 把 null 占位补成随机值）、拒绝（契约外请求 500）。

labs/15 的契约文件原样进、应答出——中间没有任何为它手写的规则，
`interaction_not_found` 的响应体里还带全部已声明交互清单。

**双跑是保真度的量尺**。同一套测试先打 stub 再打真 provider：契约内的
4 条两边全绿；对比器再逐交互核对「状态码相等 + 双方应答都符合契约声明
形状」。

若 stub 应答走形（比如生成器没生效，id 一直是 null），对比当场翻红——
本实验开发中真实踩过的一格。

**stub_only 标记划清分工**。契约外请求在 stub 世界是 500
（interaction_not_found），在真 provider 世界是它自己的 404——两边本就
不该一致。

这条用例标记 `stub_only`，真 provider 轮次用 `-m "not stub_only"` 跳过：
一致性对比只对契约内交互负责。

## Pitfalls & Q&A

踩坑清单：

- **生成器藏在 response 顶层**。现象：stub 应答里 id/price 永远是 null。
  原因：v4（pact 规范第 4 版）把 `generators` 挂在 response 顶层，分组为 `resp["generators"]["body"]`。
  解法：按 schema 层级取键；先 `python -m json.tool ../../labs/15_pact/pacts/*.json` 看结构。
- **「一致」断言写成应答全等**。现象：对比器把真实 SUT 的
  `limit`/`offset` 判成不一致。原因：pact like 语义允许未声明键——
  全等比形状符合更严，会把合法差异判红。解法：对比器按「声明键存在 +
  类型相符」实现，多余键放行。
- **契约外交互两边语义不同**。现象：同一条测试打 stub 500、打真
  provider 404，怀疑有 bug。这不是 bug：stub 的职责边界就是契约，
  契约外拒绝是它的诚实；用标记把这类用例与双跑轮次隔开。

深入问答：

- **Q：pact stub 与 08 的 Prism 有什么本质区别？**
  数据源不同：Prism 吃 OpenAPI（接口规格），pact stub 吃 pact（交互
  实例集合）。OpenAPI 说「POST /orders 合法请求长这样」；pact 说
  「那次真实交互中，这个请求得到了那个应答」。前者覆盖面广但抽象，
  后者精确到实例——团队两份契约都有时，08 与本篇各管一摊。
- **Q：生成器每次给随机值，测试怎么断言？**
  和 04 同解：断言形状与行为（id 是 int、每次不同），不断言具体值。
  labs/15 的 consumer 测试正是用 `each_like`/`integer` 这类类型匹配
  写的期望——契约世界天然是形状断言的世界。
- **Q：这份 stub 会「假绿」吗？**
  它替消费方挡住的是「provider 不在场」，挡不住「provider 实现与契约
  不符」——后者是 labs/15 verify 的职责。stub 轮全绿只说明消费方与
  契约自洽；契约与真 provider 的一致性，要靠 verify 轮（labs/15）定期
  跑。两轮合起来才是完整的契约回归。
