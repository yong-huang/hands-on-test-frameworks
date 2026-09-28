# 04 · mock 与测试替身：把外部世界请出你的测试

> 单测跑到一半真发了一封邮件？测试的第一原则是不碰真实外部依赖——SMTP、时钟、随机数
> 都是"不确定源"。读完本篇你能区分 mock 与 fake 两类替身并知道各在何时选谁、用
> monkeypatch 安全地改环境、用 freezegun 冻结时间来测"到期截止"这类逻辑。

## Background

一个通知服务要发邮件：给 `NotificationService` 写单元测试，如果直接连真实 SMTP
（邮件发送协议的服务端），就会遇到三件事——测试跑到一半真发出一封邮件、
网络抖动导致测试时红时绿、每次验证都等一秒级的真实 I/O。

不确定源是根因：网络、时钟、随机数在两次运行之间给出不同结果，
而测试的价值恰恰建立在"同样的输入永远同样的结果"上。此外，
"连接超时""收件人地址非法"这类故障在真实环境里几乎无法按需制造。

测试替身（test double，用可控行为顶替真实依赖的对象）由此成为单测的基本功：
用毫秒级、确定性、可注错的替身把外部世界请出测试。替身不止一种形态——
本实验用同一个邮件场景把 mock 与 fake 各写一遍，亲手体会取舍。

## What

mock 是**记录调用的空壳**：它不实现任何业务，只记住"谁在什么时候用什么参数调了我"，
测试据此断言调用行为。fake 是**能跑的迷你实现**：比如把邮件存进内存 `outbox`
列表的假发件器，测试查它的最终状态。

可以把替身想象成影视行业的替身演员：mock 是只摆姿势的剪影——观众（测试）只关心"戏是不是按剧本演的"（调用了没有、参数对不对）；fake 是能完整演下来的 B 角——观众关心的是"剧情结果对不对"。

但和替身演员不同的是，两者的弱点要心里有数：mock 耦合实现细节（内部改个调用方式，行为没变测试却红了），fake 要自己维护一份实现。


本实验被测对象是 `notifier.py`：业务层 `NotificationService` 只依赖
"有 `.send` 方法的对象"——这条缝隙就是替身的注入点。

## When to Use

典型场景：

- 校验交互契约：发单必须恰好调一次、参数齐全——mock 的主场。
- 校验业务结果：发件后 outbox 里应有一封收件人正确的邮件——fake 的主场。
- 制造故障：`side_effect` 按序抛 `ConnectionError`，故障注入（人为制造异常场景）
  是可靠性测试的地基。
- 测时间相关逻辑："活动 10 月 1 日截止"不冻时间就只能等到 10 月测。

何时不用：被测对象没有任何外部依赖时，替身是多余的；mock 掉你**不拥有**的第三方
接口是坏味道（契约一变，测试全绿但线上崩）——先包一层自己的薄接口，再 mock 薄接口。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| mock（MagicMock） | 记录调用，断言"怎么调用" | 查交互契约 |
| fake（InMemoryMailer） | 迷你实现，断言"结果状态" | 查业务结果 |
| 真实依赖（staging 环境） | 最真实但慢、不确定、难注错 | 少量冒烟验证 |

## Quick Start

前置条件：labs/00 体检通过；全程不连任何真实邮件服务。

```bash
cd labs/04_mock
./mock_lab.sh            # 全流程（绝不真发邮件）
./mock_lab.sh observe    # mock/fake/时间冻结三组对比
```

全量运行的真实输出（2026-09-28 实测，节选）：

```
collected 11 items

tests/test_mock.py ...........                                           [100%]

============================== 11 passed in 0.08s ==============================
```

时间冻结用例单独运行（observe ②，节选）——无论真实日期是哪天，结果永远确定：

```
tests/test_mock.py::test_campaign_sends_within_period PASSED             [ 33%]
tests/test_mock.py::test_campaign_stops_after_deadline PASSED            [ 66%]
tests/test_mock.py::test_campaign_freezegun_context_manager PASSED       [100%]
======================= 3 passed, 8 deselected in 0.07s =======================
```

诚实预期：11 条用例全绿；mock 与 fake 是同一场景的两版实现，两组各自通过。

关键 API 速查（这段在做什么：列出让替身"听话"的五个最常用调用）：

```python
mailer.send.assert_called_once_with(to, subject, body)  # 次数+参数
mailer.send.call_args.args                               # 取最后一次调用参数
mailer.send.side_effect = [None, ConnectionError("x")]   # 按序注入行为
monkeypatch.setenv("SMTP_HOST", "smtp.staging")          # 自动还原的环境变量
@freeze_time("2026-10-01")                               # 冻结 datetime.now
```

## How It Works

**mock 断言"怎么调用"**：`MagicMock` 记录一切调用，`assert_called_once_with(...)`
同时校验次数与参数，`call_args_list` 可取完整历史。`side_effect` 按序返回值或抛错，
第 2 次调用抛 `ConnectionError` 就这样造出来。

**fake 断言"结果状态"**：`InMemoryMailer.send` 把邮件 append 进 `outbox` 列表——一个真的能查的迷你实现。

断言 `outbox` 的内容，与 `NotificationService` 内部怎么组织调用完全解耦。经验法则：查交互契约用 mock，查业务结果用 fake；拿不准时同场景各写一遍（本实验就是这么干的）。


**monkeypatch 受控改环境**：`monkeypatch.setenv("SMTP_HOST", ...)` 改环境变量，
用例结束自动还原。对比手工改 `os.environ`：后者一旦忘了恢复就泄漏到其他用例，
制造出"单独跑绿、合跑挂"的顺序依赖。

**freezegun 冻结时间**：`@freeze_time("2026-10-01 00:00:01")` 让 `datetime.now`
定格在指定时刻——你在 observe ② 输出里看到的三条截止日期用例，
在 6 月跑和在 10 月跑结果一致，因为时间已是受控输入而非环境变量。

## Pitfalls & Q&A

踩坑清单：

- **patch 路径写错，patch 了寂寞**。现象：patch 生效了但被测代码没用替身。
  原因：patch 路径必须是**被测代码查找它的地方**——`notifier.print` 而非
  `builtins.print`。解法：从被测模块的命名空间出发找名字。
- **raises 块内放断言**。lab 03 的坑在 mock 下同样致命：块内所有代码都在
  "期待异常"上下文里，断言等于从未执行。
- **`assert_called_once` 只查次数不查参数**。现象：参数错了测试仍绿。
  解法：次数断言与 `assert_called_with` 按需组合使用。
- **mock 掉第三方 SDK 的深层方法**。现象：第三方升级后测试全绿、线上崩。
  原因：mock 的形状是照着旧版接口写的，接口变了 mock 也跟着"对"。
  解法：包一层自己拥有的薄接口，只 mock 薄接口。

深入问答：

- **Q：mock / stub / spy / fake 的差别？** stub 喂值、spy 只记录、mock 记录并可断言、
  fake 能跑。pytest 语境下 `MagicMock` 覆盖前三，fake 自己写。
- **Q：冻结时间还有别的方案吗？** time-machine（实现更快，lab 08 使用）、
  注入 clock 函数（依赖注入式，最干净但要改设计）。共同原则：测试里时间永远是"被测输入"。
