# 08 · OpenAPI 驱动 mock（Prism）：契约是唯一的真源

> 手写 stub（存根：一条「请求长什么样 → 应答什么」的规则）的应答靠自己声明，
> 契约驱动 mock 的应答从 OpenAPI 契约里长出来。
> Prism（Stoplight 出品的契约驱动 mock/校验工具）吃下一份 OpenAPI YAML 就能
> 起 mock：请求先按契约校验、应答按契约生成——mock 代码 0 行。实测：合法
> 请求 201 全绿且响应过独立 Schema 校验零错误、缺字段/错类型被 422 拒绝、
> `Prefer` 头切换同一路径的两套示例；契约 v2 新增必填字段后重启，旧请求
> 422 红、新请求 201 绿——mock 行为随契约而动，全程只改了 YAML。

## Background

01/02 的替身规则（替身：代替真实依赖应答的假服务）、05 的 simulation
（Hoverfly 录制的「请求-响应对」文件）、06 的 cassette（pytest 录制回放的
磁带文件），共同点是对「接口长什么样」各自有一份私有描述。

真实接口变了，这些替身不会自己知道——漂移只能靠巡检（系列 10 的主题）
追认。而这几份私有描述，抄写的都是契约本该统一提供的信息
（路径、参数、请求/响应的结构与示例）。

如果 mock 直接吃契约，描述就只有一份，接口怎么变 mock 就怎么变——
漂移在源头就被消掉了。

Prism 是这条路线的成熟工具：`prism mock contract.yaml` 一条命令，契约即替身。
本实验验证它的三件事：应答是否守契约、非法请求是否被拦、契约变了它跟不跟。

## What

契约驱动 mock 是一种从接口规格生成应答的替身：OpenAPI 契约（YAML 格式的
接口规格书，声明路径、请求结构、响应结构与示例）是唯一真源，Prism 启动时
加载契约，之后每个请求先按契约校验，应答按契约的 schema 与 examples 生成。

可以把 Prism 想成照图施工的施工队：OpenAPI 是图纸，请求先对图验收
（不合图纸的直接退回 422），成品按图纸出厂（examples 就是样板间）。但和
真图纸不同的是：改图纸不需要重新签合同——重启 Prism 即生效，旧请求与
新请求的分界就是重启那一刻。

![契约真源驱动 Prism：请求先验、非法 422、examples 选例、契约 v2 随动](images/prism.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/mocking/08_prism/images/prism.html)
> （或本地打开 [`images/prism.html`](images/prism.html)）。

图里契约在左上、唯一的真源；服务层两件事——先验请求（非法 422）、按
Prefer 选例；右上角的虚线是本篇的题眼：换契约即换行为，0 行代码。

## When to Use

典型场景：

- 契约先行团队：契约已写好，消费方（调用接口的一方）立刻要有真样子的
  mock 联调，不用等 provider（实现接口的一方）写完。
- 想消灭手写 stub 的漂移：规则不再手写，从契约生成——接口改了 mock
  一定跟着改。
- 前端并行开发：按 `Prefer` 头切换不同业务样例（正常/风控/边界），一套
  mock 覆盖多种页面状态。

何时不用：契约还不存在、行为要靠探索 → 声明式 mock（系列 01）或录制
回放（05/06）；要模拟状态流转 → scenario（03），契约驱动的应答无记忆。

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 手写规则（01/02） | 每条规则手维护，接口变更靠人盯 | 无契约、行为自定义优先 |
| 录制回放（05/06） | 应答来自真实交互 | 接口已存在且可调用 |
| 契约驱动（本篇） | 应答从 OpenAPI 生成，非法请求 422 | 契约先行、要零漂移源头治理 |

## Quick Start

前置条件：node/npx（本机 node v22.23.2 ✅，npm 包 `@stoplight/prism-cli`
5.16.0 实测在架）；仓库根 venv（labs/00 体检通过，jsonschema 已装，见
系列 04）；另用 curl 与 lsof（macOS 自带）。

```bash
cd mocking/08_prism && ./prism.sh all
```

实测输出（节选）：

