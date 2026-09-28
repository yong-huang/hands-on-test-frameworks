# 08 · 异步与时间测试：把"等一等"从测试里赶出去

> 异步测试两大痛点：重试/退避让用例动辄睡好几秒；时间相关的断言只能"等到那天再验证"。
> 本实验给出确定性方案：注入 sleeper 加速退避，冻结时钟断言时间戳——一个名义
> 3.5 秒的重试用例，真实耗时不到 1 秒。读完本篇你能写出确定性的异步用例，
> 并搞清"加速等待"与"冻结时间戳"是两件不同的事。

## Background

异步系统的核心行为全绑着时间：重试按指数退避、请求有超时、活动有截止日。
要测这些行为，最直觉的办法是真等——重试三次等 3.5 秒、超时路径等满超时时间、
截止逻辑等到那天再跑测试。结果是套件慢（一条用例数秒）、不稳定
（机器卡一下断言就抖）、截止日逻辑一年只能验证几次。

更隐蔽的陷阱是"用时间工具硬加速"：freeze 类工具冻结的是 `datetime.now` 这类
**时钟读取**，而 `asyncio.sleep` 的等待由事件循环挂在 OS 的 selector 上计时——
patch 时钟函数不会让 selector 提前返回，等待还是真实的等待。

出路是把时间变成可注入的依赖：等待用"记账不真睡"的替身加速，
时间戳判断用冻结时钟。行为照常被断言，真实时间被赶出测试。

## What

本实验的方案有两个分工明确的工具：

- **注入 sleeper**：被测客户端把"怎么睡"做成依赖（生产传 `asyncio.sleep`，
  测试传记录名义时长、瞬间返回的假 sleep）。退避序列照样可断言
  （名义 0.5s → 1.0s → 2.0s），真实耗时却是毫秒级。
- **time-machine 冻结时钟**：`@time_machine.travel("2026-09-01")` 让
  `datetime.now` 定格——适合"取当前时间做判断"的时间戳/截止日断言。

可以把这两者想成电影里的时间手法：注入 sleeper 是"快进"（剧情里的三天，放映只要三秒），
time-machine 是"布景换日期"（明明在摄影棚，日历却翻到 9 月 1 日）。
但两者不可互换：快进管"等了多久"，布景管"今天是几号"——混着期待就会踩坑。

被测客户端的可测性设计（这段在做什么：三个注入点对应三类替身）：

```python
AsyncRetryClient(transport=..., sleeper=asyncio.sleep, clock=lambda: now())
```

transport 是网络替身、sleeper 是时间替身、clock 是时钟替身——
**可测性不是测试写出来的，是被测代码设计出来的。**

## When to Use

典型场景：

- 重试/退避/限流逻辑：注入 sleeper 断言退避序列，套件不因测试变慢。
- 超时路径：`asyncio.wait_for(coro, timeout=0.05)` 用 50ms 真实等待覆盖完整超时分支。
- 取消语义：`task.cancel()` 后 `await task` 必须浮出 `CancelledError`——
  异步清理代码最容易吞掉的就是它。
- 截止日/时间戳判断：time-machine 定格 `datetime.now`，截止分支天天可测。

何时不用：纯同步代码没有事件循环问题，普通单测就够；一次性脚本里等待几秒
无伤大雅时，不必为了注入改设计——注入结构本身有维护成本。

同类方式对比：

| 方式 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 真实等待 `sleep` | 慢且抖，断言靠赌 | 几乎不用 |
| 注入 sleeper | 行为可断言，瞬间完成 | 等待/退避/重试逻辑 |
| time-machine | 冻结时钟读取 | 时间戳、截止日判断 |

## Quick Start

前置条件：labs/00 体检通过（pytest-asyncio、time-machine 已装）。

```bash
cd labs/08_async
./async_lab.sh            # 全流程
./async_lab.sh observe    # 看 ① 的整套耗时：0.4s 内跑完名义 3.5s 的退避
```

全量运行的真实输出（2026-09-28 实测，节选）：

```
collected 8 items

tests/test_async.py ........                                             [100%]

============================== 8 passed in 0.12s ===============================
>>> 本套件真实耗时 0.361 s（其中一条用例名义上要退避 3.5 秒）
```

"退避加速"单条用例的证据（observe ②，节选）：

```
tests/test_async.py::test_backoff_accelerated_under_1s PASSED            [100%]
======================= 1 passed, 7 deselected in 0.05s ========================
```

诚实预期：8 条用例全绿，整套真实耗时不到 0.4 秒——其中重试用例名义上要退避
3.5 秒（0.5+1.0+2.0），因 sleeper 是记账不真睡的替身，真实等待为零。
配置里 `asyncio_mode = auto` 让 `async def test_*` 自动可跑。

## How It Works

**pytest-asyncio 与 async fixture**：`asyncio_mode = auto` 之后
`async def test_*` 自动被识别为异步用例。

fixture 也能 `async def`，也能返回工厂
（本实验 `make_client` 返回"按剧本演的客户端 + 录音笔 Recorder"）。

**时间加速的正确姿势**是本实验最核心的一处设计：

```python
# 生产环境
AsyncRetryClient(transport=httpx.AsyncTransport(), sleeper=asyncio.sleep)
# 测试环境
AsyncRetryClient(transport=ScriptedTransport(...), sleeper=fake_sleep)
```

为什么这样写：`time-machine` 冻结不了事件循环的真实等待——`asyncio.sleep`的挂起由 OS selector 级别计时，patch 时钟函数不会让 select 提前返回。

把 sleep 做成依赖后，测试传"记账不真睡"的 fake：记录名义时长、瞬间返回。行为断言（退避序列 `[0.5, 1.0, 2.0]`）与性能断言（真实耗时 <1s）各得其所——后者兜底防止实现回归成真睡。


**time-machine 管另一类时间**：`@time_machine.travel("2026-09-01")` 冻结
`datetime.now`，本实验 `fetched_at` 用例断言"取当前时间打的戳"正确。
加速等待用注入 sleeper、冻结时间戳用 time-machine，两者别混着期待。

**超时与取消的确定性**：挂死的 transport 用 `asyncio.wait_for(coro, timeout=0.05)`
处决——真实等待 50ms，断言却覆盖完整超时路径；取消语义则要求
`task.cancel()` 后 `await task` 浮出 `CancelledError`。

## Pitfalls & Q&A

踩坑清单：

- **strict 模式下异步用例被静默跳过**。现象：`async def test_*` 没跑、收集数为 0。
  原因：pytest-asyncio strict 模式要求每条打 `@pytest.mark.asyncio`。
  解法：配置 `asyncio_mode = auto` 根治。
- **异步用例里写 `time.sleep`**。现象：整个事件循环被阻塞，其他协程饿死。
  解法：永远用 `await asyncio.sleep`。
- **期待 time-machine 加速 `asyncio.sleep`**。现象：patch 了时钟，等待还是那么久。
  原因：事件循环计时走 OS 级 selector，时钟 patch 只影响 wall-clock 读取。
  解法：等待靠依赖注入（sleeper），时间戳才用冻结时钟。
- **用 `sleep(2)` 等"大概率完成"**。现象：偶发超时失败。
  解法：`wait_for`/轮询条件是契约，固定 sleep 是赌运气。

深入问答：

- **Q：怎么测指数退避而不真等？** 注入 sleeper 断言"名义退避序列"，
  再用真实耗时断言兜底防回归成真睡。
- **Q：flaky 的异步用例怎么治？** 消灭真实时间依赖（await 结果、wait_for 条件）
  而非加长 sleep——加长只是降低概率，不改变赌的本质。
