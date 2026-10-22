# 04 · 商品目录与四种排序：CollectionView 滚动累计与诚实断言

> 目录页有 25 件商品，屏幕一次只渲染 6 件；价格金额干脆不显示在列表里。
> 读完本篇你能用滚动累计拿到列表全序（完整顺序），对四种排序下断言，并
> 学会在被测应用排序本身有缺陷时，设计"缺陷存在也能稳定通过"的断言。

## Background

商品一多，用户找东西靠的是排序和滚动。目录只有一屏时，测试断言"页面
显示了商品"就够了；商品涨到 25 件，问题变成"整条列表的顺序对不对、
四种排序是不是真的在排"。这就要求测试能拿到**全量顺序**，而不只是首屏。

移动端列表和一个静态网页不同。iOS 的列表控件是 CollectionView
（逐行渲染的滚动视图），它只渲染屏幕内的 cell（行单元），滚出屏幕的行
会被回收复用。所以无论商品有多少，页面源码里永远只有约 6 个商品——
这是省内存的正确设计，却是自动化断言的直接障碍。

本实验要解决的就是这个矛盾：用驱动层（Appium Driver，代替人在设备上
点按的自动化代理，滚动命令由它下发）的滚动命令逐屏推进，把每次可见的
商品名累计起来，重建完整顺序；金额列表页拿不到，就进详情页读。
过程中还会撞见一个意外事实：这个 App 的价格排序本身是坏的。

## What

`appium/04_catalog` 用 Page Object（页面对象：把元素定位和操作封装成
一个类，本篇是 `CatalogPage`）+ TestNG 组织 3 条用例，覆盖目录列表
与四种排序。实测该 App 目录共 25 件商品。

| 用例 | 做什么 | 断言 |
|:---|:---|:---|
| 默认目录 | 滚动累计全部商品 | 总数 ≥ 20（实测 25）；全序 = 名称升序 |
| 名称降序 | 点排序菜单后滚动累计 | 全序 = 默认顺序的精确反转 |
| 价格升/降序 | 记下首尾名，进详情页读价 | 两方向同一批商品；极值价格跨方向一致 |

