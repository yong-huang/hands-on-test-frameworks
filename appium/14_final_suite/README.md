# 14 · 🏁 终极回归套件：双模拟器并行、Retry 与 10 连跑

> 前十三个实验的能力最终要变成一条命令能跑的回归体系。读完本篇你能
> 在两台模拟器上并行跑 smoke + regression 两组共 29 条用例，用
> RetryAnalyzer 自动重试偶发失败，并用 N 连跑统计通过率与 flaky 率。

## Background

单条用例绿了不等于套件能交付：回归要回答的是"整套 25+ 条用例在两台
设备上并行跑，连续十轮还全绿吗"。并行引入新问题——两个 Appium
session 若共用 WDA 端口或构建目录会互相冲突；偶发失败（flaky）会
污染通过率的统计。

工程上的三个对策：**套件分组**（smoke 快速反馈 + regression 全量）、
**资源隔离**（每个 session 独占 wdaLocalPort 和 derivedDataPath）、
**失败重试 + 连跑统计**（偶发失败自动重试一次，重试后通过计入
flaky 而不是失败）。

本套件是全系列的收官：smoke 组复用 03/04/05/07/10 的快速用例，
regression 组覆盖 04/05/08/09/10/11 的全量能力，页面对象复用 12 的
POM 分层。

## What

`appium/14_final_suite` 的套件 XML（configs/final-suite.xml）定义
两个并行 <test> 块，各绑定一台模拟器：

| 组 | 设备 | 用例数 | 覆盖 |
|:---|:---|:---:|:---|
| smoke | iPhone 17（wdaLocalPort 8100） | 8 | 登录、目录升序、降序、角标、购物车、删除、后台、重置 |
| regression | iPhone 17 · 2（wdaLocalPort 8101） | 21 | 目录×3、购物车×3、生命周期×4、专项×6、数据驱动×5 |

RetryAnalyzer 让每条失败用例自动重试 1 次；RetryTransformer 把它
挂到全部 @Test 上。run_suite.sh 支持 N 连跑并归档每轮报告。

