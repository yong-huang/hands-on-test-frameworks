# 09 · 生物识别与系统弹窗：Face ID 模拟登录

> Face ID 登录的测试难点在于"脸"——真机靠用户的脸，自动化靠模拟器
> 的匹配接口。读完本篇你能在 iOS Simulator 上登记生物特征、分别模拟
> 匹配成功与失败两种系统弹窗结果，并验证失败不会阻塞下一次尝试。

## Background

生物识别登录把"证明你是你"从密码换成了脸和指纹。对测试来说，真机上
这条链路几乎不可自动化（每次都要真人配合），但 iOS Simulator 提供
了一组模拟接口：登记、匹配成功、匹配失败，全部可以用命令触发。

这组接口有一个容易忽略的边界：系统的人脸提示（屏幕下方弹出的人脸识别框）
是系统级覆盖层，不在应用的页面源码里——读源码永远看不到它，点击
也点不到它。它的结果只能用 Appium 的 `sendBiometricMatch` 命令来
"回答"，这正是本实验的核心动作。

本实验在 My Demo App 上走完整链路：打开 Face ID 登录开关、登记
生物特征、分别以匹配成功和失败各走一遍登录，并验证失败后紧接的
成功尝试不受阻塞。

## What

`appium/09_biometrics` 用 TestNG 3 条用例驱动同一条链路的三种结果。
前置操作：Biometrics 页打开 "Allow login with Face ID" 开关后，
Login 页出现 FaceId Icons 按钮。

| 用例 | 动作 | 断言 |
|:---|:---|:---|
| 匹配成功 | enroll → 点按钮 → match=true | 进入结算地址页（该 App 登录后落点） |
| 匹配失败 | enroll → 点按钮 → match=false | 停留登录页，应用不崩 |
| 失败后重试 | match=false 紧接 match=true | 两次弹窗逐次应答，最终登录成功 |

![Face ID 模拟登录：开关、登记、匹配与重试](images/biometric-flow.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/appium/09_biometrics/images/biometric-flow.html)
> （在线链接需仓库推送并部署 Pages 后可用；或本地打开
> [`images/biometric-flow.html`](images/biometric-flow.html)）。匹配
> 节点分成功与失败两条分支，失败分支再汇入重试路径。

## When to Use

适合套用这套结构的场景：

- 登录、支付确认等依赖 LocalAuthentication（iOS 的生物识别框架，
  应用侧调用它弹系统提示）的流程；
- 需要覆盖"识别成功 / 识别失败"两种分支的安全类回归；
- 在 Simulator 上跑的日常套件（真机请换真实 Face ID，人工配合）。

不适合直接照搬的场景：

- 真机执行（`enrollBiometric` / `sendBiometricMatch` 仅 Simulator
  有效）；
- 权限类系统弹窗（定位、通知、相册）——本机未装 applesimutils
  （权限模拟的可选工具），这类弹窗用 `autoAcceptAlerts` 能力自动
  允许，精细控制留给装了该工具的环境；
- 需要验证生物识别底层数据安全的场景（超出 UI 自动化边界）。

## Quick Start

前置条件：完成 01 与 03，Appium Server、iPhone 17 模拟器和 My Demo
App 已就绪。`biometrics.sh apply` 复用 01 环境脚本。

```bash
cd appium/09_biometrics
./biometrics.sh all          # apply → observe → clean
./biometrics.sh observe      # 只跑 BiometricLoginTest
mvn -q -Dtest=BiometricLoginTest test   # 或者直接用 Maven
```

observe 的真实输出（2026-10-23 实测；TestNG 方法顺序可能不同）：

