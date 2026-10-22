# 03 · 登录与鉴权矩阵：DataProvider 与系统 alert

> 登录页只有两个输入框，却藏着三个移动端问题：输入后键盘遮住提交按钮、
> 系统 alert 不在普通 DOM 里、LogOut 后登录态没清。读完本篇你能用
> DataProvider 把 5 条场景压进一个套件，并分清哪些断言来自 App 的真实行为，
> 哪些只是 Demo App 2.3.0 的缺陷。

## Background

登录是交易链路的第一道门，也是最适合练"输入 + 等待 + 系统弹窗"的场景。
SauceLabs My Demo App 的登录页刻意做得很简单：用户名和密码**只要非空就放行**，
不存在"密码错误"分支。因此本实验不伪造真实鉴权负例，而是覆盖：

- 正常登录与登录后的状态；
- 空用户名、空密码两条校验；
- 点邮箱建议后自动填充；
- LogOut 后的页面与登录态。

空字段的错误不是页面内文本，而是 iOS 原生 alert。它不按 Web 的 DOM 方式
（DOM 即网页的元素树，Web 表单测试直接在页面结构里找错误文本）暴露。

所以要先定位 `XCUIElementTypeAlert`，再读其中的 `XCUIElementTypeStaticText`。
这一步也是本实验和普通网页表单测试最大的区别。

## What

`appium/03_login` 用 Page Object（页面对象模式：把一个页面的元素定位和操作
封装成一个 Java 类，本实验里就是 `LoginPage`）+ TestNG DataProvider 组织
5 条用例：成功登录、邮箱自动填充、空用户名、空密码、登出。

TestNG 是本系列使用的 Java 测试框架；DataProvider 是它的数据驱动注解，
让同一个测试方法吃多组参数、每组各跑一遍。空字段两行数据由同一个测试方法
执行，所以 TestNG 报告里是 5 次运行、4 个方法。

| 场景 | 输入 / 动作 | 关键断言 |
|:---|:---|:---|
| 成功登录 | 选 `alice@example.com` → 点 Login | Catalog 可见；More 页出现 `LogOut-menu-item` |
| 邮箱自动填充 | 选 `bob@example.com` | 用户名等于 `bob@example.com`；密码非空；键盘未弹出 |
| 空用户名 | 不选建议，直接点 Login | alert `Validation Error!` / `Username is required` |
| 空密码 | 选 `bob@example.com` → 清空密码 → 提交 | alert `Validation Error!` / `Password is required` |
| 登出 | 登录 → More → LogOut | 回到 Login 表单；`clearApp` 后 `Login Button` 重新可见 |

![登录与鉴权生命周期：主路径、校验分支与 LogOut 缺陷](images/login-lifecycle.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/03_login/images/login-lifecycle.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开 [`images/login-lifecycle.html`](images/login-lifecycle.html)）。
> 从左到右读主路径；`Validation Error` 是空字段分支；最后一段单独标出
> LogOut 的登录态缺陷和 `clearApp` 复位。

## When to Use

适合用这套结构的场景：

- 一个表单有多个等价输入组合，想避免为每一行复制一个测试方法；
- 需要断言原生 alert 的标题和正文，而不只是断言"页面没跳转"；
- 登录后要验证跨页面状态（Catalog / More / LogOut）；
- 移动端输入被键盘遮挡，需要可重复的提交方式。

不适合直接照搬的场景：

- 真实鉴权系统：要补错误密码、锁定、验证码、token 过期等分支；
- 只做一次性手工验证：不必为 5 条路径搭 Page Object；
- 需要并行多设备：当前 `BaseTest` 是单 session（一次从连接 Appium 到
  `driver.quit()` 的自动化会话），多设备要先拆配置和 WDA（WebDriverAgent，
  Appium 驱动 iOS 的自动化代理）端口。

## Quick Start

前置条件：完成 01/02，Appium Server、iPhone 17 模拟器和 My Demo App 已就绪。
`login.sh` 复用 `../01_ios_session` 的 `apply` / `clean`，不重复安装环境。

```bash
cd appium/03_login
./login.sh all            # apply → observe → clean
./login.sh apply          # 只准备环境（转调 01）
./login.sh observe        # 只跑 LoginTest
./login.sh clean          # 删除 target / test-results 并转调 01 清理
```

也可以直接跑 Maven；`-Dtest` 只点名登录套件：

```bash
mvn -q -Dtest=LoginTest test
```

`configs/testng.xml` 是同一套用例的 TestNG suite 入口，便于后续并入更大套件。

observe 的真实输出（2026-10-22 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] 登录与鉴权矩阵（5 条用例）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
Session ID: <本次 session>
✅ 成功登录：Catalog 可见，More 页显示 LogOut-menu-item
✅ 邮箱自动填充：用户名和密码均已填充，键盘未弹出
✅ 空字段校验：空用户名 → Validation Error! / Username is required
✅ 空字段校验：空密码 → Validation Error! / Password is required
⚠️ Demo App 的 LogOut 未清除登录态；clearApp 后 Login Button 重新可见
Session 已关闭
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，负责运行 TestNG 并把
结果写入 `target/surefire-reports`）：

