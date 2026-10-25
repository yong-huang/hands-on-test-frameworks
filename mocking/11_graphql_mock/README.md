# 11 · GraphQL mock：schema 感知 + AB 场景切换

> REST 的 mock（替身：代替真实依赖应答的假服务）靠路径匹配，GraphQL
> （客户端把需要的字段写成 query 文本发给服务端的 API 协议）只有一个
> 端点——替身的重心从「路由」转向「schema（类型系统的真源）」。本篇用
> Ariadne（Python 的 GraphQL 服务库，用法是先写 schema、再补每个字段的
> 取值函数）实现：schema 外字段在执行前被校验拒绝并返回结构化 errors
> （不是 500 文本）；字段级错误带 path 定位；`X-Mock-Scene` 请求头
> 做同一 query 的 AB 两套数据切换。实测：3 条 query 各自命中预设、
> `Cannot query field 'nonexistentField'` 结构化报错、AB 两套数据分叉。

## Background

系列前十个实验的替身全是 REST 思维：一个路径一条规则。GraphQL 只有一个
`/graphql` 端点，查询长什么样由客户端的 query 文本决定——「路径匹配 +
预设响应」的组合拳在这里无处发力，硬匹配 query 文本则脆得没法用。

GraphQL 服务天生有两个可依赖的结构：schema（服务端声明的类型系统，
客户端只能在它的范围内提问）与 resolver（每个字段的取值函数）。让
mock 长在 schema 上，校验、错误、数据选择就有了类型系统的地基——
这也是 GraphQL 替身与 REST 替身的分水岭。

## What

GraphQL mock 是 schema 感知的替身：加载 SDL（schema 定义语言，GraphQL
的类型声明文件）构建类型系统，query 先被 schema 校验，再由 resolver
按预设数据应答。三个能力对应三块积木：

| 能力 | 机制 | 实测表现 |
|:---|:---|:---|
| schema 感知 | SDL 构建类型系统，执行前校验 | schema 外字段 → `Cannot query field …` |
| AB 场景切换 | `X-Mock-Scene` 头经 context（框架传给 resolver 的请求上下文）进 resolver | 同一 query，a/b 两套数据分叉 |
| 字段级错误 | resolver 抛错 → errors 带 path | `path: ["riskyOrder"]` 定位到字段 |

可以把 resolver 想成带**分场剧本的演员**：schema 是剧目的角色表（观众
问不到表外的角色），X-Mock-Scene 头是导演递的场记板——同一幕戏，a 场
按常规演，b 场按大额风控演。但和真演员不同的是：演员没有记忆，同一场景
内每次演出的结果完全相同（03 的状态机才管「演到哪了」）。

![schema 校验在前、场景化 resolver 选数据、AB 两套预设分叉](images/graphql.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/11_graphql_mock/images/graphql.html)
> （或本地打开 [`images/graphql.html`](images/graphql.html)）。

图里 schema 校验是第一道闸（schema 外字段进不了 resolver），场景头在
resolver 处分叉出 a/b 两套数据；无论哪条路，应答都是 JSON 的
data+errors 结构。

## When to Use

典型场景：

- 前端在真 GraphQL 服务就绪前开发：schema 先定，替身按 schema 出数，
  前端的 query 写法即最终写法。
- 页面多状态覆盖：AB 场景头切换「常规/大额风控」两套数据，一套 query
  验两种 UI 分支。
- 错误处理的契约化：schema 外字段、字段级异常都返回结构化 errors，
  前端的错误渲染逻辑有稳定形状可依。

何时不用：团队只有 REST → 01/02 的路径匹配更省；要状态流转（创建→
支付→发货）→ 03 的 scenario 思路移植到 resolver 内部做。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| REST 路径匹配（01/02） | 一路径一规则 | REST 依赖 |
| GraphQL schema mock（本篇） | schema 感知 + 场景头 | GraphQL 依赖、多 UI 状态 |
| 契约驱动（08） | 从 OpenAPI（REST 接口规格的行业标准格式）生成 | 契约先行的 REST 团队 |

## Quick Start

前置条件：仓库根 venv 已装 `pip install ariadne uvicorn`（本机 ariadne
配 graphql-core 3.3.0 ✅）；另用 curl 与 lsof（macOS 自带）。

```bash
cd mocking/11_graphql_mock && ./graphql_mock.sh all
```

实测输出（节选）：

