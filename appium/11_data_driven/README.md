# 11 · 数据驱动与测试数据隔离：DataProvider + JSON 数据源

> 同一条结算流程，5 组地址和支付数据各跑一遍——复制粘贴 5 个测试方法
> 是下策，数据驱动才是正解。读完本篇你能用 DataProvider 从 JSON 数据源
> 读用例，用唯一收件人证明"数据真的生效了"，并理解为什么每条数据前
> 必须重置应用。

## Background

结算流程写完一条 E2E 后，自然的追问是：换个地址、换张卡还成立吗？
没有数据驱动时，答案是复制测试方法再改字面量——5 组数据 5 份代码，
改一个字段要改 5 处，漏一处就是假绿。

数据驱动把"流程"和"数据"分开：流程代码只写一份，数据放 JSON 文件，
测试框架按行喂给同一个方法。移动端还有第二个坑：应用状态存在本地，
上一条数据留下的购物车、登录态会污染下一条——不重置的数据驱动是
随机结果生成器。

本实验把两条都解决：JSON 数据源 + 每条数据前 clearApp 重置，并给
每组数据生成唯一收件人，让"数据生效"这件事本身可断言。

## What

`appium/11_data_driven` 复用 06 的 `flows/CheckoutFlow` 编排器，
新增 `CheckoutDataDrivenTest`：DataProvider 读
`testdata/checkout-cases.json`（5 组：英国/美国/中国/德国/日本）。

每组生成唯一收件人后独立跑完整结算。

| 要素 | 实现 | 断言 |
|:---|:---|:---|
| 数据源 | `checkout-cases.json`，Jackson（Java 生态最常用的 JSON 解析库，本篇唯一新增的 Maven 依赖）解析 | 5 组数据 5 次运行 |
| 唯一收件人 | 姓名 + 毫秒后缀（36 进制） | Review 页源码含唯一姓名 |
| 隔离 | 每条数据前 clearApp | 5 组全部独立成功，顺序无关 |

![数据驱动结算：JSON 数据源到 5 次独立结算](images/data-driven-flow.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/11_data_driven/images/data-driven-flow.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/data-driven-flow.html`](images/data-driven-flow.html)）。
> 左侧是数据源与隔离手段，右侧是每组数据的结算管线。

## When to Use

适合套用这套结构的场景：

- 同一流程要覆盖多组输入（地址、表单、搜索词、金额边界）；
- 数据需要 review（JSON 可以在 code review 里逐行看）；
- 用例间有状态污染，需要"每条数据前重置"的强隔离。

不适合直接照搬的场景：

- 各组流程步骤不同（那不是数据驱动，是不同用例——分开写）；
- 数据量大到影响 review（几百组该考虑外部数据平台或生成器）；
- 断言依赖数据间顺序（好的数据驱动用例彼此独立，依赖顺序是设计问题）。

## Quick Start

前置条件：完成 06，Appium Server、iPhone 17 模拟器和 My Demo App
已就绪。`datadriven.sh apply` 复用 01 环境脚本。

```bash
cd appium/11_data_driven
./datadriven.sh all          # apply → observe → clean
./datadriven.sh observe      # 只跑 CheckoutDataDrivenTest
mvn -q -Dtest=CheckoutDataDrivenTest test   # 或者直接用 Maven
```

observe 的真实输出（2026-10-23 实测；后缀每次运行不同）：

```text
=====> [observe] 数据驱动结算（5 组数据 × 完整结算）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
▸ 数据组 1（英国标准地址）：收件人=Rebecca Winter-mvkeozpc
▸ 数据组 2（美国西海岸）：收件人=Alice Johnson-mvkepl7c
▸ 数据组 3（中国地址）：收件人=李雷-mvkeq6wm
▸ 数据组 4（德国长地名）：收件人=Klara Musterfrau-mvkeqtlt
▸ 数据组 5（日本短字段）：收件人=Yamada Taro-mvkergek
✅ 数据组 3：Review 页收件人核验通过
▸ 步骤 40：下单成功，出现 CheckoutComplete-screen
✅ 数据组 5：下单完成
…（块为节选；每组含 8 条"▸ 步骤 N"流程日志，此处省略；
实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 145.8 s -- in dev.handson.appium.CheckoutDataDrivenTest
```

诚实预期：5 组数据里含中文地址与中文姓名（"李雷"），iOS 输入框对
sendKeys 直填 CJK（中日韩字符）无问题；但中文姓名拼上后缀后较长，Review 页源码
按子串匹配即可。整组套件约 2.5 分钟（每组一次完整结算约 30 秒）。

## How It Works

**DataProvider 返回二维数组，每行触发一次测试方法。**
`checkoutCases()` 用 Jackson 把 JSON 读成 `List<Map<String,String>>`
再转 `Object[][]`。

TestNG 对每行调用一次 `checkoutWithDataSettlesEndToEnd(Map)`——
报告里是 5 次运行、1 个方法。

**唯一收件人让"数据生效"可断言。** 如果 5 组都用数据文件里的原始
姓名，第 2 组的 Review 页出现 "Alice Johnson" 时无法区分是本组数据
生效还是上一组的残留。姓名拼上毫秒后缀（36 进制）后，每个名字全局
唯一——Review 页源码含唯一姓名 = 本组数据确实被应用采用了。

**clearApp 是隔离的执行者。** `clearApp` 清掉购物车、登录态、Face ID
开关等全部本地状态，每条数据从同一张白纸出发。重跑某一条失败的
数据也不依赖任何前置——这也是"失败重跑"可靠的前提。

**数据文件进版本库，代码改流程、数据改内容。** 新增一组用例 =
JSON 加一个对象，不动 Java；改流程 = 只动 CheckoutFlow。两者变更
互不牵连。

## Pitfalls & Q&A

**坑：不重置的数据驱动会产生顺序依赖。** 第 1 组登录后，第 2 组可能
跳过登录门——本地页/购物车/登录态全部残留。解法是 BeforeMethod 里
clearApp，每条数据从零开始。

**坑：唯一后缀忘了加，数据生效断言失效。** 原始姓名会跨组重复，
Review 页含姓名的断言在残留场景下也绿。毫秒后缀（36 进制）足够短
且不会撞名。

**坑：CJK 输入在某些键盘状态下可能异常。** 本实验实测
sendKeys("李雷") 直填正常；若你的环境出现输入异常，可先确认键盘
无残留输入法状态，或该行数据改用拼音。

**Q：为什么用 JSON 不用 CSV？**
字段有层次（地址 5 字段 + 支付 4 字段），JSON 按字段名取值不易错位；
CSV 适合扁平表。Jackson 需在 pom 加一个 test 依赖（jackson-databind），解析只需一行代码。

**Q：DataProvider 和 5 个测试方法比，报告里怎么看？**
TestNG 报告显示"1 个方法、5 次运行"，每次运行独立计通过/失败；
失败的那组数据会在报告里带参数（整行 Map），定位到具体哪组数据
一目了然。

**Q：这和 06 的 CheckoutE2ETest 是什么关系？**
06 验证的是流程本身（一条数据）；11 验证的是流程对数据的通用性
（五条数据走同一条流程）。CheckoutFlow 编排器两者共用——这正是
06 把它抽成 flows 的原因。
