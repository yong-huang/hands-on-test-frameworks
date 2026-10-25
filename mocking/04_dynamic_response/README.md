# 04 · 动态响应与数据驱动：让替身的应答每次都「合理地不同」

> 静态 stub（存根：写死「请求长什么样 → 答什么」的固定应答规则）连打两次
> 答案一字不差，但真实服务每次都生成新订单号、回显请求参数。WireMock
> （业界标准的 HTTP 替身服务器）的响应模板（用 Handlebars 模板语言——一种
> 以 `{{帮手}}` 占位、应答前求值的模板语法——渲染应答体）让替身带上随机性
> 与请求上下文。实测：同一 stub 连打 100 次返回 100 个不重复订单号且全部
> 过 JSON Schema、customer/amount 逐笔回填正确、800ms 延迟 stub 实测
> P95（95 分位延迟）806ms。

## Background

静态替身暴露在两类断言下。一是唯一性：订单号、流水号这类字段重复即业务
事故，替身每次回同一个号，测试只能放宽到「有这个字段就行」——假绿。
二是回显：客户端传了 customer 和 amount，应答却不是这两个值，下游拿
替身响应做的断言全在测一个不存在的世界。

客户端侧的补救是每次自己造期望数据，再配一张「请求↔期望」对照表——
测试代码长出一套数据工厂，而替身本身还是死的。

模板化把变化性声明进替身：应答体写成填空模板，空位由随机源、请求字段、
时钟在应答前填上。测试因此可以断言「形状」（Schema）与「行为」（回填、
唯一性），而不是对着一个常量硬编码。

## What

响应模板是 stub 的一种应答方式：mapping（一条「请求长什么样 → 答什么」的
规则记录，存于 `mappings/*.json`）声明 `response-template`
transformer（转换器：应答前对模板求值的钩子）后，应答体里的 `{{帮手}}`
在每次应答前求值。本实验用到三个内建帮手：

| 帮手 | 作用 | 示例输出 |
|:---|:---|:---|
| `randomValue` | 随机字母数字串 / UUID | `ORD-k3f9x2m1qa` |
| `jsonPath request.body '$.customer'` | 从请求体取字段回填 | `alice` |
| `now format='yyyy-MM-dd HH:mm:ss'` | 当前时间戳 | `2026-10-23 23:41:07` |

可以把模板想成把 01 的应答手册升级成**填空模板**：句式固定，空位由骰子
（randomValue）、来信（请求字段）、日历（now）填上。但和真填空不同的是：
模板没有记忆——上一单填出的订单号这一单查不到，「记住历史」是 03 状态机
的职责，两件事互补不重叠。

延迟是另一类动态性：`fixedDelayMilliseconds: 800` 写在响应定义里（静态
字段，不走模板求值），每次应答前等 800ms——慢下游仿真用。

![动态响应：请求字段与随机源经模板引擎渲染进应答，逐条过 Schema](images/dynamic.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/04_dynamic_response/images/dynamic.html)
> （或本地打开 [`images/dynamic.html`](images/dynamic.html)）。

图里三条渲染输入在模板处汇合：请求体字段（回填）、随机源（唯一性）、
延迟分支（慢仿真）；渲染结果逐条过 Schema 校验。

## When to Use

典型场景：

- 下游字段有唯一性约束：订单号、流水号、幂等键（防同一笔操作被重复执行的
  请求标识）——重复即业务错误。
- 回显型接口：客户端带 reference 调用，后续请求要原样带回，替身必须
  回填正确才能支撑链路测试。
- 弱网与慢下游仿真：给 stub 注入延迟，验证超时与降级（本系列 07 的
  故障矩阵在延迟一档就用它）。

何时不用：应答依赖历史 → 03 的 scenario；需要「真实形状」的大响应 →
录制回放（本系列 05）比手写模板省力。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 静态 stub（01/02） | 应答是常量 | 断言只看状态码的粗粒度验证 |
| 响应模板（本篇） | 应答随请求与随机源变化 | 唯一性、回显、延迟仿真 |
| 录制回放（05） | 应答来自真实流量 | 形状复杂、手写不值的大 payload |

## Quick Start

前置条件：仓库根已建 venv（labs/00 体检通过）并装 `pip install jsonschema`
（本机 4.26.0 ✅）；Docker 在跑，镜像已拉 `wiremock/wiremock:3.13.0`；
另用 curl 与 lsof（macOS 自带）。

```bash
cd mocking/04_dynamic_response && ./dynamic_mock.sh all
```

实测输出（节选）：

