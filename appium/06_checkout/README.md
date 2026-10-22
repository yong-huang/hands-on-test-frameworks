# 06 · 结算全流程：地址、支付、Review 与下单

> 结算是链最长的一条路：登录门、两个预填却"不被认账"的表单、两种校验
> alert、还藏着一笔 Review 页才出现的运费。读完本篇你能把登录到下单的
> 8 步串成一条可重复的 E2E（End-to-End，端到端测试：整条链路连起来
> 从入口跑到最终结果），并学会用"每步日志 + 双条件等待"驯服长链路
> 的不确定性。

## Background

购物车里的数字只是"意向"，下单成功才闭环。结算把前面所有环节串到一起：
没登录要先登录，地址和支付要过校验，金额要复核，最后还要真的下一单。
这条链上任何一步"看起来对但实际没生效"，订单就会失败或金额出错。

长链路测试最大的敌人不是某个元素难定位，而是**不确定性**：这个 App 的
登录态有时保留有时清除、表单预填值有时被认账有时不被认账、校验 alert
有时弹有时不弹。每换一种排列，脚本就多一种死法。

本实验的解法是把不确定性变成分支：每一步都"看到什么就走哪条路"，并用
步骤日志把实际走的路径记下来——失败时日志就是现场证据。

## What

`appium/06_checkout` 的核心是 `flows/CheckoutFlow`——一个可复用的结算
编排器（把页面定位、动作、等待封装成 add → open → fill → review →
place 八个方法，后续项目直接调用）。`CheckoutE2ETest` 用它跑 3 条用例。

| 用例 | 路径 | 断言 |
|:---|:---|:---|
| 端到端下单 | 加购 → 登录 → 地址 → 支付 → Review → 下单 | 到达 CheckoutComplete-screen；Review 总价 = 购物车总价 + $5.99 运费 |
| 空姓名 | 地址表单留空 Full Name | 弹 "Please provide your full name." |
| 空卡号 | 支付表单留空 Card Number | 弹 "Value looks invalid." |