![目录与排序的验证流程：滚动累计、两条断言路径与排序态重置](images/catalog-sort.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/04_catalog/images/catalog-sort.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开 [`images/catalog-sort.html`](images/catalog-sort.html)）。
> 主路径是"滚动累计 → 名称排序断言"；价格分支会进详情页读金额，灰色
> 节点标出"离开列表排序态就重置"这个约束。

## When to Use

适合套用这套结构的场景：

- 验证长列表的完整顺序，而页面只渲染可见部分
  （iOS 的 CollectionView / Android 的 RecyclerView）；
- 排序、筛选等会改变全序的功能回归；
- 断言依据只在二级页面暴露（列表给入口，详情给数据）。

不适合直接照搬的场景：

- 列表一次全部渲染（直接读元素列表即可，不必滚动累计）；
- WebView 里的列表（WebView 是 App 内嵌的浏览器控件，定位要切到
  Web 上下文——Appium 把页面当网页来看的模式，滚动也不是 `mobile: scroll`）；
- 对排序算法做穷举验证（随机数据加本地排序比对更适合那种目标）。

同类滚动手段对比：

| 手段 | 差异 | 什么时候选它 |
|:---|:---|:---|
| `mobile: scroll` | 指定元素和方向，模拟系统级滚动 | 有稳定列表容器时首选（本篇用） |
| W3C swipe | 按坐标构造手势，完全可控 | 容器定位不稳或要控制滑动距离 |
| `mobile: scrollToElement` | 直接滚到指定元素 | 目标元素有唯一 locator 时 |

## Quick Start

前置条件：完成 01/02，Appium Server、iPhone 17 模拟器和 My Demo App
已就绪。`catalog.sh` 复用 `../01_ios_session` 的 `apply` / `clean`。

```bash
cd appium/04_catalog
./catalog.sh all            # apply → observe → clean
./catalog.sh observe        # 只跑 CatalogSortTest
mvn -q -Dtest=CatalogSortTest test   # 或者直接用 Maven
```

observe 的真实输出（2026-10-22 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] 目录与四种排序（3 条用例）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
✅ 商品总数：25（验收下限 20）
✅ 默认即名称升序：首=Sauce Labs Backpack - Black 尾=Test.allTheThings() T-Shirt - Yellow
⚠️ 价格升序：首=Sauce Labs Bolt T-Shirt - Black($15.99) 尾=Sauce Labs Bike Light($9.99)——尾件价格低于首件 不是本序列最小价，排序键疑似缺陷
✅ 价格升降镜像成立：asc 首/尾 = $15.99/$9.99，desc 首/尾 = $9.99/$15.99
✅ 名称降序全序一致：首=Test.allTheThings() T-Shirt - Yellow 尾=Sauce Labs Backpack - Black
…（块为节选；实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 368.2 s -- in dev.handson.appium.CatalogSortTest
```

诚实预期：价格升序把 $9.99 的 Bike Light 排在末位，这不是数值升序，
是被测应用的缺陷。用例因此只断言"缺陷存在也成立"的性质（两方向同一批
商品、极值价格跨方向一致），缺陷本身用 ⚠️ 打印，详见 Pitfalls & Q&A。

整条套件约 6 分钟，慢在价格用例要进出详情页 4 次。

## How It Works

**排序图标没有任何无障碍标注。** 目录页右上角的排序入口，名字就叫
`Button`（图标是 sort 样式，但没有 accessibility id——App 给控件预留的
无障碍标识，02 实验里它是最稳的定位方式）。定位用
predicate——iOS 的一种条件定位语法，形如 `label == 'x'`：

```java
AppiumBy.iOSNsPredicateString("type == 'XCUIElementTypeButton' AND name == 'Button'")
```

**排序菜单是四个静态文本。** 点开后的 `Sort by:` 菜单里，四个选项
（`Name - Ascending` 到 `Price - Descending`）都是
`XCUIElementTypeStaticText`，label 即文案。

点击后菜单自动关闭、列表立即重排。`sortBy()` 用"等 `Sort by:` 消失"
来确认菜单关闭。

**滚动累计重建全序。** `mobile: scroll` 指定列表容器和方向滚一屏，
每屏把可见商品名加进 `LinkedHashSet`——它保留下第一次出现的顺序，
正好是列表全序。连续 3 次滚动都没有新名字就判定到底，避免滚动回弹
（到底后画面不再变化）造成的误判。

**价格要进详情页读，而且先记名字。** 列表里 `Product Price` 的
name、label、value 全是这四个字，金额只出现在详情页的 `Price`
元素（形如 `$ 15.99`）。名称到价格是商品的固有属性、与排序无关，
所以流程是：排序后先滚动记下首尾商品名，再进详情页读价。

**离开列表，排序态就重置。** 实测点商品进详情、或切到别的 tab 再
回来，列表都会回到默认的名称升序。`openProduct()` 因此先 `scrollToTop()`
再滚动找目标——从详情页返回时列表可能停在任意位置，从顶部重新找才是
确定的起点。

**价格断言只保留缺陷打不破的性质。** "升序首件 ≤ 尾件"在这个 App 上
不成立（见 Quick Start 的 ⚠️），写成断言就是给缺陷背书。

套件断言的是：两个方向是同一批 25 件商品的两种排列；升序首尾与降序
首尾的**价格**跨方向相等。同价并列时商品名可以不同，价格必相等。

## Pitfalls & Q&A

**坑：排序图标定位不到。** 按 "sort" 搜元素一无所获，实际 name 是
`Button`——它没有 accessibility id（无障碍标识）可依赖。解法是用
predicate 组合控件类型和名字。

**坑：列表页读不到金额。** `Product Price` 不暴露数字，价格断言必须
进详情页。这也是为什么本篇的价格用例比名称用例慢。

**坑：详情页没有返回按钮。** 页面源码里没有任何 back 类按钮，返回
列表靠底部 tab 栏的 `Catalog-tab-item`。

**Q：为什么滚动到底要连续 3 次无新增才停？**
一次滚动无新增可能只是回弹或惯性没走完，不一定是到底。3 次阈值在
实测里稳定，代价是多花几秒。`accumulateAll()` 和 `openProduct()` 都
用这个约定。

**Q：Bike Light 为什么在价格升序里排最后？**
实测它 $9.99，却是升序的末位；$15.99 的 T-Shirt 反而是首位。排序
键不是数值，疑似实现把价格当字符串或别的字段处理。这是 App 的缺陷，
套件不把它写成断言，避免将来修复后测试变红。

**Q：价格全序为什么只断言到"同一批商品 + 极值一致"？**
金额在列表页不可见，全序断言需要 25 次进详情读价，一轮要十几分钟，
不值得。首尾价格是排序错误最敏感的位置，配合两方向互验已经覆盖了
回归风险的大头。

**Q：为什么用 `LinkedHashSet` 而不是 `List` 去重？**
cell 复用让同一商品可能出现在相邻两屏，要去重；同时它保留首次插入
顺序，累计结果直接就是列表全序，不需要再排序还原。
