# 13 · 报告、截图与失败诊断：Allure 证据链

> 用例失败在凌晨三点，你只有一张"expected 2 but found 1"。读完本篇
> 你能用一个 TestNG 监听器让失败用例自动附带截图、page source、设备
> 日志和录屏——四类证据一条链，成功用例零附件。

## Background

一条 UI 用例失败的根因，往往藏在失败瞬间的画面和界面树里——"expected
2 but found 1" 本身什么都不解释。事后手工复现既慢又可能不复现
（时序类失败尤其如此），诊断信息必须在失败发生的那一刻自动采集。

采集的难点是"去哪拿"：截图和 page source 从 driver 拿；设备日志在
XCUITest 的 syslog 里；画面回放要靠录屏。更麻烦的是时机——必须在
失败后立刻采，还得把它们挂到报告里对应的那条用例上，而不是散落在
临时目录里。

本实验用一个 TestNG 监听器（挂进 TestNG 生命周期的类：每条用例
开始、成功、失败时，TestNG 会自动回调它的对应方法）统一采集四类
证据，接入 Allure 报告（主流的测试报告工具，支持把附件挂在用例上），
并用一条故意失败的用例演示完整证据链。

## What

`appium/13_reporting` 由两部分组成：`DiagnosticListener`（ITestListener
实现，失败时自动采集）+ `ReportingTest`（2 条成功用例 + 1 条故意
失败用例）。套件跑完是 2 通过 1 失败——失败是故意的，它的价值在证据链。

| 用例 | 结果 | 证据 |
|:---|:---|:---|
| 目录名称升序 | 通过 | 无附件 |
| 建议登录 | 通过 | 无附件 |
| 故意失败演示 | 失败（断言 2 vs 1） | 截图 + page source + syslog + 录屏 |

![失败诊断链：录屏、失败采集与 Allure 报告](images/reporting-flow.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/13_reporting/images/reporting-flow.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/reporting-flow.html`](images/reporting-flow.html)）。失败
> 分支的四类证据最终都汇入 Allure 报告的用例详情页。

## When to Use

适合套用这套结构的场景：

- 长跑回归套件（夜间无人值守，失败后靠证据链远程诊断）；
- 时序敏感的 UI 用例（失败瞬间的录屏比任何文字描述都准确）；
- 需要把失败现场发给非自动化的同事复核（Allure 链接即证据包）。

不适合直接照搬的场景：

- 全部用例都稳定的成熟套件（录屏只增加耗时与磁盘占用）；
- 需要在 CI 平台原生报告里看结果（Allure 报告是独立产物，CI 要
  额外发布它）；
- 单条探针实验（前十个实验不接报告，聚焦行为本身）。

## Quick Start

前置条件：完成 01，Appium Server、iPhone 17 模拟器和 My Demo App
已就绪；安装 Allure CLI（`brew install allure`，本机实测 2.46.1）。
`reporting.sh apply` 复用 01 环境脚本。

```bash
cd appium/13_reporting
./reporting.sh all        # apply → observe（含报告生成） → clean
./reporting.sh observe    # 跑用例并生成 target/allure-report
allure serve target/allure-results   # 或者起临时服务在线看
mvn -q test               # 也可以只跑用例不生成报告
```

注意：`all` 的最后一步 clean 会删除 target/——刚生成的 Allure 报告
和录屏会一起被清掉。想看报告，单独跑 `./reporting.sh observe`（生成
后不清理），再执行 `allure serve target/allure-results`。

observe 的真实输出（2026-10-23 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] 报告与失败诊断（3 条用例：2 成功 + 1 故意失败）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
✅ 目录 6 件商品，默认名称升序
[diag] 失败证据已附加：截图 + page source + syslog + 录屏
✅ 建议登录成功：More 页 LogOut 可见
=====> [observe] 生成 Allure 报告（target/allure-report）
  报告已生成。查看：allure serve target/allure-results
…（块为节选；实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件）——**1 条失败是
故意的**，这是演示样本：

```text
Tests run: 3, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 86.14 s
```

诚实预期：故意失败用例断言角标为 "2"（实际是 1），它在 Allure 报告
里应该是红色且带四类附件——这张"失败现场包"就是本实验的交付物。
两条成功用例零附件（录屏停了就丢），这是"成功不产生多余附件"的
验收点。

## How It Works

**监听器挂在 TestNG 的事件流上。** `DiagnosticListener` 实现
ITestListener（TestNG 的用例事件接口：开始、成功、失败都会回调），
在 `onTestStart` 启动录屏，在 `onTestFailure` 采集四类证据。

注册顺序写在 configs/testng.xml：**DiagnosticListener 必须排在
AllureTestNg（Allure 官方提供的 TestNG 监听器，负责把用例结果写进
报告，与 DiagnosticListener 一样注册在 testng.xml 里）之前**。

原因：Allure 处理失败时会关闭该用例的结果上下文（Allure 内部记录
"当前正在写哪条用例"的标记），排后面附件就会掉进容器（container
.json，Allure 为每条用例生成的外层包装文件；附件只有归属到它包住
的那条用例，报告里才显示出来）而不是用例（实测踩过）。

**四类证据四个来源。** 截图与 page source 来自 driver，设备日志在
`manage().logs().get("syslog")`，录屏由 start / stopRecordingScreen
产出（base64 解码成 mp4）。

全部通过 Allure 的 `addAttachment` 挂进报告。

**成功用例零附件的实现是"只停不存"。** `onTestSuccess` 只调用
`stopRecordingScreen` 丢弃录像，不做任何 addAttachment——附件的
生产成本（磁盘、报告体积）只花在失败上。

**附件同时落盘一份。** 录屏额外写到 `target/evidence/<用例名>.mp4`，
不依赖 Allure 报告的存在；`target/` 整体不进版本库（仓库 .gitignore
已覆盖）。

## Pitfalls & Q&A

**坑：Allure.addAttachment 没有 byte[] 重载。** 四个参数版本收的是
InputStream，字节数组要自己包一层 ByteArrayInputStream。编译错误
"找不到合适的方法"就是指这个。

**坑：监听器顺序错了，附件掉进容器。** Allure 处理失败时会关闭用例
的结果上下文（Allure 内部记录"当前正在写哪条用例"的标记）。

排在其后的监听器再 addAttachment 只会落到容器（container.json，
用例的外层包装文件）而不是用例本身。解法是 testng.xml 里把
DiagnosticListener 放在 AllureTestNg 前面。

**坑：`mvn test` 不读 configs/testng.xml。** Surefire 默认按类扫描
跑用例，测试文件里的 testng.xml 不生效——监听器会完全失效（实测
踩过）。解法是 pom 里配置 `suiteXmlFiles` 指向它。

**Q：为什么录屏成功时也启动，却不保存？**
录屏的启动/停止有固定开销（约 1-2 秒），按"失败才停才存"实现，
逻辑最简单；成功时丢弃只浪费这一点点时间，换来监听器无需预知结果。

**Q：syslog 是什么，为什么能从 driver 拿到？**
syslog 是 iOS 设备的系统日志流，XCUITest 驱动通过 `manage().logs()`
暴露它。崩溃、权限、网络错误都会在里面留痕，是截图之外的第二现场。

**Q：Allure 报告目录要提交仓库吗？**
不要。`target/allure-results` 和 `target/allure-report` 都是生成物，
仓库 .gitignore 已覆盖 `target/`。报告的价值在"当场看"，需要留档
时把整个 `allure-report` 目录压缩归档即可。