![结算全流程：登录门、两段表单、Review 运费与完成页](images/checkout-flow.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/06_checkout/images/checkout-flow.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/checkout-flow.html`](images/checkout-flow.html)）。红色分支是
> 两条负向校验（故意给坏数据、预期被拦截）路径；登录门画成菱形，因为
> 登录态是否残留决定走哪条路。

## When to Use

适合套用这套结构的场景：

- 多页面串联的端到端链路（下单、注册、审批流），每步都可能被拦截；
- 表单"预填值但需要真实编辑"的界面——先清空重填再提交；
- 需要在成功路径之外覆盖负向校验（留空、格式错）的表单。

不适合直接照搬的场景：

- 短链路（单页表单）——一个页面对象加两条用例就够，编排器是过度设计；
- 支付成功后的第三方页（钱包、银行 OTP——One-Time Password，一次性
  验证码）——本 App 没有这一步；
- 需要验证库存、优惠券等订单引擎逻辑（本 App 没有这些概念）。

## Quick Start

前置条件：完成 01-05，Appium Server、iPhone 17 模拟器和 My Demo App
已就绪。`checkout.sh` 复用 `../01_ios_session` 的 `apply` / `clean`。

```bash
cd appium/06_checkout
./checkout.sh all          # apply → observe → clean
./checkout.sh observe      # 只跑 CheckoutE2ETest
mvn -q -Dtest=CheckoutE2ETest test   # 或者直接用 Maven
```

observe 的真实输出（2026-10-22 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] 结算全链路（3 条用例）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
▸ 步骤 2：进入购物车页，总价 $29.99
▸ 步骤 3：登录门出现：点用户名建议自动填充后 Login
▸ 步骤 7：进入 Review Order 页
✅ Review 总价一致：$35.98 = $29.99 + $5.99 运费
▸ 步骤 8：下单成功，出现 CheckoutComplete-screen
✅ 端到端下单完成
✅ 空卡号被拦截：Value looks invalid.
✅ 空姓名被拦截：Please provide your full name.
…（块为节选；"▸ 步骤 N" 是 CheckoutFlow 每步打印的日志，三个用例连续编号）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 77.89 s -- in dev.handson.appium.CheckoutE2ETest
```

诚实预期：两条负向 alert 的文案不一样——空姓名弹
"Please provide your full name."（地址步的校验），空卡号弹
"Value looks invalid."（校验的是支付表单数据，alert 在点 Review
Order 时才弹出）。规划时以为两句相同、时机相同，实测都不是。

另外登录门这次运行出现了三次、上次运行一次都没出现，这个不确定由
条件门（一种轮询探测、见哪个信号就走哪条分支的等待逻辑，机制见下文
How It Works 首段）消化。

## How It Works

**条件门消化登录态的不确定性。** 点 Proceed 后每 0.5 秒探测一次：出现
用户名建议列表就走"建议自动填充 + Login"，直接出现地址表单就说明登录
态残留、跳过登录。两种情况最后都等 "Enter a shipping address" 出现，
后续步骤不感知差别。

**预填值必须清空重填。** 地址表单预填了 Rebecca Winter，但不点开重新
输入就直接点 To Payment，App 弹 "Please provide your full name."——
预填只是显示，表单模型是空的。

`typeIntoField()` 对每个字段执行点击 → clear → sendKeys → 发 Tab 键
（`mobile: keys` 带 `keys: [\uE004]`）收起键盘，5 个必填字段逐个来。

**双条件等待代替单点等待。** 被拦截时目标页面永远不会出现，单等
"支付页出现"会空转 30 秒。`toPayment()` 和 `reviewOrder()` 同时等两个
信号——alert 的 OK 按钮或下一屏的标题——先到者赢，并返回是否被拦。

**Review 总价多了一笔运费。** 实测 Review 页总价 $35.98 = 购物车
$29.99 + 运费 $5.99（常量 `DELIVERY_FEE`），断言写的是这个加法。购物车
总价在离开购物车页之前读取，由 `openCheckout()` 带出来。

**每步日志是长链路的黑匣子。** 可以把每步日志理解成长链路的黑匣子
（类比飞机的飞行记录仪）；和飞机黑匣子不同的是，它不用等事故后回收
解读——失败时最后几行当场就能读。

`CheckoutFlow` 每个动作打一行"▸ 步骤 N"，三个用例连续编号。现场信息
包括：停在哪一步、走的是登录门还是直达、总价读到了多少。

## Pitfalls & Q&A

**坑：登录态跨 clearApp 残留。** 今天这次运行登录门弹了三次，上一次
一次没弹——App 会话存活比 `clearApp` 的清理更顽固。条件门让两种状态
都能走通，不要写死"一定有登录页"。

**坑：表单预填值是摆设。** 地址、支付两段表单都预填了演示数据，但
不重新输入直接提交就报校验。别被 `value` 属性骗了，模型里是空的。

**坑：两种校验文案、两个弹出时机。** 地址步（点 To Payment 时）报
"Please provide your full name."；支付表单的卡号问题要等点 Review
Order 时才报 "Value looks invalid."——按"点哪个按钮后弹的"区分断言，
别写成一个常量。

**Q：为什么把逻辑放在 flows 而不是页面对象里？**
结算的页面在流程里是一次性的（过了就不再回来），拆成多个 Page Object
反而要跨类传状态。`CheckoutFlow` 一层同时管定位与步骤顺序，后续项目
（如回归套件）只要调它的方法就能复用整条链路。

**Q：billing 勾选框为什么没动？**
它是图标按钮（`CheckBoxUnselected Icons`），默认未勾选也能直接走完——
说明演示 App 没有强制"账单地址不同"的分支。勾选后的表单行为未验证，
留给需要它的项目再探。

**Q：负向用例为什么只测姓名和卡号各一个？**
校验按"第一个无效字段"报错，留空一个字段得到的文案是确定的；同时留空
多个字段时断言的文案取决于字段的校验顺序，不稳定。一个字段一个用例，
失败时原因唯一。