```text
Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 38.88 s -- in dev.handson.appium.LoginTest
```

诚实预期：5 条都绿不代表 LogOut 行为正确。最后一条用例先验证"LogOut 回到
登录表单"，再用 `clearApp` 复位并验证 `Login Button` 可见；它证明的是
**测试能在缺陷存在时稳定跑完**，不是"App 登出逻辑没问题"。

## How It Works

**先建立干净的起点。** `BaseTest.@BeforeMethod` 对每条用例执行
`mobile: clearApp` + `mobile: launchApp`，等 `Catalog-tab-item` 出现后才开始。
这样用例顺序不影响结果，也不会继承上一条的登录态或购物车状态。

**登录页没有可用的 `name` / `label`，用 class chain 锁类型。** class chain
是 Appium 的 iOS 定位语法，按元素类型逐层匹配（如 `**/XCUIElementTypeTextField`）；
用户名和密码没有可用的名字，只能靠元素类型区分。

用户名是 `XCUIElementTypeTextField`，密码是 `XCUIElementTypeSecureTextField`。
提交按钮是 `XCUIElementTypeButton[name == "Login"]`。这三个定位都放在
`LoginPage`，测试方法不直接写定位字符串。

**邮箱建议是登录页的捷径，也是自动填充场景。** 点 `bob@example.com` 后，
App 会同时填充用户名和密码，而且不弹键盘。测试因此断言用户名等于邮箱、
密码非空、键盘不可见；不要再用 `sendKeys` 覆盖密码，否则会改变被测路径。

**键盘遮挡时，Tab + doubleTap 比 hideKeyboard 可靠。** 清空密码后键盘会重新
弹出，并盖住 Login 按钮。`driver.hideKeyboard()` 在这个 App 上直接报
"Did not know how to dismiss the keyboard"。

第一步，用 Appium 的 `mobile: keys` 发送实际字符 `U+E004`（Tab），键盘会移到
屏幕外（`visible=false`）。

第二步，普通 click 仍会被键盘拦截，并给密码追加一个圆点。所以要用
`mobile: doubleTap`（或 `mobile: twoFingerTap`）带 `elementId` 点击 Login。
`submitWithKeyboardCoveringButton()` 把这三步封装在一起。

**系统 alert 分两层读。** 先等 `XCUIElementTypeAlert` 可见，再取其中的
`XCUIElementTypeStaticText`。

第 1 个是标题 `Validation Error!`，第 2 个是正文 `Username is required` /
`Password is required`。读完点 alert 内的第一个按钮关闭，避免阻塞下一条用例。

**LogOut 的行为要如实记录。** 当前 Demo App 点 `LogOut-menu-item` 只回到空白
Login 表单，登录态仍在；再次进入 Catalog → More 仍能看到 LogOut。

`terminateApp` + `launchApp`、`ResetAppState-menu-item`、`mobile: clearKeychains`
都不能恢复未登录，只有 `mobile: clearApp` 能清掉。

因此 `logoutReturnsToLoginForm` 先断言 LogOut 后的表单，再复位、进入 More、
断言 `Login Button` 可见，并在输出里打印警告。

## Pitfalls & Q&A

**Q：为什么不用 `hideKeyboard()`？**
这个 App 的键盘不支持该命令，调用会抛 "Did not know how to dismiss the
keyboard"。

Tab 能把键盘移出屏幕；注意发送的是实际字符 `U+E004`，不是六个字符的
字面量 `\uE004`，后者会报 "Input key ... is too long"。

**Q：Tab 之后为什么不能直接 `click()` Login？**
键盘虽然不可见，单指 tap/click 仍可能被系统键盘层接住，表现为密码框多一个
圆点、alert 不出现。`mobile: doubleTap` 或 `mobile: twoFingerTap` 带
`elementId` 才能稳定触发按钮。

**Q：为什么没有"密码错误"用例？**
Demo App 只校验非空，任何非空密码都会登录成功。硬造一个"错误密码"负例，
测试会在 App 放行时失败，但失败原因是假设错了，不是产品缺陷。真实项目里
再按真实鉴权接口补这一分支。

**Q：LogOut 用例绿了，是不是说明登出正常？**
不是。用例分成两段：第一段只断言 LogOut 后回到 Login 表单；第二段显式
`clearApp` 后断言 `Login Button` 回来。

README 和测试输出都标注了这是 Demo App 缺陷的 workaround；验收原文里的
"登出后 Login Button 可见"在当前 App 上不成立。

**Q：为什么要区分 `Login Button` 和 `Login`？**
More 页的 `Login Button` 是进入登录页的容器；登录表单里的 `Login` 才是提交
按钮。

前者用 accessibility id（App 给控件预留的无障碍标识，相当于稳定的控件 ID），
后者用 class chain。混用会在错误页面等超时。

**Q：测试顺序会影响结果吗？**
不会依赖顺序。每条方法前都会 `clearApp` + `launchApp`，登录态和页面都从
Catalog 重新开始；失败时先看 surefire 报告里的 session 日志，再确认模拟器
没有被其他 session 占用。
