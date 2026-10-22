# 02 · 定位策略：从 accessibility id 到 XPath 的优先级

> 同一个元素，`findElement` 能找到，不代表它稳定。Catalog 里 6 个商品共用
> `Product Name`，购物车角标的 `visible` 还和截图相反。读完本篇你能先读
> page source 做侦察，再按 accessibility id → predicate → class chain →
> XPath 的顺序选定位，并把"能定位"变成"改版也不怕"。

## Background

iOS 自动化的第一反应通常是打开 Appium Inspector，点一个元素，复制 XPath
放进代码。单次能跑，但页面层级一变就失效；XPath 还要遍历整棵 UI 树，
在元素多的页面上明显更慢。

iOS 提供了更贴近语义的定位方式：accessibility identifier 是开发给元素起的
稳定名字，predicate 用属性条件筛选，class chain 用层级和索引定位。
三者的稳定性和成本不同，选错就会把维护成本留给下一条用例。

本实验用 SauceLabs My Demo App 的 Catalog、商品详情、More、Cart 四个页面，
对 6 类元素各做两种定位，并把每次踩到的真实差异写进
[`locator-notes.md`](locator-notes.md)。

## What

六类元素：Catalog tab、Login Button、商品名、商品价格、购物车角标、结算按钮。
每类用 accessibility id / predicate / class chain 中的两种定位，共 12 次查找。

另有一条独立的 XPath 演示用例：证明 XPath 能定位，但不进入主套件。
主用例的 XPath 出现次数由脚本用 grep 检查，必须为 0。

![定位策略优先级：先 id，再 predicate，class chain 兜底，XPath 最后](images/locators.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/02_locators/images/locators.html)
> （或本地打开 [`images/locators.html`](images/locators.html)）。
> 从左到右读：UI 树先被 id 命中；id 不唯一时用 predicate 加条件；
> 需要层级时用 class chain；XPath 只在无路可走时出现。

## When to Use

适合用这套顺序的场景：

- 新页面第一次写用例：先抓 page source，确认哪些元素有稳定 id。
- 修一条 flaky 用例：把脆弱的 XPath 换成 id 或 predicate。
- Code review：检查测试里是否出现"复制 Inspector 的 XPath"。
- 多商品/多卡片列表：id 重复时，用 predicate 的 label 锁定具体一项。

何时不用：一次性脚本可以怎么快怎么来；纯 WebView 页面要用 Web 定位，
不是这套 iOS 原生策略；元素本身没有可读属性时，先推动开发补
accessibility identifier，而不是长期维护索引定位。

四种方式的取舍：

| 方式 | 稳定性 | 可读性 | 什么时候选它 |
|:---|:---|:---|:---|
| accessibility id | 最高 | 最好 | 元素有稳定语义 id |
| predicate | 高 | 好 | id 重复，或需要 label/type 组合条件 |
| class chain | 中 | 一般 | 必须按层级/索引定位，且 XPath 太慢 |
| XPath | 低 | 差 | 只作演示和最后手段 |

## Quick Start

前置条件：完成 01，Appium Server、iPhone 17 模拟器和 My Demo App 已就绪。
脚本会复用 01 的 `apply` 与 `clean`，不重复安装环境。

```bash
cd appium/02_locators
./locators.sh            # apply → observe → clean 全流程
./locators.sh apply      # 只准备环境（转调 01）
./locators.sh observe    # 只跑定位矩阵与 XPath 演示
./locators.sh clean      # 删除构建产物并转调 01 清理
```

`configs/testng.xml` 与 `configs/testng-xpath.xml` 是可选套件文件；
脚本默认用 `-Dtest` 点名执行，避免把 XPath 演示混进主套件。

observe 的真实输出（2026-10-22 实测）：

