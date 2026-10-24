# 12 · POM / 组件对象重构：分层边界与零 findElement

> 前十个实验的定位器散落在各测试类里，流程一长就到处复制。读完本篇
> 你能把登录、目录、购物车、结算收进 Screen Object（页面对象，即下文
> POM 里每个屏幕对应的类）+ Flow（跨屏流程编排层）的三层结构，做到
> 测试类零 `findElement`——并理解为什么业务断言必须留在测试层。

## Background

前十个实验为了聚焦单点能力，定位器都直接写在测试方法里。用例少时
没问题；同一个"点购物车"动作在 04、05、06 里各写了一遍，改一个
accessibility id 就要翻三个文件——定位器的重复是维护成本的第一来源。

第二个问题是边界模糊：测试方法里既有"点哪个元素"（动作）、又有
"等它出现"（等待）、还有"结果对不对"（断言）。三者搅在一起，
用例读起来是流水账，复用无从谈起。

标准解法是页面对象模型（POM，Page Object Model：每个屏幕一个类，
元素定位和操作封装在类里）。本实验在此之上补齐移动端特有的两层：
组件级复用与跨页 Flow 编排。

并用一条硬规则守住边界——**测试类里 `findElement` 出现次数为 0**
（指 4 个 `*PomTest`；夹具基类与 Page/Flow 层除外）。

## What

`appium/12_pom` 把 03/04/05/06 的核心能力重构为三层结构，
`mvn -q test` 跑 6 条核心用例（登录 1、目录 2、购物车 2、结算 1）。

| 层 | 类 | 职责 |
|:---|:---|:---|
| Page 层 | `pageobjects/BasePage` + 4 个屏幕类（ProductPage 一个类同时管详情页和购物车两个屏） | 定位器、显式等待、动作、状态查询 |
| Flow 层 | `flows/PurchaseFlow` | 跨页业务编排（登录门、结算漏斗——地址→支付→Review 逐步收窄的下单链路），带步骤日志 |
| 测试层 | 4 个 `*PomTest` | 业务断言 + 用例组织，零定位器 |

![POM 三层结构：Page 定位、Flow 编排、测试断言](images/pom-layers.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/12_pom/images/pom-layers.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/pom-layers.html`](images/pom-layers.html)）。虚线是测试层
> 唯一允许做的事——调用 Page/Flow 的公开方法。

## When to Use

适合套用这套结构的场景：

- 同一 App 的多条回归用例（定位器写一次，处处复用）；
- 跨多屏的业务链路（需要 Flow 层编排）；
- 定位器频繁变动的迭代期（改一处 Page，全部用例受益）。

不适合直接照搬的场景：

- 一次性验证脚本（封装备而不用，直接写更快）；
- 探针类实验（前十个实验的风格就是故意的：先看清行为再抽象）；
- 页面结构每天在变的需求早期（Page 跟着改两遍，不如晚点抽）。

## Quick Start

前置条件：完成 03/04/05/06，Appium Server、iPhone 17 模拟器和 My
Demo App 已就绪。`pom.sh apply` 复用 01 环境脚本。

```bash
cd appium/12_pom
./pom.sh all          # apply → observe → clean
./pom.sh observe      # mvn -q test，跑全部 6 条核心用例
mvn -q test           # 或者直接用 Maven
```

observe 的真实输出（2026-10-23 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] POM 核心 6 条用例
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
✅ 建议登录成功：More 页 LogOut 可见
✅ 加购后角标=1
✅ POM 结算端到端：到达 CheckoutComplete-screen
✅ 目录 25 件商品，默认名称升序
✅ 名称降序全序一致：25 件
…（块为节选；还有"购物车有商品""删除后回到 No Items 空态"两条 ✅
与"▸ 步骤 N"结算日志；实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 6, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 159.9 s -- in TestSuite
```

诚实预期：6 条用例覆盖登录、目录排序、购物车、结算各一次，不追求
每条链路的全部分支（那些分支在对应实验里已经覆盖）。本实验的价值
在结构：同样的 6 条断言，测试类里一行定位器都没有。

## How It Works

**BasePage 收敛常用 Selenium 原语。** click、type、labelOf、exists、
isVisible 等，加上 presenceOf/visibilityOf/clickable 三种等待——
子类以这些方法为主，只有滚动加载、Webview 演示等少数场景直接用
driver。

其中 isVisible 用 `isDisplayed()`，与 presence（仅存在）严格区分：
这个 App 有大量元素存在但 `visible=false`（角标、空态文案），两种
检查语义不同。

**懒加载定位：By 描述而非元素引用。** 每个 Page 把定位器定义为
`static final By` 常量，用的时候才去查——元素引用会随页面刷新失效
（stale），By 描述不会。这是移动端 Web 表单之外又一个"存描述不存
引用"的场景。

**Screen 与 Component 的切分。** CatalogPage、LoginPage 是独立屏幕
（Screen）；ProductPage 同时管详情页和购物车（购物车的加减、角标
与详情页的加购是同一业务组件的两面）——切分依据是业务组件，不是
机械的一屏一类。

**结算链路由测试层依次调用 Flow 的五个方法。** `CheckoutPomTest`
依次调用 `PurchaseFlow` 的 `addItemToCart()`、`openCheckout()`、
`fillShipping()`、`fillPaymentAndReview()`、`placeOrder()`。

这串起加购 → 登录门（点结算后可能出现）→ 地址 → 支付 → 下单；
登录门保留 06 的条件分支（有建议列表就登录、登录态残留就直达）。
Flow 每步打"▸ 步骤 N"日志，失败现场直接可读。

**业务断言留在测试层的原因。** Page 的 `badgeText()` 返回数值、
`cartIsEmpty()` 返回状态，断言写在测试里——断言是对需求的判断，
Page 只提供事实。

把断言藏进 Page，失败时定位到的就是 Page 类，测试报告反而更难读。

## Pitfalls & Q&A

**坑：同名的按钮和 StaticText。** "Remove Item" 同时是按钮和静态
文本，`findElements` 会拿到两个，点文本会 stale。

解法是谓词加 `type == 'XCUIElementTypeButton'`，删完等按钮消失
再继续。

**坑：切 tab 后立刻读源码。** 购物车页要等 "My Cart" 标题可见再读，
否则读到的是上一个页面的残留树。Page 方法里的等待就是为这个服务的。

**Q：为什么断言不放进 Page？**
断言是需求，Page 是机制。放进 Page 后，一个断言失败要在 Page 类里
排查，报告也只显示 Page 方法名；留在测试层，失败直接对应一条业务
规则。

**Q：新增一个页面要改哪些地方？**
一个 Page 类 + （可选）一个 Flow 方法。测试类按需注入——这就是
"新增一个页面只需新增一个类"的验收含义，不需要碰任何已有类。

**Q：懒加载定位和 PageFactory 有什么区别？**
PageFactory 用 `@iOSFindBy` 注解 + initElements 预先建元素代理；
本篇的 `static final By` 是纯描述，每次操作现查。

后者没有 stale 代理对象的坑，也不依赖 PageFactory 的初始化时机，
对新手更可调试。

**Q：Flow 和 Page 的方法怎么分界？**
单屏内的动作序列（如"填地址 5 个字段"）放 Page；跨屏的顺序（如
"加购后必须先过登录门再填地址"）放 Flow。判断标准：换掉 App 的
某个屏，Flow 要不要跟着改——要改的就是流程，不是页面。