```text
=====> [observe] 生物识别登录（3 条用例，仅 iOS Simulator 有效）
连接 Appium: http://127.0.0.1:4723/wd/hub
设备: iPhone 17 / iOS 26.5
…（Session ID 每次运行不同，此处省略）
✅ Face ID 登录已开启，Login 页出现 FaceId Icons 按钮
✅ 模拟器已登记生物特征（enrollBiometric）
✅ sendBiometricMatch：match=true
✅ Face ID 匹配成功：已登录并进入结算地址页
✅ sendBiometricMatch：match=false
✅ 第一次尝试：match=false，停留登录页
✅ 第二次尝试：match=true，登录成功——弹窗无残留阻塞
…（块为节选；实际输出末尾还有 Session 已关闭 一行）
```

Surefire 汇总（Surefire 是 Maven 的测试执行插件，报告写入
`target/surefire-reports`）：

```text
Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 34.71 s -- in dev.handson.appium.BiometricLoginTest
```

诚实预期：Face ID 提示弹出后应用页面"卡住"是正常现象——提示是系统
覆盖层，应用在等系统回调，此时读源码、点元素都可能超时，必须先用
`sendBiometricMatch` 应答。`match=false` 的断言是"停留登录页"，
不是"报错"——该 App 的失败分支没有错误文案。

## How It Works

**开关是图标按钮，状态断言看功能不看图标。** Biometrics 页的开关是
`SwitchUnselected Icons` 按钮，拨动后图标名实测不变（不是 Switch
类型控件）。开关是否生效，用功能信号断言：Login 页出现
`FaceId Icons` 按钮即开关已开。

**两个模拟命令各管一段。** `enrollBiometric(enroll=true)` 相当于
在模拟器"录入了一张脸"，做一次即可（重复执行无害）；
`sendBiometricMatch(type=faceId, match=...)` 在系统提示弹出后
应答它——match 决定应用收到成功还是失败回调。

**失败的断言是"没变化"。** 该 App 的匹配失败分支没有错误提示，
`match=false` 后唯一可观察的结果是留在登录页。断言登录表单的
用户名建议列表仍可见、FaceId 按钮仍存在（应用未崩溃），就足够
锁定这个行为。

**autoAcceptAlerts 兜底权限弹窗。** BaseTest 里
`setAutoAcceptAlerts(true)` 让定位、通知等权限类系统弹窗自动允许，
避免它们阻塞用例。

Face ID 提示不归它管（要靠 sendBiometricMatch 给结果），两类弹窗的
应答方式不同。

## Pitfalls & Q&A

**坑：人脸提示弹出后应用像"死"了。** 它在等系统回调，此时读源码
可能超时。解法是提示弹出后立刻 `sendBiometricMatch` 应答，不要
在提示存在期间做其他操作。

**坑：开关拨了但图标名没变。** 拨动后元素名实测仍是
`SwitchUnselected Icons`，拿图标名断言开关状态会失败。解法是看
Login 页有没有出现 FaceId 按钮。

**坑：真机上这套命令无效。** `enrollBiometric` / `sendBiometricMatch`
只在 Simulator 生效；真机的 Face ID 必须真人配合，UI 自动化通常
跳过这条分支或改用密码登录。

**Q：失败后紧接第二次尝试，为什么要专门测？**
系统弹窗是有状态的覆盖层，应答失败（match=false）后如果应用或
WebDriverAgent 残留了等待状态，下一次点击可能无响应。

失败→成功的连续用例证明弹窗被逐次干净地应答，这正是"系统弹窗
不阻塞下一条用例"的验收点。

**Q：为什么每次用例前都 clearApp 还要重新开开关？**
`clearApp` 会清掉应用数据，Face ID 开关状态也在其中。每条用例的
第一步都是重新打开开关——这也是用例自包含的一部分，避免依赖
上一条的残留状态。

**Q：applesimutils 是什么，为什么这里没用到？**
它是模拟器的权限模拟工具（改定位、通知、相册等权限的白名单），
本机未安装；本实验的权限弹窗用 `autoAcceptAlerts` 已够用。若需要
"拒绝权限"之类的精细分支，先安装它再扩展用例。
