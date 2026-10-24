# 08 · WebView 混合应用：Context 切换与它的前提条件

> 混合应用的 Web 内容既能像网页一样断言，也可能在自动化面前"隐身"。
> 读完本篇你会走完 native → Webview → native 的完整往返，理解为什么
> 这个 App 的 WEBVIEW context 永远不出现（WKWebView 没开 inspectable），
> 以及拿不到 context 时如何用 native 树做诚实的降级断言。

## Background

电商 App 里总有几页是网页：活动页、帮助中心、协议。它们运行在原生
App 内嵌的 WKWebView（iOS 的内嵌浏览器组件）里，自动化框架要看懂
网页内容，必须先"切换"到 Web 上下文——Appium 把原生界面和网页
当成两个世界，各自有一套元素树。

切换的前提常被略过：Appium 发现 WEBVIEW context 依赖 WebKit（WKWebView
背后的浏览器引擎）的远程检查协议，而 WKWebView 必须在 App 构建时
显式开启 inspectable（可检查）才允许被检查。App 没开，context 就永远
不会出现——这不是测试代码能修复的。

本实验先按标准路径走一遍：轮询等待 context、切换、断言标题；拿到
context 就切，拿不到就退回 native 树断言 Web 内容——两条路径都以
同一组断言收尾，不假装切换成功。

## What

`appium/08_webview` 用 `webviewConnectTimeout` 能力和轮询逻辑处理
context 的延迟与缺席，TestNG 3 条用例覆盖菜单基线、加载往返和二次加载。

被测页面是本机起的一个静态页（`webview.sh apply` 启动
`configs/webview-page.html`），避免外部网络的不确定性。

| 用例 | 动作 | 断言 |
|:---|:---|:---|
| 菜单基线 | More → Webview 菜单 | URL 输入框默认值；Go To Site 可见；contexts 含 NATIVE_APP |
| 加载与返回 | 填本地 URL → Go To Site → 轮询 context → 返回 | Web 内容 "Hello WebView" 可见；回到 Catalog |
| 二次加载 | 返回菜单再走一遍 | 内容仍可断言 |