```
=====> [apply] ① 清场 + npx 起 Prism(:9800，契约 v1)
Prism 监听 :9800，契约 contracts/orders_v1.yaml（mock 代码量：0 行）

=====> [observe] ② 契约三事：Schema 校验 / example 优先级 / 422 拒绝
  ✅ 响应过独立 Schema 校验零错误 — 0 条失败
  ✅ Prefer: example=risk-review 切到第二套（review=true） — order_id=ORD-EX-RISK
  ✅ 缺 amount → 422 — Invalid request
    ……

=====> [observe] ③ 契约随动：换 v2（新增必填 channel），不改任何 mock 代码
>>> 旧请求（无 channel）→ 422 红；新请求（带 channel）→ 201 绿
>>> mock 行为随契约而动 ✅（全程只改了 YAML）
```

诚实预期：Prism 返回的应答来自契约 examples——除 example 声明的字段外
不会有别的字段，客户端断言的是「形状与示例符合契约」而非业务值。

422 的拒绝理由（响应体 `validation` 数组的 `message`，如 `Request body
must have required property 'amount'`）会点名具体违规字段，可直接用于
调试消费方代码。

## How It Works

**mock 代码 0 行的含义**。契约里的每个 path+method 就是一条应答规则：
请求先按 `requestBody` 的 schema 校验（缺必填、错类型直接 422，响应体
`validation` 数组指出违规点），合法请求按 `responses` 的 schema 选示例渲染。

mappings（WireMock 的映射文件，一条「什么请求答什么」的记录）、优先级、
匹配器（判定请求命中哪条规则的部件）——01/02 手写的一切，这里都从契约推导。

**example 优先级是可控的**。契约给 201 配了两套 examples（常规/风控），
默认取第一套；带 `Prefer: example=risk-review` 头就切到指定示例——同一
mock、多套业务样例，前端切页面状态不用改任何文件。

**「独立 Schema 校验」校的是谁**。客户端用 PyYAML 从契约里取出 201 响应
的 schema，喂给 jsonschema 库去验 Prism 的实际应答——校验器（jsonschema）
与被测物（Prism）互不依赖，防止「自己出题自己判」。

**契约随动是重启语义**。v2 契约只比 v1 多一个必填 `channel`（enum:
web/pos）：Prism 重启后，无 channel 的旧请求 422、带 channel 的新请求
201。mock 没有被「修改」过——它只是加载了新的真源。

## Pitfalls & Q&A

踩坑清单：

- **Prism 的应答不会回显请求**。现象：请求里传了 customer，应答里没有。
  原因：应答严格按契约的响应 schema/examples 生成，不做请求回显——
  需要回显的是 04 模板的能力。解法：断言形状与示例，别断言业务回显。
- **422 不是 400**。现象：想当然断言 400 的用例红了。原因：Prism 对
  契约违规统一回 422（可处理的实体错误），与 03 状态机的选择一致。
- **npx 首次运行会先下载包**。现象：第一次 `apply` 停顿较久。原因：
  `npx -y` 要先把 `@stoplight/prism-cli` 拉进缓存。解法：预热一次即
  后续秒起。

深入问答：

- **Q：契约驱动的 mock 会「假绿」吗？**
  恰恰相反，它消灭的是最常见的一种假绿——mock 与接口各说各话。剩下的
  风险是「契约本身与真实服务不符」，那要靠 provider 验证（labs/15 的
  契约测试）与漂移巡检（本系列 10）看住，三层防线各管一段。
- **Q：和 03 的 scenario 能结合吗？**
  状态流转是 Prism 的弱项（应答无记忆），它也没有自定义请求匹配的扩展点——
  应答选择只认 `Prefer` 头；复杂状态机更适合 03 的 scenario 或 01 的自研引擎。
  契约驱动管「形状与合法性」，状态机管「历史与顺序」，各管一段。
- **Q：为什么强调「独立」Schema 校验？**
  Prism 内部也做校验，但那是被测物的自我声明。客户端拿契约原件、用
  第三方库（jsonschema）再核一遍，是「不信任被测物自我报告」的测试
  基本原则——本系列 10 的漂移门禁会把这一步常态化。
