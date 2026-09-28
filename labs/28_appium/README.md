# 28 · 移动端测试（Appium）：完整链路 + Playwright fallback 双路径

> Appium 的环境链是全系列最长的（Xcode + Simulator + server + driver）。
> 本实验按"双路径"设计：完整 Appium 链路给出可运行的参考实现与补齐清单；
> 环境受阻时 fallback 到 Playwright 移动视口 + 触屏——fallback 也算完成，
> 且如实记录。读完本篇你能判断移动端测试该走哪条路径、识别链路断在哪一环。

## Background

移动端测试的特殊性是真实的：触屏语义与鼠标不同（tap 不是 click）、真机/模拟器矩阵、设备描述符（把"iPhone 14"翻译成视口/触屏/UA——User-Agent，浏览器向网站自报身份的字符串——的组合）。

但这些特殊性之外，移动测试的环境链也是出了名的长：macOS 上跑 iOS 自动化需要完整 Xcode（不是 Command Line Tools）、Simulator、Appium server、driver（XCUITest），任何一环断掉整条链不可用。


工程上的成熟应对是**双路径**：完整链路给参考实现与补齐清单（环境补齐后
直接能跑）；环境受阻时用等价的降级路径完成同等验收，并**如实记录**
走了哪条路。环境受阻不可耻，假装跑通才可耻。

本实验在本机探测到的断点：`simctl` 不可用（xcode-select 指向
CommandLineTools）+ Appium server 未装——于是 fallback 路径担纲验收。

## What

Appium 是移动端自动化的协议层翻译官：把 WebDriver 协议翻译成 iOS 的
XCUITest / Android 的 uiautomator2 原生驱动——多语言通用，代价是多一层
协议转换延迟。

fallback 路径用 Playwright 的**设备描述符**（device descriptor：
`playwright.devices["iPhone 14"]` 展开成 390×843 视口、`hasTouch`、
移动 UA 的一组参数）模拟移动环境。

用例里的 `.tap()` 走的是**触摸事件**而非鼠标点击，触屏语义真实成立。

可以把设备描述符想成给浏览器办一张"手机身份证"：视口是身高、
hasTouch 是指纹、UA 是口音——三样齐了，Web 应用拿到的就是真手机才有的
输入信号。但和真手机不同的是，它没有原生能力（相机、推送、手势系统），
那些必须真机 + 原生框架。

## When to Use

典型场景：

- 移动 Web 适配验收：小屏布局不出横向滚动条、触屏下单可用、
  竞态按钮触屏可操作——三个验收点 fallback 路径全覆盖。
- 原生 App 冒烟：Appium + XCUITest/uiautomator2，`accessibility id` 定位。
- 环境评估：先探测链路断在哪，再决定补环境还是走 fallback——
  这本身就是移动测试工程师的日常判断。

何时不用：要验证原生能力（相机/推送/生物识别）时 fallback 无能为力，
必须真机 + 原生框架；纯桌面 Web 也不需要移动视口——按用户真实设备
分布决定要不要测移动端。

## Quick Start

前置条件：labs/16 的 Playwright 浏览器就绪；脚本自动起 SUT。

```bash
cd labs/28_appium
./mobile_lab.sh    # ① 环境探测（诚实打印断点）② fallback 三用例
./mobile_lab.sh observe
```

observe 的真实输出（2026-09-28 实测，节选）：

```
=====> [observe] ① 环境探测：Appium 完整链路（Xcode + Simulator + Appium server）
  Appium server: 未安装
  simctl: 不可用（xcode-select 指向 CommandLineTools，无法启动 iOS Simulator）
  ⚠️  Appium 链路受阻（如实记录）。按清单约定，fallback 方案计入完成：
     补齐方式见 appium_reference.py 模块注释；本机先跑 ② 的 fallback

=====> [observe] ② 移动 fallback：Playwright iPhone 14 触屏 + 视口（3 条用例）
collected 3 items

tests/test_mobile_fallback.py ...                                        [100%]

============================== 3 passed in 2.02s ===============================
```

诚实预期：探测段如实打印链路断点（本机：Appium 未装 + simctl 不可用）；
fallback 三条用例（触屏下单/小屏布局/竞态按钮）应全绿。
要跑完整 Appium 链路，按参考实现注释补齐三步：

```bash
sudo xcode-select -s /Applications/Xcode.app        # 启用完整工具链
npm install -g appium && appium driver install xcuitest
appium --base-path /wd/hub                          # 起 server
pip install Appium-Python-Client
```

关键片段（这段在做什么：设备描述符注入 + 触屏操作 + 布局断言）：

```python
device = playwright.devices["iPhone 14"]
context = browser.new_context(**device)         # 视口+触屏+UA 一次到位
page.get_by_role("button", name="创建订单").tap()
assert page.evaluate("document.documentElement.scrollWidth") <= page.evaluate("window.innerWidth") + 2
```

## How It Works

**fallback 的等价性**：设备描述符带来三件事——视口（390×843）、`hasTouch: true`（`.tap()` 走触摸事件而非鼠标点击）、移动 UA。

移动端 Web 的三个验收点（触屏下单、无横向滚动、触屏竞态按钮）全部被覆盖，与 Appium 路径的验收语义等价——等价的是**验收语义**，不是实现路径，这正是双路径设计的要义。


**小屏布局断言**：`scrollWidth <= innerWidth + 2`（允许 2px 余量）——
移动端基本盘是不出横向滚动条。这类断言成本极低、价值极高，
值得进每一条移动用例。

**Appium 参考实现**：`appium_reference.py` 演示了 capabilities 设备声明
（`device_name`/`platform_version`/`automation_name`）。

定位首选是 `accessibility id`（与视觉实现解耦、双语种稳定、
本身就是可访问性要求——一举三得），整体是"启动→定位→断言"的最小闭环。

环境补齐后可直接跑。


**诚实记录的机制**：探测段逐环检查（Appium server → simctl → Xcode），
断在哪一环打印哪一环——fallback 完成的用例与完整链路的用例在报告里
路径可辨，不混淆。

## Pitfalls & Q&A

踩坑清单：

- **把 fallback 当成完整链路糊弄**。现象：报告声称"Appium 测试通过"，
  实际跑的是移动视口。解法：双路径各自标注路径名，验收口径明确。
- **xcode-select 只装了 CommandLineTools 就想跑 Simulator**。现象：simctl
  报不可用。解法：`sudo xcode-select -s /Applications/Xcode.app`
  切换到完整 Xcode（占 ~10GB，按需取舍）。
- **用 `.click()` 代替 `.tap()` 测移动端**。现象：触屏手势类 bug 测不到。
  解法：设备描述符 + `.tap()`，让触摸事件真实发生。
- **漏掉小屏布局断言**。现象：上线后用户侧横向滚动。
  解法：`scrollWidth <= innerWidth + 2` 进每条移动用例。

深入问答：

- **Q：Appium 和 Espresso/XCUITest 的关系？** Appium 是协议层翻译官，
  底层仍驱动 XCUITest/uiautomator2——多语言通用，但多一层延迟。
- **Q：accessibility id 为什么是定位首选？** 与视觉实现解耦、双语种稳定、
  本身就是可访问性要求——一举三得。
- **Q：移动 Web 和原生 App 测试的边界？** 移动 Web 用 Playwright 移动视口
  已覆盖大半；原生能力（相机/推送）必须真机+原生框架。