![WebView 实验流程：菜单、加载、context 轮询与 native fallback](images/webview-flow.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/08_webview/images/webview-flow.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/webview-flow.html`](images/webview-flow.html)）。context
> 轮询画成菱形分支：拿到 WEBVIEW 就切换断言标题，拿不到走 native
> fallback，两路汇合到同一组内容断言。

## When to Use

适合套用这套结构的场景：

- App 内嵌网页（活动页、帮助、协议）的加载与返回回归；
- 混合应用的灰度场景：App 版本不同，inspectable 开关可能不同，
  用例自动适配两种状态；
- 需要本地可控页面替代外部网站做验证的流程。

不适合直接照搬的场景：

- 纯原生页面（没有 context 概念，直接断言元素）；
- 依赖登录态或 Cookie 的网页（本地静态页没有这些概念）；
- 需要验证网页内部交互（表单、跳转）的深度 Web 测试——那应该用
  浏览器测试栈（Playwright/Cypress 系列）做。

## Quick Start

前置条件：完成 01，Appium Server、iPhone 17 模拟器和 My Demo App
已就绪。`webview.sh apply` 复用 01 环境并启动本地测试页
（端口 8923）。

```bash
cd appium/08_webview
./webview.sh all          # apply（起本地页） → observe → clean
./webview.sh observe      # 只跑 WebViewTest（需先跑过 apply：本地页要在 8923 起着）
mvn -q -Dtest=WebViewTest test   # 替代 observe，同样需先 ./webview.sh apply
```

`all` 末尾的 clean 会停掉本地页，之后想单独 observe 需先重新
`./webview.sh apply`。

observe 的真实输出（2026-10-23 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] WebView 混合应用（3 条用例）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
⚠️ 30 秒内未出现 WEBVIEW context——该构建 WKWebView 未开 inspectable，context 切换不可用（如实记录）
✅ Web 内容断言（native 树）：Hello WebView 可见
✅ 菜单页基线：URL 输入框 + Go To Site，contexts=[NATIVE_APP]
✅ 二次加载后内容仍可断言：Hello WebView 可见
…（块为节选；轮询日志每 5 秒一行，此处省略；实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 614.7 s -- in dev.handson.appium.WebViewTest
```

诚实预期：这套件跑一次约 10 分钟，慢在 30 秒 + 10 秒 + 10 秒的三段
context 轮询——在 context 真的会出现的环境里，轮询第一秒就返回。

当前环境下 context 始终不出现（该 App 构建未开 inspectable，模拟器级
`defaults write` 强制开启也无效），断言退回 native 树：Web 内容以
StaticText（原生树里的纯文本元素）形式暴露，"Hello WebView" 可定位
即可证明页面加载成功。

## How It Works

**context 轮询是双信号等待。** `pollForWebviewContext()` 每秒读一次
`getContextHandles()`，看到含 WEBVIEW 的 context 就返回名字；30 秒
超时返回 null。

调用方据此分支：有 context → `driver.context(...)` 切换并断言
`getTitle()`；没有 → 打印警告，走 native 断言。

**Web 内容会以原生文本元素出现在 native 树。** 切不了 context 不等于
断不了言：WKWebView 里的标题和正文会以 `XCUIElementTypeStaticText`
（iOS 原生树里的纯文本元素）的形式出现——这是 iOS 无障碍系统的行为。

断言 `label == 'Hello WebView'` 就能证明本地页真的加载了。

**本地页替代外部网站。** 菜单页默认 URL 是
`https://www.website.com`——在本网络环境永远停在 "Loading"。

`webview.sh apply` 在本机 8923 端口起了一个静态页
（`configs/webview-page.html`，标题 WebView Demo），测试清空输入框
填入 `http://127.0.0.1:8923/`，加载即时完成。

**返回路径有两次导航和一次键盘陷阱。** 返回箭头无任何标注
（name/label 为 null），且 x/y 坐标不能用于 NSPredicate（实测谓词
零命中），只能遍历按钮按 rect（元素的屏幕矩形框，含 x/y 坐标和宽高）
过滤：左上角、y<150 的那个。

返回一次只到菜单页，URL 输入框会自动聚焦弹键盘——键盘盖住 tab 栏，
点击 Catalog 全部落空。再按一次返回到 More 页，焦点随导航离开，
键盘自然消失，此时切 tab 才有效。

**离开 WebView 后可达性树（iOS 无障碍系统维护的界面元素树，也是
自动化读到的元素树）会短暂陈旧。** 回到 Catalog 后源码里可能
找不到 "Products" 标题（屏幕上明明有）。

等 `Product Name` 元素的 presence 并重切一次 tab 即可恢复——和 07
的 visible 标志怪癖同族，解法都是"等存在，不等可见"。

## Pitfalls & Q&A

**坑：context 永远只有 NATIVE_APP。** 该 App 构建的 WKWebView 没开
inspectable——iOS 16.4+ 后这是 App 侧代码的事
（`webView.isInspectable = true`），测试侧无法开启。

模拟器 `defaults write` 强制开启实测也无效。解法是 native fallback
断言。

**坑：默认 URL 加载不出来。** 菜单页预填 `https://www.website.com`
（广告停放域名），本网络下永远 Loading。`webview.sh apply` 起本地页
解决，这也让实验不依赖外网。

**坑：返回箭头找不到。** 它 name/label 全空，x/y 又进不了谓词。
解法是遍历按钮取 rect：左上角（x≤10 且 y<150）的那个就是它。

**坑：回菜单页后 tab 点击全部落空。** URL 输入框自动聚焦弹出键盘，
正好盖住 tab 栏。解法是再按一次返回到 More 页，焦点随导航离开。

**Q：为什么轮询要 30 秒这么久？**
`webviewConnectTimeout` 给了 30 秒的连接窗口，轮询与之对齐。在
inspectable 正常的环境里 context 几秒内出现、轮询立即返回；30 秒
只在"永远不出现"的环境里才走满，代价是套件变慢（约 10 分钟）。

**Q：native fallback 断言会不会掩盖页面加载失败？**
不会反过来：加载失败时 "Hello WebView" 不出现，断言照样红。fallback
只是换了证据来源（native 树里的原生元素，而非 Web 世界的 title），
断言强度没有降低——它验证的仍是"页面加载出了预期内容"。
