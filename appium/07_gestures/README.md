# 07 · 手势与滚动：W3C Actions、画布签名与像素级断言

> 原生 App 的手势（画线、长按、滑动）在页面源码里不留痕迹——画完之后
> 源码一个字都不变。读完本篇你能用 W3C Actions 按相对坐标驱动四种手势，
> 并用截图像素差给"看不见"的画布结果写断言。

## Background

前面六个实验的断言都读页面源码：元素在不在、文本是什么、金额对不对。
手势类操作打破了这套方法——在画布上画一条线，页面源码不会多出一个
"线条"元素；长按留下的墨点、滑动后的列表位置，源码全都不知道。

手势测试要回答"动作真的生效了吗"，就得换证据来源：截图像素。画布
有墨迹 = 画布区域的像素和基准帧（动手画之前截的那张底图）不同；
Clear 生效 = 像素差回落到零。
这是手势测试区别于功能测试的根本差异。

另一个差异是坐标。手势作用在"点"上而不是"元素"上，写死像素坐标
换一台设备就全错。本篇所有坐标都从元素 rect（元素在屏幕上的边界矩形：左上角 x/y 坐标
加宽和高）按百分比推导，设备无关。

## What

`appium/07_gestures` 用 W3C Actions（WebDriver 标准的多步手势指令，
通过 PointerInput/Sequence 组合）驱动 4 种手势，TestNG 4 条用例各带
一条断言。

| 手势 | 动作 | 断言 |
|:---|:---|:---|
| 画折线 | 4 个相对坐标点连成笔迹 | 画布区域像素差 > 500 |
| 长按 | 按住画布中心 1.2 秒 | 按出墨点（像素差 > 10）；Clear 后回落近零 |
| swipe | 从屏幕 72% 高度滑到 22% | 最后一件商品进入可见区 |
| Reset | 点 More 菜单的 Reset App State | 确认框出现；重置后购物车空态 |

![手势测试：画布签名、长按、swipe 与重置的验证路径](images/gesture-flow.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/07_gestures/images/gesture-flow.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/gesture-flow.html`](images/gesture-flow.html)）。画布分支的
> 断言证据是像素差，菜单分支的断言证据是确认框与空态。

## When to Use

适合套用这套结构的场景：

- 画板、签名、涂鸦等"操作结果只在像素里"的界面；
- 滑动、拖拽、长按等手势回归，尤其是列表到底、排序拖拽这类边界；
- 涉及系统弹窗的流程（权限请求），需要预授权或显式处理。

不适合直接照搬的场景：

- 有独立元素可断言的功能操作（优先断言元素，别退回像素）；
- 需要验证笔迹内容/形状的识别类产品（本篇只证明"画上了"）；
- 多指手势（本篇全部单指，多指的 PointerInput 组合另行展开）。

## Quick Start

前置条件：完成 01，Appium Server、iPhone 17 模拟器和 My Demo App
已就绪。`gesture.sh apply` 会在复用 01 环境之后预授权照片权限
（Save 首次触发系统权限弹窗，弹窗会吞掉后续所有点击）。

```bash
cd appium/07_gestures
./gesture.sh all          # apply（含预授权） → observe → clean
./gesture.sh observe      # 只跑 GestureTest
mvn -q -Dtest=GestureTest test   # 或者直接用 Maven
```

observe 的真实输出（2026-10-23 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] 手势与滚动（4 条用例）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
✅ 画布墨迹像素变化：11400
✅ Save 已点击（该 App 无保存成功反馈，实测无 alert）
✅ 长按墨点像素变化：38
✅ Clear 后残留差异像素：0
✅ 确认框出现：Are you sure you want to reset the app state
✅ 重置后购物车回到 No Items 空态
✅ swipe 到达目录最后一件商品
…（块为节选；实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 4, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 41.99 s -- in dev.handson.appium.GestureTest
```

诚实预期：规划里的"长按 App Header 触发 Reset App State"在这个版本
实测不存在——长按页头、长按商品都无任何反应（长按商品还会退化成普通
点击、直接打开详情页）。Reset 的真实入口是 More 页的
ResetAppState-menu-item。长按手势改在画布上演示（按住出墨点）。

## How It Works

**W3C Actions 的三段式：移动、按下、抬起。** 每个手势都是一条
Sequence：`createPointerMove` 定位起点、`createPointerDown` 落指、
若干带时长的 move 画轨迹、`createPointerUp` 抬指。

起点用 `Origin.viewport()` 绝对坐标，数值从元素 rect 按百分比算出。
长按的区别只是按下和抬起之间插一个 `Pause(1.2s)`。

**像素差断言三步走。** ① 基准帧：画之前截一张图；② 动作帧：画之后
再截一张；③ `diffPixels()` 不缩放截图，而是把画布矩形的坐标按"截图像素数 /
屏幕点数"的比例换算到截图坐标系（模拟器截图是 2x 视网膜，比例即 2）。

只统计画布矩形内 RGB 差值超过阈值的像素。
画折线约 1.1 万像素变化，长按墨点只有 38 个——阈值按手势分别设定。

**Save 没有可断言的反馈。** 点击 SaveButton 后源码零变化、无 alert
（实测），能断言的只有"点击后没有错误弹窗"。这是被测应用的缺陷级
体验，测试如实记录而不是硬造断言。

**滑动用"找不到就再滑一次"的循环。** swipe 一次滑半屏（手指从屏幕 72% 高度拖到 22%），
每滑完检查目标商品是否可定位，最多 15 次。判断依据是元素可定位（列表渲染到
哪，元素就出现在哪），不需要读滚动位置。

**Reset 后的重启绕开粘滞状态。** 点 RESET APP 确认后，App 停在 More
页且 tab 栏 visible=false（实测粘滞）。测试用 `mobile: terminateApp`
+ `mobile: launchApp` 干净重启，再切到购物车断言空态——绕开比修复快。

## Pitfalls & Q&A

**坑：系统权限弹窗吞掉一切。** Save 首次触发照片权限弹窗，它是系统级
的：不在应用源码里、点不到下面的元素、跨 `clearApp` 和应用重启一直挂着。

解法是 `./gesture.sh apply` 里预授权（`simctl privacy grant photos`）；
已挂起的弹窗用 `mobile: alert` 的 accept 动作关闭。

**坑：DrawingBackground 的 visible 标志不可靠。** 打开 Drawing 后画布
元素在源码里但 `visible=false`，等可见性会超时。等 presence 即可，
坐标交互不受影响。

**坑：长按退化为点击。** 长按一个可点击的元素（商品、页头），按下
1.5 秒再抬起会被当作一次普通点击处理（商品被打开、进详情页）。长按
必须作用在无点击语义的区域——本篇选画布。

**Q：像素差阈值怎么定？**
先跑一次拿到实测值再定：画折线实测 1.1 万+，长按墨点实测 38，Clear
复原实测 0。阈值取"实测值的零头"（墨迹 >500、墨点 >10、复原 <墨迹/10），
既容住截图噪声，又不会放过失效。

**Q：为什么坐标用元素的百分比而不是屏幕百分比？**
画布不是全屏的（x=16, y=201, w=361, h=402），屏幕百分比会画到画布外。
从 `getRect()` 推导的画布内百分比，换设备、换机型都不变。

**Q：swipe 和 mobile: scroll 怎么选？**
`mobile: scroll` 是 Appium 封装的高级命令，一行一个滚动；W3C swipe
自己控制起点、终点、时长，能控制滑动距离和速度。

本篇为练 W3C 用 swipe；日常列表滚动用 `mobile: scroll` 更省事
（见 04 实验）。