![终极套件：双模拟器并行、分组与 10 连跑统计](images/final-suite.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/14_final_suite/images/final-suite.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/final-suite.html`](images/final-suite.html)）。两条泳道
> 即两台模拟器，smoke 跑完即出快速反馈，regression 全量收尾。

## When to Use

适合套用这套结构的场景：

- 多设备回归的日常执行（一条命令、并行出结果）；
- 版本发布前的稳定性验证（N 连跑 + flaky 统计）；
- 新用例接入现成回归体系（加一个 groups 标签即可归组）。

不适合直接照搬的场景：

- 单设备调试（并行编排是额外复杂度，直接跑单套件）；
- 云真机矩阵（设备 Farm 有自己的并行模型，本地双模拟器只是入门）；
- 需要跨 iOS/Android 的双端并行（两端驱动与端口模型不同，需分别
  建套件再在同一流水线汇总）。

## Quick Start

前置条件三条：①完成 01-13；
②被测应用包在 `/tmp/SauceLabs-Demo-App.Simulator.zip`（重启过机器
按实验 01 重新下载解压）；③第二台模拟器已创建（`xcrun simctl
clone`，克隆连应用一起复制）。Appium Server 无需手动启动——
`run_suite.sh` 的 setup 会先复用实验 01 的 `ios_session.sh apply`
（幂等：已启动则跳过）。

**UDID 与构建路径必须替换**：`run_suite.sh` 顶部的 `UDID1`/`UDID2`
和 `configs/final-suite.xml` 里的 `device.udid` 要改成你机器上查询
到的 UDID（iOS 模拟器的唯一设备标识，两处必须一致）。

`derived.dataPath` 改成本机可写目录。

不替换的话安装与启动会静默失败，最终表现为 session 创建报
device not found。

```bash
cd appium/14_final_suite
./run_suite.sh        # 默认 1 轮：双模拟器并行跑 29 条
./run_suite.sh 10     # 10 连跑：每轮归档报告到 target/archive/run-N
```

单轮的真实输出（2026-10-23 实测）：

```text
=====> [setup] 启动双模拟器

=====> [setup] 两台模拟器上安装/更新被测 App

=====> [setup] 起本地 WebView 页（8923）
  本地页就绪

=====> [run 1/1] 双模拟器并行：smoke（iPhone 17）+ regression（iPhone 17 · 2）
  ── 第 1 轮：总用例 29，通过 29，失败 0（含重试前失败）


=====> [summary] 1 轮总汇
  总用例数：29
  通过：29
  失败：0
  flaky（重试后通过）：0
  🏁 1 轮连续全绿
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 29, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 453.9 s -- in TestSuite
```

诚实预期：10 连跑在双模拟器并行负载下约需 70-80 分钟（归档实测
每轮约 7.5 分钟）；首轮还包含两台设备各自的 WDA（WebDriverAgent，「并行的基础是
资源隔离」一段说的自动化代理）构建（首次 2-5 分钟）。

并行负载下的偶发失败由 RetryAnalyzer 兜底，重试后通过的计入
flaky 统计——flaky 率是套件健康度的核心指标，目标为零。

## How It Works

**并行的基础是资源隔离。** 两个 session 各自设置
`setWdaLocalPort(8100/8101)` 和 `setDerivedDataPath`（独立构建目录）
——共用任一项都会让两个 WebDriverAgent 互相覆盖。

设备参数从套件 XML 的 `<parameter>` 注入 BaseTest，每个 <test> 块
在自己的线程里建独立 session。

**分组靠 TestNG groups。** 用例标注 `groups = "smoke"` 或
`"regression"`，套件 XML 用 `<groups><run><include>` 挑选——同一批
测试类可以同时服务两个组，新增用例只需打对标签。

**RetryAnalyzer 给偶发失败一次自愈机会。** IRetryAnalyzer 的
retry() 在失败时返回 true 触发重试，最多 1 次；RetryTransformer
通过 IAnnotationTransformer 把它挂到全部 @Test，用例无需逐个声明。

**连跑统计把稳定性变成数字。** run_suite.sh 循环 N 轮，每轮归档
surefire 报告到 `target/archive/run-N`；汇总阶段累加总用例、通过、
失败。

RetryAnalyzer 在用例首次失败、触发重试时打"⚠️ flaky：…"日志；
run_suite.sh 汇总阶段用 grep 统计各轮日志里的标记数。标记按"至少
失败过一次"的用例计：重试后通过的构成 flaky，重试仍失败的会同时
计入失败数——需要更精确的归因时，去各轮日志按用例名检索。

## Pitfalls & Q&A

**坑：共用 WDA 端口或构建目录。** 两个并行 session 用同一个
wdaLocalPort 会端口冲突，共用 derivedDataPath 会互相覆盖构建产物
——症状是其中一个 session 随机超时。每个 <test> 块必须配独立的
wdaLocalPort 和 derivedDataPath。

**坑：第一轮特别慢。** 两台设备首次都要构建 WebDriverAgent（每台
2-5 分钟）。这是 Xcode 的正常行为；后续轮次复用构建产物。

**坑：reset 后 tab 栏粘滞。** Reset App State 确认后应用停在 More
页且 tab 栏不可见（07 同款）。套件里的重置用例改用角标断言（重启
应用后角标应消失），绕开粘滞状态下的导航。

**Q：为什么 smoke 和 regression 会有重叠用例？**
冒烟组是回归组的子集——同样的用例先在 smoke 里快速过一遍。两组在
不同设备上并行，重叠是有意的冗余，不是浪费。

**Q：flaky 率怎么算，目标是多少？**
flaky 次数 = 各轮日志中"⚠️ flaky："标记的条数（run_suite.sh 用
grep 统计），flaky 率 = flaky / 总用例。目标为零：出现 flaky 说明
有需要根治的时序或环境问题，重试只是给诊断争取时间。

**Q：为什么深链接不在套件里？**
该 App 未注册自定义 URL scheme，`xcrun simctl openurl` 只会打开
Safari。演示可以照敲（能看到 Safari 打开目标网址），套件里没有
可断言的对象。
