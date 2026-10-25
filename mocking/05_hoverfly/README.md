# 05 · Hoverfly 代理录制：让真实依赖死后再复活

> 自研磁带（[architect/08](../../architect/08_mock_server/README.md)）回答了录制回放的
> 原理，本篇用业界服务虚拟化工具 Hoverfly（SpectoLabs 开源、Go 单二进制）把同一
> 支付场景做成产品级形态：客户端把 Hoverfly 当 HTTP 代理，capture 模式转发并记下
> 「请求-响应对」；杀掉真上游后 simulate 模式离线回放。实测：回放输出与录制期
> 逐字节一致、手工编辑 simulation 注入 500 按预期红、恢复原 simulation 后再回放
> 仍与录制一致——注入是可逆的单点操作。

## Background

自研磁带停在教学形态：精确 path 匹配、JSON 磁带、手工编辑注入故障。真实
团队的录制回放工具长什么样——捕获什么、按什么匹配、怎么编排——没见过
就只有想象。选型讨论（自研 vs 成熟工具）也缺一份实证依据。

把同一个支付场景（真上游用的就是 architect/08 那个假网关）用 Hoverfly
完整走一遍：录制、断网回放、故障注入三件事逐一对照。走完得到两个产物：
能跑的工具经验，和一张三方案对比表。

## What

Hoverfly 是一个服务虚拟化工具：以 HTTP 代理形态运行——本机代理端口收
请求，转发给真实上游或按 simulation 应答；模式由 admin API 切换，录制期
叫 `capture`（转发 + 捕获），回放期叫 `simulate`（查库即答）。

捕获产物叫 simulation（v5 格式 JSON）：一组「请求匹配器 + 响应」的对
（pair），可读、可 diff、可入库、可手工编辑。

可以把 Hoverfly 想成 08 那台磁带录音机的工业版。但和自研磁带不同的是：
它捕获的是「请求-响应对」而不是「path → 响应」——query 串、请求头、
body 天然都在匹配材料里，08 承认做不到的 path 归一化，这里是内建能力。

代价是匹配走「最强匹配策略」，行为需要理解而不是一眼看穿。

![Hoverfly 录制期捕获请求响应对，回放期杀上游离线应答并逐字节 diff](images/hoverfly.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/05_hoverfly/images/hoverfly.html)
> （或本地打开 [`images/hoverfly.html`](images/hoverfly.html)）。

图里两条泳道对应两阶段：录制期客户端经代理到真上游，交互落成 simulation；
回放期上游已死，simulation 喂给 simulate 模式应答，输出进逐字节 diff。

## When to Use

典型场景：

- 依赖响应复杂到手写不值：报文字段几十个、签名头一串——录一次全都有。
- 测试资产要沉淀：simulation 是 JSON，进 git 可评审、可复用、可当
  离线测试环境分发给同事。
- 异常注入要可逆：编辑一个字段就是一次故障演练，恢复只需换回原文件。

何时不用：

- 规则要前向声明（依赖还没存在）→ 声明式 mock（本系列 01）。
- 要验证双方预期一致 → 契约测试（[labs/15](../../labs/15_pact/README.md)）。
- 拦的是浏览器里的请求 → 那是 Playwright route 层的事
  （[playwright/05](../../playwright/05_pw_network_pro/README.md)，层次不同）。

三方案对比表（同一支付场景的三种替身形态，验收产物）：

| 维度 | 自研磁带（architect/08） | Hoverfly（本篇） | 声明式（系列 01） |
|:---|:---|:---|:---|
| 应答来源 | 录制（后向） | 录制（后向） | 规则前向声明 |
| 匹配语义 | `METHOD + path` 精确键 | 请求-响应对，最强匹配 | 特异度评分，平分先定义 |
| 未命中行为 | 自造 599 响亮报错 | 404 + unmatched 可查 | 404 带逐条失败诊断 |
| 故障注入 | 手工编辑磁带加 timeout | 编辑 simulation 状态/响应 | 编辑规则响应 |
| 资产格式 | 自定义 JSON 磁带 | simulation v5（业界通用） | 规则 JSON |
| 运行形态 | 纯标准库单文件 | Go 单二进制 + admin API | 纯标准库单文件 |

## Quick Start

前置条件：`brew install hoverfly`（1.12.16 ✅）。brew formula 只带 hoverfly
二进制、没有 hoverctl（官方配套的命令行控制工具，本实验用不到），编排走
admin API——Hoverfly 自带的独立管理端口（见输出里的 admin :9502）。

上游复用 architect/08 的假支付网关；仓库根 venv；另用 curl 与 lsof
（macOS 自带）。

```bash
cd mocking/05_hoverfly && ./hoverfly.sh all
```

实测输出（节选；txn 每次运行不同，同一次运行内录制/回放/恢复三处一致）：