```
=====> [apply] ① 依赖体检 + 清场 + 起 GraphQL mock(:9750，Ariadne ASGI)
GraphQL mock 就绪（endpoint /graphql，场景开关 X-Mock-Scene）

① 三条 query 各自命中预设响应（场景 a）
  ✅ 单订单 query → ORD-A-1 — amount=100.0
  ✅ 列表 query → 2 条（limit 生效） — ids=['ORD-A-1', 'ORD-A-2']

② 结构化 errors：schema 外字段与字段级错误都是 JSON errors 数组
  ✅ schema 外字段 → errors 带 Cannot query field（非 500 文本） — http 400；Cannot query field 'nonexistentField' on type 'Order'.
  ✅ 字段级错误带 path 定位 — http 400；path=['riskyOrder']

③ AB 切换：同一 query，X-Mock-Scene 头决定两套数据
  ✅ 场景 a → review=false（常规） — amount=100.0
  ✅ 场景 b → review=true（大额） — amount=9999.0
```

诚实预期：本实验的 Ariadne 实现在「有任何 errors」时 HTTP 回 400（包括
字段级执行错误）——GraphQL 的语义载体是应答体的 `data`+`errors`，状态码
是实现选择，断言对象应跟着语义走；③ 的两套数据是预设静态值，不带 04
那种随机生成。

## How It Works

**schema 感知是执行前的校验**。SDL 加载成类型系统后，query 文本先过
graphql-core 的校验——`nonexistentField` 不在 Order 类型里，进不了
resolver，直接得到带 `Cannot query field` 的 errors。

这是「schema 是类型系统的真源」的含义：替身能应答什么、拒绝什么，
由 schema 说了算。

**AB 切换是 context 传阅**。Ariadne 把 ASGI（Python 的异步 Web 应用接口，
前置条件里装的 uvicorn 就是运行这类应用的服务器）请求装进 context 传给
每个 resolver，resolver 从请求头读 `X-Mock-Scene` 选数据集：

```python
@query.field("order")
def resolve_order(_, info, id):
    return DATA[_scene(info)]["order"]   # 场景头决定走 a 还是 b
```

切换开关是请求的一部分——同一时刻不同消费者可以用不同场景头各测各的，
互不干扰。

对照 03 的 scenario：状态机是服务端全局单实例，场景头是请求级开关，
这是两者的本质分野。

**字段级错误自带 path**。riskyOrder 的 resolver 抛出的异常被 GraphQL
引擎捕获，渲染成 `errors[0].path == ["riskyOrder"]` 的结构化条目。

前端凭 path 知道「哪个字段的数据没拿到、其余字段照常」——这是 GraphQL
错误模型比「500 加一段文本」精细的地方。

## Pitfalls & Q&A

踩坑清单：

- **context 的形态随框架变**。现象：resolver 里取请求头报
  `'dict' object has no attribute 'headers'`。原因：Ariadne ASGI 默认
  context 是字典，Request 在 `["request"]` 键下。
  解法：兼容两种形态取头（见 `_scene`），别假设 context 就是请求。
- **HTTP 状态码不是 GraphQL 的语义载体**。现象：断言校验错误返回 200
  而实测 400。原因：状态码是实现选择——本实验的 Ariadne 对校验与执行
  错误都回 400。解法：断言 `data`/`errors` 应答体的内容与结构。

- **非 null 字段出错会连带 data 变 null**。现象：`riskyOrder: Order!`
  （类型后的 `!` 表示 non-null：该字段不允许为 null）出错时 `data`
  整个为 null。原因：GraphQL 的 non-null 传播规则——字段失败向上冒泡
  到最近的 nullable（允许为空的）祖先。
  解法：想保住部分数据，把易错字段声明为 nullable。

深入问答：

- **Q：为什么不用 WireMock（业界标准的 HTTP 替身服务器）的路径/文本匹配直接处理 GraphQL？**
  query 文本含任意空白与别名，文本匹配脆且不校验 schema——schema 外
  字段会得到「合法的假应答」而非结构化报错。schema 感知让替身与真服务
  共享同一套「什么能问」的边界，这是协议级 mock 与字符串级 mock 的分界。
- **Q：AB 场景和 03 的状态机怎么选？**
  看「分叉的依据」：按调用方意图切（本次要常规数据/要风控数据）→ 场景头，
  请求级、无状态、可并行；按历史顺序切（未支付不能发货）→ 状态机，
  服务端游标、序列敏感。GraphQL mock 想加状态，把 03 的游标塞进
  resolver 即可。
- **Q：真实 GraphQL 服务会照这个形状应答吗？**
  schema 层面会——schema 外字段、类型错误的结构化报错是协议行为，任何
  合规服务一致；数据层面是预设静态值，与真实服务的差异靠 10 的巡检
  对表（基准换成真 GraphQL 服务即可，diff 逻辑不变）。
