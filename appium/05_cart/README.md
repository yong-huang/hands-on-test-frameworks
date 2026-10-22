# 05 · 商品详情、加购与购物车：角标、数量与总价同步

> 加购是把浏览变成钱的那一步：详情页调数量、角标悄悄变化、购物车里
> 总价跟着走。读完本篇你能断言角标与总件数的关系，用 BigDecimal 校验
> 总价同步，并在删除商品后验证空态——包括角标统计的是"总件数"这个
> 反直觉行为。

## Background

电商 App 里，购物车是出错代价最高的一块：数量算错、总价对不上，直接
变成客诉和资损。所以加购链路的回归要盯三件事——角标数字、购物车里的
数量、总价金额，三者必须随时一致。

这条链路还有两个移动端特有的麻烦。一是状态藏在看不见的地方：tab 栏的
购物车角标（图标上的数字徽章）在页面源码里 `visible=false`，普通断言
"元素可见"会直接失败。二是金额格式不统一：详情页单价是 `$ 29.99`（带
空格），购物车总价是 `$29.99`(无空格)，字符串比较永远不相等。

本实验把这三个数字串成一条断言链：加购后角标变化、购物车里加减数量、
总价实时同步、删除后回到空态。金额用 BigDecimal（Java 的高精度十进制
类型，金额计算不用 double）清洗比较。

## What

`appium/05_cart` 用 Page Object（页面对象，本篇是 `CartPage`）+
TestNG 组织 3 条用例，覆盖加购、数量加减与删除。被测商品是目录第一件
Sauce Labs Backpack - Black，单价 $29.99。

| 用例 | 动作 | 断言 |
|:---|:---|:---|
| 加购 2 件 | 详情页数量文本 Amount 调到 2 后加购一次 | 角标=2；总价 = $29.99 × 2 |
| 购物车加减 | 行内 +1 / -1 | 总价与 "N Items" 随数量同步 |
| 删除商品 | 点 Remove Item | 回到 No Items 空态 |

![加购链路：详情页、角标状态与购物车校验](images/cart-flow.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/05_cart/images/cart-flow.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/cart-flow.html`](images/cart-flow.html)）。主路径从详情页
> 一路到空态；角标节点单独标出它统计的是总件数。

## When to Use

适合套用这套结构的场景：

- 加购、数量、删除这类"改状态再验证状态"的回归链路；
- 断言对象是徽章、角标等视觉上存在、源码里 `visible=false` 的元素；
- 总价、小计等金额计算需要跨页面取数比对。

不适合直接照搬的场景：

- 结算（地址、支付、下单）——那是下一条更长的链路，页面结构和等待
  方式都不一样；
- 多商品并存的购物车（本篇只放一件商品，多行时需要行级定位与遍历）；
- 需要验证优惠、运费、税费的价格引擎（本 App 没有这些概念）。

## Quick Start

前置条件：完成 01-04，Appium Server、iPhone 17 模拟器和 My Demo App
已就绪。`cart.sh` 复用 `../01_ios_session` 的 `apply` / `clean`。

```bash
cd appium/05_cart
./cart.sh all            # apply → observe → clean
./cart.sh observe        # 只跑 CartTest
mvn -q -Dtest=CartTest test   # 或者直接用 Maven
```

observe 的真实输出（2026-10-22 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] 商品详情、加购与购物车（3 条用例）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
✅ 加购 2 件：角标=2，单价 $29.99
✅ 购物车总价同步：$59.98 = $29.99 × 2（2 Items）
✅ 购物车 +1：2 Items，总价 $59.98
✅ 购物车 -1：1 Items，总价 $29.99
✅ 删除前：1 Items，总价 $29.99
✅ 删除后回到 No Items 空态
…（块为节选；实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 19.79 s -- in dev.handson.appium.CartTest
```

诚实预期：角标统计的是**总件数**，不是商品行数。先加 1 件、把数量调
到 2 再加购一次，角标是 3 不是 2——想得到"角标=2"，要么一次加 2 件，
要么加两次各 1 件。套件里每个用例前都会 `clearApp` 复位购物车，用例
之间互不带货。

## How It Works

**角标是看不见的数字文本。** 加购后 tab 栏出现数字徽章，但它的页面
节点是 `visible=false` 的 StaticText，`name` 就是数字本身。所以断言用
presence（存在于源码）而不是 isDisplayed。

定位时用 `name MATCHES '[0-9]+'` 并排除名为 `Amount` 的详情页数量
文本，避免混到别的数字。

**两种金额格式，一个清洗函数。** 详情页单价 label 是 `$ 29.99`，购物车
总价是 `$29.99`，差一个空格。`parseAmount()` 用正则 `[^0-9.]` 删掉所有
非数字字符再进 BigDecimal，两种格式都归一化。

比较用 `assertEquals`：清洗后两侧都是两位小数，值与位数一致才判等。

**数量加减的等待锚点是 "N Items"。** 行内的数字文本和角标同名（都是
纯数字），直接等它更新会命中旧元素。购物车底部的 `"2 Items"` 文案全局
唯一，`tapAddPlusInCart()` 在点击**前**记住当前件数，点击后等
"`N+1 Items`" 出现，确保同步完成再读总价。

**总价断言的期望值由单价推导。** 断言写的是
`unitPrice.multiply(BigDecimal.valueOf(2))`，而不是硬编码 `$59.98`——
单价变了测试不必跟着改，只有乘法真的算错时测试才会红。

**删除的空态断言用可见性反转。** `No Items` 文案常驻页面源码，有商品
时 `visible=false`，删除后变 `visible=true`。所以空态断言是
`isDisplayed()` 为真，而不是元素存在——存在性在任何时候都成立，没有
区分度。

## Pitfalls & Q&A

**坑：角标断言用 isDisplayed 直接失败。** 它在源码里就是
`visible=false`，这不是 bug 而是该 App 对徽章的实现方式。解法是断言
presence 加文本，别断言可见。

**坑：先加 1 件再调数量加购，角标是 3。** 角标统计总件数（1+2=3），
不是"第几次加购"。想要角标=2，调完数量后只加购一次。

**坑：数量 +1 后马上读总价，读到旧值。** App 更新总价是异步的，点击
后立刻读会拿到上一次的 `$29.99`。解法是先等 `"N+1 Items"` 出现，总价
才稳定。

**Q：为什么不用坐标点 + / - 按钮？**
数量控件的图标没有独立文案（`AddPlus Icons`），但 name 稳定，predicate
按 name 定位足够可靠。写死坐标在换机型或横竖屏后全部失效。

**Q：数量减到 1 再减会怎样？**
实测没有继续往下按——多数购物车此时要么禁用要么直接删行，行为不同
断言就不同。本篇只覆盖 +1/-1 的安全区间，把"减到 0"留给结算链路前
的边界用例。

**Q：金额为什么必须 BigDecimal？**
double 的二进制浮点算 $0.1 都会有精度尾巴，金额断言会出现
`59.980000000000004 != 59.98`。BigDecimal 按十进制计算。

测试用 `assertEquals` 比较：清洗后两侧都是两位小数，值和位数（scale）
都一致才判等；若小数位数可能不同，要改用 `compareTo` 只比数值。