```
=====> [observe] ① 六类元素 × 两种定位策略（12 次定位）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
Session ID: e57e3106-bad6-49ae-93d5-2b267058ca11
已重置 App 状态并加入 1 件商品（角标 = 1）
✅ 购物车角标：predicate / class chain（visible 属性不可靠，断言存在与文本）
✅ Catalog tab：accessibility id / predicate
✅ 结算按钮：accessibility id / predicate
✅ Login Button：accessibility id / predicate（容器名稳定，子按钮 id 不可靠）
✅ 商品名：id 命中 6 个（有歧义）/ predicate 锁定 Black
✅ 价格：列表 id/class chain + 详情页 id/predicate（$ 29.99）
Session 已关闭

=====> [observe] ② XPath 演示（单独执行，不进主套件）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
Session ID: 161379be-cc7d-4f3d-b8a0-fca88c00ce3b
⚠️ XPath 演示：能定位，但遍历整棵 UI 树，只作最后手段
Session 已关闭

=====> [observe] ③ XPath 纪律检查：主用例必须 0 次
✅ LocatorStrategyTest 中 XPath = 0（演示只在 XPathDemoTest）
```

诚实预期：① 的 6 条用例应全绿，输出顺序由 TestNG 决定，不必按上面的顺序读；
每轮测试开始时会重置 App 并预置 1 件商品，所以角标和结算按钮有稳定状态。
② 的 XPath 用例**单独执行**，它绿不代表主套件允许 XPath。

## How It Works

**先侦察，再写定位。** `driver.getPageSource()` 或 Appium Inspector 能看到
元素的 `name`、`label`、`value`、`type` 和层级。

实测 Catalog 一次渲染 6 个商品，`Product Name` 和 `Product Price` 都各出现
6 次——只看 id 会误以为它们唯一。

**accessibility id 是首选。** `Catalog-tab-item`、`Login Button`、
`ProceedToCheckout` 都属于这一类，语义明确，改版通常不会动。Java 里用
`AppiumBy.accessibilityId(...)`，不要和 HTML 的 `id` 混为一谈。

**predicate 用来收窄条件。** 商品名重复时，用 `label` 锁定具体商品：

```java
AppiumBy.iOSNsPredicateString("label == 'Sauce Labs Backpack - Black'")
```

角标没有稳定 id，就用 `name` + `type` 组合：

```java
AppiumBy.iOSNsPredicateString("name == '1' AND type == 'XCUIElementTypeStaticText'")
```

**class chain 用在必须看层级的地方。** 列表价格没有唯一 id，第一个价格元素
可以用 class chain 锁定：

```java
AppiumBy.iOSClassChain("**/XCUIElementTypeStaticText[`name == \"Product Price\"`][1]")
```

它比 XPath 快，但 `[1]` 是索引：列表顺序一变，定位就换人。索引只能兜底，
不能当默认写法。

**XPath 是最后手段。** 它从整棵树里匹配节点，元素多时慢，而且对层级变化
敏感。`XPathDemoTest` 只证明"能定位"，主套件里出现 XPath 会被脚本拦截。

**测试数据要可重复。** `BaseTest.resetAppState()` 调
`mobile: clearApp` 清空购物车，再 `mobile: launchApp` 拉起 App；
`seedCart()` 加 1 件商品，保证角标为 1、结算按钮可见。这样用例顺序变化或
重跑都不会依赖上一次的状态。

## Pitfalls & Q&A

**Q：`Product Name` 明明能查到，为什么说它不稳定？**
`findElement` 只返回第一个；列表有 6 个商品时，你锁定的是"碰巧排第一"的
那个。要具体商品，用 predicate 的 `label`。

**Q：列表价格为什么读不到 `$ 29.99`？**
Catalog 的 `Product Price` 元素只暴露标签，金额没有进 page source；
商品详情页的 `Price` 元素才暴露 `$ 29.99`。所以列表页断言"价格元素存在"，
详情页断言"金额正确"，不要硬编造一个列表价格文本。

**Q：角标明明在屏幕上，`isDisplayed()` 却是 false？**
实测 page source 里角标的 `visible="false"`，但文本是 `1`。这类元素的
`visible` 不可靠，断言存在和文本，不要断言 `isDisplayed()`。

**Q：Login Button 的子按钮为什么叫 `LogOut-menu-item`？**
界面显示 "Login" 时，子按钮 id 仍然是 `LogOut-menu-item`。这是 App 的
命名遗留，不要用它判断登录状态；定位外层 `Login Button` 容器即可。

**Q：什么时候可以用 XPath？**
只在没有 id、predicate、class chain 可用，且已经接受维护成本时。即便用了，
也要把 XPath 限制在单个演示/兜底用例，不让它扩散到主套件。
