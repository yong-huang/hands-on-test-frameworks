# 10 · 应用生命周期与状态恢复：后台、terminate 与 Reset

> 移动用户随时会切走应用：回个消息、锁个屏、杀个进程。读完本篇你能用
> 四个生命周期命令驱动应用的"前台 / 后台 / 未运行"迁移，用 queryAppState
> 断言状态值，并按实测行为验证状态恢复——包括"购物车不保留、登录态
> 保留"这种不对称。

## Background

Web 测试没有"生命周期"概念：浏览器一直在前台，页面关闭即一切结束。
移动端不同——用户按一下 Home 键应用就进了后台，划掉卡片应用就死了，
测试必须回答两个问题：切走再回来，页面还在吗？杀掉再打开，数据还在吗？

这两个问题的答案不取决于测试，而取决于应用把状态存在哪：内存里的
数据（如购物车）随进程死亡消失，持久化的数据（如登录凭据）跨进程
保留。

测试的职责是把每种数据的实际行为断言出来，而不是假设它们
"应该"被保留。

本实验用 Appium 的四个生命周期命令（background、activate、terminate、
queryAppState）驱动 My Demo App 的状态迁移，并验证 Reset App State
菜单的清理效果。

深链接（deep link，用 `myapp://product/1` 这类 URL 直接打开应用内
指定页面）不在验收内：该 App 未注册自定义 URL scheme（应用在系统里
登记的私有 URL 前缀，系统据此把这类 URL 路由给应用），`simctl
openurl` 只会打开 Safari 而非本应用。

## What

`appium/10_lifecycle` 用 TestNG 4 条用例覆盖生命周期的迁移与恢复。
实测该 App 的行为：后台 5 秒再激活停留原页面；terminate 后重启，
购物车清空（未持久化）但登录态保留。

| 用例 | 动作 | 断言 |
|:---|:---|:---|
| 后台与激活 | backgroundApp 5 秒 → activateApp | queryAppState 3→4；停留详情页 |
| 状态值追踪 | terminate → activate | queryAppState 4→1→4 |
| 重启恢复 | 加购 + 登录 → terminate → 重启 | 购物车清空；登录态保留 |
| Reset 清理 | More 菜单 Reset App State | 购物车回 No Items 空态 |

![应用生命周期：状态迁移与 queryAppState](images/app-lifecycle.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/10_lifecycle/images/app-lifecycle.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/app-lifecycle.html`](images/app-lifecycle.html)）。三个节点
> 标注 queryAppState 的实测状态值，箭头标注触发迁移的命令。

## When to Use

适合套用这套结构的场景：

- 切后台恢复类回归（来电、锁屏、切应用的模拟）；
- 杀进程重启后的状态持久化验证（登录态、缓存、草稿）；
- Reset / 清理菜单的回归（确认框 + 数据清空 + 界面回位）。

不适合直接照搬的场景：

- 纯页面内操作（生命周期命令帮不上忙）；
- 需要验证系统级推送、小组件等进程外能力（超出 Appium 边界）；
- 真机上的后台行为（后台时长受系统调度影响，模拟器更可控）。

和同类手段怎么选：`clearApp`（前几篇用过的清数据命令）只重置数据，
不产生前后台/杀进程迁移，验证不了"切走再回来"；Reset App State 是
被测应用自带的清理入口，只有应用提供该菜单时才可用。

真实的前后台与杀进程迁移只能用本篇四个命令；系统推送、小组件等
进程外能力需换 XCUITest 等原生框架。

## Quick Start

前置条件：完成 01、03、05，Appium Server、iPhone 17 模拟器和 My Demo
App 已就绪。`lifecycle.sh apply` 复用 01 环境脚本。

```bash
cd appium/10_lifecycle
./lifecycle.sh all          # apply → observe → clean
./lifecycle.sh observe      # 只跑 LifecycleTest
mvn -q -Dtest=LifecycleTest test   # 或者直接用 Maven
```

observe 的真实输出（2026-10-23 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] 应用生命周期与状态恢复（4 条用例）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
✅ 后台 5 秒再激活：queryAppState 3→4，停留详情页
✅ queryAppState 全程 4 → 1 → 4
✅ Reset App State 后购物车回到 No Items 空态
✅ terminate 后购物车清空（该 App 未持久化购物车）
✅ 登录态保留：More 页 LogOut 可见
…（块为节选；实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 4, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 57.38 s -- in dev.handson.appium.LifecycleTest
```

诚实预期：购物车不保留、登录态保留是**实测行为**，不是设计期望——
如果未来版本把购物车改成了持久化存储，"购物车清空"断言会变红，
那时该更新的是断言（跟着新行为走），不是回滚应用。深链接仅演示：
`xcrun simctl openurl <UDID> <url>` 打开的是 Safari，与本 App 无关。

## How It Works

**四个命令各管一段迁移。** `backgroundApp` 把应用切到后台并保持
（不带 duration 参数——实测带 duration 会在后台指定秒数后自动回
前台）；`activateApp` 拉回前台；`terminateApp` 杀进程；`launchApp`
重新启动。

`queryAppState` 随时读状态：前台 4、后台 3、终止后 1。

**像素级等待换成状态值等待。** 后台期间页面树不可用（应用没在渲染
UI），此时唯一可靠的断言是 `queryAppState` 的数值——等它变成 3 再
激活，比裸 sleep 更能证明"确实进了后台"。

**状态恢复按实测行为写断言。** 加购一件再 terminate 重启，购物车
空了（该 App 没把购物车写进持久化存储），登录态却在（凭据在 Keychain——iOS 的系统级加密存储，不随进程死亡
丢失）。断言忠实记录这两个事实，并在消息里注明"实测行为"，
避免读者误以为这是缺陷。

**Reset 的确认框与粘滞状态。** Reset App State 走 More 菜单，点
RESET APP 后应用停在 More 页且 tab 栏不可见（07 同款粘滞状态），
测试用 `terminateApp` + `launchApp` 重启绕开，再验证购物车空态。

## Pitfalls & Q&A

**坑：backgroundApp 带 duration 会自动回前台。** 实测
`{"appId": ..., "duration": 5}` 是"后台 5 秒后自动激活"——命令返回时
应用已经回前台，queryAppState 读到 4。解法是不带 duration，由测试
自己 sleep 控制后台时长。

**坑：queryAppState 的返回值是数字。** 4=前台、3=后台、1=未运行
（0=未安装）。Java 客户端返回 Object，要转成 Number 再比较。

**坑：RESET APP 后直接断言会超时。** 确认后应用停在 More 页且 tab
栏不可见（07 同款粘滞状态）。解法是重启应用再验证，别在粘滞状态里
硬等。

**Q：为什么登录态保留而购物车不保留？**
两者存储位置不同：登录凭据通常在 Keychain 或 UserDefaults（iOS 的
键值对持久化存储，两者都不随进程死亡丢失），购物车实测只在内存或
非持久存储（进程死亡即消失）。

这是实测行为，不是本实验能改变的；重要的是把它断言出来，防止
未来版本悄悄改变持久化策略。

**Q：深链接为什么不测？**
该 App 未注册自定义 URL scheme，`simctl openurl` 只会打开 Safari。
演示可以（命令照敲能看到 Safari 打开目标网址），断言没有对象——
不为"演示"写假断言。

**Q：后台期间为什么要用 queryAppState 而不是读源码？**
应用在后台不渲染 UI，页面源码不可用（读到的可能是最后一次快照）。
状态值是系统级事实，不受渲染影响。