```
=====> [apply] ① 清场 + 起真上游(:9500，复用 architect/08 假支付网关)与 Hoverfly 代理(:9501)
Hoverfly v1.12.16 就绪（代理 :9501，admin :9502）

=====> [observe] ② 代理录制：客户端把 Hoverfly 当 HTTP 代理，真上游响应被记进 simulation
Hoverfly → capture 模式
POST /pay → 200 txn=TXN-26d366a0 gw_status=ok
GET /pay/status → 200 state=settled
--- simulation 捕获 2 对交互 ---
    ……

=====> [observe] ③ 断网：杀掉真上游，Hoverfly 切 simulate——离线回放
Hoverfly → simulate 模式
POST /pay → 200 txn=TXN-26d366a0 gw_status=ok
GET /pay/status → 200 state=settled
回放与录制逐字节一致 ✅（上游已死，答案来自 simulation）
    ……

>>> 验收：代理录制 ✅ 断网回放逐字节一致 ✅ 注入 500 按预期红 ✅ 恢复可逆 ✅
```

诚实预期：③ 的 txn 与录制期完全相同——那是 simulation 里存的录制时
响应，不是新答案；④ 注入后客户端退出码 1 是设计好的红（业务走进失败
分支而非崩溃），⑤ 换回原 simulation 立即恢复——故障注入必须是可逆的。

## How It Works

**代理录制的本质是绝对 URI 请求行**。客户端连的是 Hoverfly 的代理端口，
但请求行写的是真实目标的完整 URL（`POST http://127.0.0.1:9500/pay`）——
HTTP 代理协议的核心就这一句话。

capture 模式下 Hoverfly 转发请求、把「请求-响应对」记进内存库，
`GET /api/v2/simulation` 随时导出。

**simulate 按「最强匹配」选对**。回放时请求进来，Hoverfly 在 pairs 里
找匹配最具体的记录应答——路径、query、头、body 都是匹配材料。

这就是「录一对、放一万次」的机制：录制期那笔 `txn=TXN-26d366a0`，
回放期原样返回，链路里第二步的 `?txn=` 查询因此能命中自己那条记录。

**注入是编辑数据，不是改代码**。把 simulation 里 POST /pay 那对的
`status` 改成 500、body 换成错误结构，`PUT /api/v2/simulation` 推回，
下次应答就是故障。

这与 architect/08 的「磁带编辑出超时」同一个思想，只是数据格式换成了
simulation v5。恢复 = 推回原文件，天然可逆。

**macOS 的 urllib 会绕过本机代理**。标准库 `ProxyHandler` 在 macOS 上
查系统代理排除表，对 `127.0.0.1` 一律直连——客户端请求根本没进 Hoverfly
（journal——Hoverfly 记录经代理请求的流水，admin API 可查——为空是判据）。

解法是用 `http.client` 直连代理端口、请求行写绝对 URL，即上面那句
「代理协议的核心」。

## Pitfalls & Q&A

踩坑清单：

- **macOS urllib 旁路本机代理**。现象：客户端全拿到 200，simulation 却是
  空的。原因：`ProxyHandler` 在 macOS 查系统排除表，127.0.0.1 被旁路。
  解法：`http.client` 直连代理 + 绝对 URI 请求行；journal 空不空是
  「请求是否真经代理」的判据。
- **API 里「录制」叫 capture 不叫 record**。现象：切模式返回
  `{"error":"Not a valid mode"}`。原因：hoverctl 的 record 到了 admin API
  里叫 capture（另有 modify/synthesize）。解法：以 admin API 文档为准。
- **brew formula 没有 hoverctl**。现象：`hoverctl` 命令不存在。原因：
  brew 只打包 hoverfly 二进制；解法：启停/模式/导入导出全部走 admin API
  （`/api/v2/hoverfly/mode`、`/api/v2/simulation`），本实验即此做法。
- **健康检查对上游用 `-f` 会永远超时**。现象：上游活着但 apply 报超时。
  原因：上游对 `GET /pay` 回 404，`curl -sf` 把 404 当失败。解法：探活
  分两档——admin 用 `-f`（要 2xx），上游用无 `-f`（有应答即活）。

深入问答：

- **Q：simulation 会撒什么谎？**
  与 08 的磁带同源：录制时的响应不保证永远合法——上游改字段、证书轮换、
  token 过期都会让仿真悄悄过期。Hoverfly 的解法也是同一思路：定期重录
  加真实联调抽查；进 git 的 simulation 靠评审与 diff 追踪变化。
- **Q：为什么「逐字节一致」是核心验收？**
  它一次性证明了三件事：捕获完整（两个交互都记下了）、匹配正确（回放
  命中的是同一条）、应答保真（响应体没有被加工）。任何一处出问题，
  diff 当场翻红。
- **Q：三方案到底怎么选？**
  一句话：规则现在就得有 → 声明式（01）；数据后向且想彻底懂原理 →
  自研磁带（08）；数据后向且要交给团队长期用 → Hoverfly。三者在
  When to Use 的对比表里逐维可查，选型是查表不是站队。