```
--- 已加载的动态 stub ---
  slow-report        [模板] 延迟 800ms
  payment-dynamic    [模板]
  order-dynamic      [模板]

① 同一 stub 连打 100 次：动态生成 + 请求参数回填
  ✅ 100 次返回 100 个不重复订单号 — 去重后 100
  ✅ 全部响应过 JSON Schema 零错误 — schema: ORD-[a-z0-9]{10}
  ✅ customer/amount 逐笔回填正确 — 100 笔全对
  ✅ UUID 帮手生成 payment_id — PAY-b329f6c7-9592-43a5-927…

② 延迟注入实测：stub 固定延迟 800ms，连打 20 次量 P95
  ✅ P95 ≥ 800ms（实测 806ms，均值 804ms）
```

诚实预期：P95 取 20 个样本的第 19 小值，实测值在 800ms 上下小幅浮动
（调度抖动），判据是 ≥ 800ms 而非等于；100 次全过 Schema 指形状校验
零错误——单条具体值不校验，随机字段本来就不该有「期望值」。

## How It Works

**模板写进 mapping 的两种形态**。字符串值里嵌帮手，`jsonBody` 直接可用；
但占位整个 JSON 值（如数字字段）会让 mappings 文件加载即失败——jsonBody
必须先通过 JSON 解析，裸 `{{...}}` 不是合法 JSON。

数字占位要用 `body` 字符串形式，整个应答体作为模板渲染后再解析：

```json
{"name": "order-dynamic",
 "response": {"status": 201,
   "body": "{ \"order_id\": \"ORD-{{randomValue length=10 type='ALPHANUMERIC' uppercase=false}}\", \"amount\": {{jsonPath request.body '$.amount'}}, …… }",
   "transformers": ["response-template"]}}
```

`uppercase=false` 保证订单号全小写——正对应 Schema 里的 `[a-z0-9]`；
`……` 处省略了 state/customer/created_at 三个字段，写法同理。

**回填是逐笔可断言的**。`jsonPath` 帮手从请求体取字段渲染进应答——
Quick Start 里「100 笔回填全对」就是客户端每笔都断言
`响应.customer == 请求.customer`、`响应.amount == 请求.amount` 的结果，
不是抽样。

**延迟与 P95**。`fixedDelayMilliseconds: 800` 让 slow-report 每次应答前
睡 800ms；客户端用 `time.monotonic()` 量 20 次，P95 取第 19 小值。
延迟是容量与降级实验的旋钮——下一阶段故障矩阵会把它参数化成一档输入。

**随机性与可断言性靠 Schema 平衡**。randomValue 的值不可预测，但形状
可预测：`^ORD-[a-z0-9]{10}$` 锚定格式，`required` 锚定字段，唯一性断言
锚定行为。三层锚点立住，测试就不需要知道具体随机值。

## Pitfalls & Q&A

踩坑清单：

- **jsonBody 里裸模板占数字位，加载即失败**。现象：容器启动抛 JSON 解析
  异常，映射一条没加载。原因：jsonBody 先过 JSON 解析再谈模板，裸
  `{{...}}` 不是合法 JSON。解法：数字/布尔占位改用 `body` 字符串形式，
  整体渲染后再解析；字符串值内嵌帮手不受影响。
- **faker 扩展不在发行版里**。现象：`{{faker 'datatype.uuid'}}` 原样输出
  不求值。原因：WireMock 内建帮手只有 randomValue/jsonPath/now 等一组，
  faker 是社区扩展 jar，要另行安装。解法：本实验全用内建帮手达成同样
  目标（不重复 + UUID 形状）。
- **P95 对样本量敏感**。现象：20 样本的 P95 抖动几十毫秒。原因：P95 落在
  第 19 小值，单次调度毛刺直接抬线。解法：判据放宽为 ≥ 800ms；
  要更稳就加样本数（成本是时间线性增长）。

深入问答：

- **Q：随机值会不会让测试不确定？**
  断言分三层：Schema 锚形状、唯一性锚行为、回填锚上下文——都不锚具体
  随机值。不确定性被限制在「你本来就不该断言的维度」上，这是数据驱动
  替身与生俱来的边界。
- **Q：为什么偏偏是 100 次？**
  唯一性断言的置信度随次数增长：10 次暴露不出 10 字符随机串的碰撞，
  100 次已能暴露「模板没生效、每次同值」这类实现错误。次数是断言强度
  的参数，不是仪式。
- **Q：模板里能写业务逻辑吗？**
  能做的不该多做：每个帮手是一次变换，Handlebars 的条件与循环足以把
  mapping 写成没人敢动的程序。替身的职责是「形状合理、行为可控」，
  复杂逻辑的正确性该由真实服务的契约测试管（labs/15）——替身写成
  应用，是比静态 stub 更深的坑。
