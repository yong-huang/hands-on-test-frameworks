# 08 · 异步与时间测试：把"等一等"从测试里赶出去

> 异步测试两大痛点：重试/退避让用例动辄睡好几秒；时间相关的断言只能"等到那天再验证"。
> 本实验给出确定性方案：**注入 sleeper 加速退避，冻结时钟断言时间戳**，
> 一个名义 3.5 秒的重试用例，真实耗时不到 1 秒。

## 1. 为什么需要它

- 重试、超时、限流、截止日——异步系统的核心行为全绑着时间。
- 真等真实时间：慢 + 不稳定（机器卡一下断言就抖）。测试要的是**行为正确**，不是真等。

## 2. 总览：一次重试的完整时序（含被加速的部分）

<!-- 图: images/async.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/08_async/images/async.html)
> （或本地打开 [`images/async.html`](images/async.html)）。

客户端对瞬态错误按指数退避重试：0.5s → 1.0s → 2.0s。测试里 transport 与 sleeper
都是注入的替身——退避"名义上发生、瞬间完成"，时序行为照样被精确断言。

## 3. 快速开始

```bash
./async_lab.sh            # 全流程
./async_lab.sh observe    # 看 ① 的整套耗时：0.4s 内跑完名义 3.5s 的退避
```

## 4. 核心概念

### 4.1 pytest-asyncio 与 async fixture

`asyncio_mode = auto` 让 `async def test_*` 自动可跑；fixture 也能 async，
也能返回工厂（本实验 `make_client` 返回"按剧本演的客户端 + 录音笔 Recorder"）。

### 4.2 时间加速的正确姿势：注入 sleep

**坑**：`time-machine` 冻结不了事件循环的真实等待——`asyncio.sleep` 的挂起由
OS selector/select 级别计时，patch 时钟函数不会让 select 提前返回。
正确姿势是**把 sleep 做成依赖**：生产传 `asyncio.sleep`，测试传"记账不真睡"的
fake（记录名义时长、瞬间返回）。行为断言（退避序列 `[0.5, 1.0, 2.0]`）与
性能断言（真实耗时 <1s）各得其所。

### 4.3 time-machine 管另一类时间

`@time_machine.travel("2026-09-01")` 冻结 `datetime.now`——适合**时间戳/截止日**
这类"取当前时间做判断"的断言（本实验 `fetched_at` 用例）。加速等待用 4.2，
冻结时间戳用 time-machine，两者别混着期待。

### 4.4 超时与取消的确定性测试

- 挂死的 transport 用 `asyncio.wait_for(coro, timeout=0.05)` 处决——
  真实等待只有 50ms，断言却覆盖了完整超时路径。
- 取消语义：`task.cancel()` 后 `await task` 必须浮出 `CancelledError`——
  异步清理代码最容易吞掉的正是它。

### 4.5 易错点

- pytest-asyncio strict 模式下忘打 `@pytest.mark.asyncio` 用例直接被跳过——auto 模式根治。
- 异步用例里写 `time.sleep` 会阻塞整个事件循环，永远用 `await asyncio.sleep`。

## 5. 被测客户端的可测性设计

```python
AsyncRetryClient(transport=..., sleeper=asyncio.sleep, clock=lambda: now())
```

三处注入点对应三类替身：transport=网络替身、sleeper=时间替身、clock=时钟替身。
**可测性不是测试写出来的，是被测代码设计出来的。**

## 6. 文件结构

```
08_async/
├── README.md
├── async_lab.sh             # 主演示脚本
├── configs/pytest.ini       # asyncio_mode = auto
├── client.py                # 被测对象：指数退避重试客户端（3 个注入点）
├── tests/test_async.py      # 8 条：重试矩阵/加速/超时/取消/冻结
└── images/
```

## 7. 面试要点

- **Q: 怎么测指数退避而不真等？** 注入 sleeper，断言"名义退避序列"，
  真实耗时断言兜底防回归成真睡。
- **Q: freezegun/time-machine 能加速 asyncio.sleep 吗？** 不能——事件循环计时走
  OS 级 selector；时钟 patch 只影响 wall-clock 读取。等待要靠依赖注入。
- **Q: flaky 的异步用例怎么治？** 消灭真实时间依赖（await 结果、wait_for 条件）
  而非加长 sleep——`sleep(2)` 是赌运气，`wait_for` 是契约。

## 8. 总结

异步与时间不再是测试的盲区。下一篇 [09_xdist](../09_xdist/README.md)：
把 60 秒的套件并行到 15 秒以内——并行化与用例独立性改造。
