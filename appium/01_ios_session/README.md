# 01 · 首会话：从 TestNG 用例到 iOS 模拟器

> Appium 的第一条用例不是"写个断言"那么简单：Java 测试把 capabilities 发给
> Appium Server，XCUITest driver 编译并拉起 WebDriverAgent，WDA 再通过 XCTest
> 操控模拟器里的 App。五层里任何一层没对齐，你看到的都只是
> `session not created`。

## Background

iOS 自动化的门槛在第一会话最高。Android 的 UiAutomator 随系统提供，
iOS 却要求测试框架先编译 WebDriverAgent（WDA）——一个 XCTest Runner，
由它把"点击/查找元素"翻译成 XCTest 调用。

WDA 首次编译要 2-5 分钟。这期间界面看起来像卡住，
很多人提前 Ctrl-C，然后把"Appium 起不来"写进笔记。

第二道坎是工具链：`xcode-select` 可能指向 Command Line Tools，
而 WDA 编译必须用完整 Xcode，错误通常以 `xcodebuild failed` 出现。

首会话其实只做三件事：建立 session、让 App 出现在 Catalog 首屏、
正常释放 session。本实验把每件事都留下可验证的证据。

## What

本实验用 Java 17 + Maven + TestNG + Appium Java Client 9.4，
连接 Appium 3.8 / XCUITest 12.19，在 iPhone 17（iOS 26.5）模拟器上
启动 SauceLabs My Demo App。

断言 `Catalog-tab-item` 可见，最后 `quit()`。`BaseTest` 建/拆 session，
`FirstSessionTest` 写断言，`ios_session.sh` 串起准备、运行、清理。

![首会话：从 TestNG 用例到 iOS 模拟器的五层调用](images/ios_session.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/01_ios_session/images/ios_session.html)
> （或本地打开 [`images/ios_session.html`](images/ios_session.html)）。
> 三段是建立会话、启动 App、断言与释放；红色竖条是 WDA 的存活区间。

## When to Use

适合用这套最小会话的场景：

- 新机器、新 Xcode 或新 iOS runtime 到位后，先验证 iOS 工具链是否闭环。
- 新项目搭第一根冒烟用例：先证明"能启动、能找到元素"，再堆业务断言。
- CI 的 iOS 健康检查：WDA 有缓存时一次约 5 秒，足够放进每条 PR。
- 排查"是环境坏了还是用例写错了"：先跑首会话，把变量缩到最小。

不适合：只查进程存活（`curl /status` 就够）、测接口、需要业务状态复现的场景。

## Quick Start

前置条件：macOS + 完整 Xcode（本实验用 Xcode 26.6）、iPhone 17 /
iOS 26.5 模拟器、Java 17+、Maven 3.9+、Node 20+，以及 4723 端口空闲。

```bash
cd appium/01_ios_session
./ios_session.sh          # apply → observe → clean 全流程
./ios_session.sh apply    # 只准备环境：Appium、模拟器、App
./ios_session.sh observe  # 只跑 FirstSessionTest
./ios_session.sh clean    # 停止脚本启动的 Appium，删除 target
```

首次运行会自动安装 Appium 3.8 与 XCUITest driver，
并下载约 6 MB 的 My Demo App。
WDA 第一次编译需要 2-5 分钟；有缓存后全流程实测 5.4 秒。

observe 的真实输出（2026-10-22 实测）：

```
=====> [observe] 运行 FirstSessionTest：建立会话 → 启动 App → 断言 Catalog tab
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
Session ID: fbe104bd-6fe7-450f-94bf-f1f75a0f493b
找到 Catalog-tab-item，App 已启动
Session 已关闭
```

验收命令与结果：

```bash
./ios_session.sh apply
mvn -q -Dtest=FirstSessionTest test; echo "mvn_exit=$?"
curl -s -o /dev/null -w "status_http=%{http_code}\n" \
  http://127.0.0.1:4723/wd/hub/status
./ios_session.sh clean
# mvn_exit=0
# status_http=200
```

`mvn_exit=0` 证明断言通过；`status_http=200` 证明 `driver.quit()`
之后 Appium Server 仍然存活——这两件事经常被混为一谈。

## How It Works

**capabilities 是五层之间的合同。** 四个关键值是 `deviceName`、
`platformVersion`、`automationName` 和 `bundleId`。

本实验分别取 `iPhone 17`、`26.5`、`XCUITest`、
`com.saucelabs.mydemo.app.ios`。

前两个决定去哪台模拟器，第三个决定由哪个 driver 接单，
第四个告诉 driver 启动哪个 App。用 `bundleId` 而不是 `app` 路径，
意味着 App 必须已经安装；`noReset=true` 则保留 App 数据。

**session 创建是一次握手，不是一次 HTTP 调用。** Appium 收到
`POST /session` 后解析 capabilities，交给 XCUITest driver；
driver 检查 Xcode、模拟器和 WDA，必要时编译并启动 WDA Runner。

WDA 就绪后才返回 session id。时序图里 `创建会话` 到 `WDA 就绪`
之间的等待，就是首次运行那 2-5 分钟。之后每条命令都走
`用例 → Appium → XCUITest → WDA → 模拟器`。

**定位用的是 accessibility identifier。** `By.id("Catalog-tab-item")`
在 iOS 上映射到元素的 accessibility identifier，而不是 HTML 的 `id`。
`WebDriverWait` 最多等 30 秒，避免首屏没渲染完就断言。

**quit 释放的是会话，不是服务器。** `driver.quit()` 发送
`DELETE /session`，停掉本次 WDA 会话并释放模拟器占用；
Appium Server 继续监听 4723。

脚本只清理自己启动的 server，4723 上已有的外部实例不会被误杀。

## Pitfalls & Q&A

**Q：`xcodebuild failed` / WDA 起不来？**
先看 `xcode-select -p`；指向 CommandLineTools 时 WDA 编译必失败。

临时 `export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`，
永久 `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer`。

`ios_session.sh` 已默认导出 `DEVELOPER_DIR`。

**Q：session 建好了，但 App 没启动？**
`bundleId` 只对已安装的 App 有效；用 `simctl get_app_container` 确认，
没有就 `./ios_session.sh apply`。同时确认 `platformVersion` 与 runtime 一致。

**Q：为什么 Maven 编译报 `找不到 ContextAware`？**
Java Client 9.4.0 的 Selenium 范围是 `[4.26.0, 5.0)`，Maven 选到 4.51；
而 Selenium 4.34 起删除了这个接口。本实验用 `selenium-bom:4.33.0` 锁住。

**Q：首次运行为什么这么慢？**
慢在 WDA 首次编译；缓存后约 5 秒。别把 `wdaLaunchTimeout` 调到 10 秒，
本实验给 240 秒——首次编译必然超过 10 秒。

**Q：`driver.quit()` 之后还要关 Appium 吗？**
不用。quit 只释放 session；`./ios_session.sh clean` 才关脚本启动的 server。
`curl http://127.0.0.1:4723/wd/hub/status` 返回 200 说明 server 仍在。

**Q：为什么 URL 里带 `/wd/hub`？**
本实验启动 server 时加了 `--base-path /wd/hub`，客户端 URL 也要带。
若改用 Appium 3 默认根路径，启动参数和 URL 两边同步去掉。
