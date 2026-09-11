# 04 · mock 与测试替身：把外部世界请出你的测试

> 单测跑到一半真发了一封邮件？测试的第一原则是**不碰真实外部依赖**——
> SMTP、时钟、随机数都是"不确定源"。替身（test double）分很多种，
> 本实验用同一个邮件服务场景，把 mock 与 fake 各写一遍，亲手体会取舍。

## 1. 为什么需要它

- 稳定：不依赖网络/时钟/第三方，测试随时可跑、永远可复现。
- 可控：能制造真实世界难造的故障（连接失败、坏地址），故障注入是可靠性测试的地基。
- 快：毫秒级替代秒级 I/O。

## 2. 总览：被测服务与两类替身的关系

<!-- 图: images/mock.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/04_mock/images/mock.html)
> （或本地打开 [`images/mock.html`](images/mock.html)）。

`NotificationService` 只依赖"有 .send 方法的对象"——这条缝就是替身注入点。
mock 是**记录调用的空壳**，fake 是**能跑的迷你实现**；下方时间轴演示 freezegun 冻结时钟。

## 3. 快速开始

```bash
./mock_lab.sh            # 全流程（绝不真发邮件）
./mock_lab.sh observe    # mock/fake/时间冻结三组对比
```

## 4. 核心概念

### 4.1 mock：断言"怎么调用"

`MagicMock` 记录一切调用，`assert_called_once_with(...)` / `call_args_list` 校验
调用形状。`side_effect` 可以按序抛错——制造故障。**弱点是耦合实现**：
内部改个调用方式，行为没变测试却红了。

### 4.2 fake：断言"结果状态"

`InMemoryMailer` 把邮件存进 `outbox` 列表——一个真的能查的迷你实现。
断言 `outbox` 内容，与内部实现解耦。**弱点是要自己维护实现**。
经验法则：查交互契约用 mock，查业务结果用 fake；同场景各写一遍（本实验就是这么干的）。

### 4.3 monkeypatch：受控地改环境

`monkeypatch.setenv/delenv` 改环境变量，用例结束自动还原——对比手工
`os.environ` 修改的"泄漏到其他用例"风险。

### 4.4 freezegun：冻结时间

"9 月活动 10 月 1 日截止"这种逻辑，不冻时间就只能在活动月测试。
`@freeze_time("2026-10-01 00:00:01")` 让 `datetime.now` 定格——截止分支天天可测。

### 4.5 易错点

- `patch` 路径必须是**被测代码查找它的地方**（`notifier.print` 而非 `builtins.print`）。
- `raises` 块内别放断言（lab 03 的坑在 mock 下同样致命）。
- mock 的 `assert_called_once` 只查次数不查参数——两者经常要一起用。

## 5. 关键 API 速查

```python
mailer.send.assert_called_once_with(to, subject, body)  # 次数+参数
mailer.send.call_args.args                               # 取最后一次调用参数
mailer.send.side_effect = [None, ConnectionError("x")]   # 按序注入行为
monkeypatch.setenv("SMTP_HOST", "smtp.staging")          # 自动还原的环境变量
@freeze_time("2026-10-01")                               # 冻结 datetime.now
```

## 6. 文件结构

```
04_mock/
├── README.md
├── mock_lab.sh             # 主演示脚本
├── configs/pytest.ini
├── notifier.py             # 被测对象：通知服务（SmtpClient + 业务层）
├── tests/test_mock.py      # 11 条：mock/fake 同场景对比 + monkeypatch + freezegun
└── images/
```

## 7. 深入要点

- **Q: mock/stub/spy/fake 的差别？** stub 喂值、spy 记录、mock 记录+断言、fake 能跑。
  pytest 语境下 MagicMock 覆盖前三，fake 自建。
- **Q: 什么时候 mock 是坏味道？** mock 掉你**不拥有**的第三方接口时——契约一变测试全绿但线上崩；
  此时包一层自己的薄接口再 mock 它。
- **Q: 冻结时间还有别的方案吗？** time-machine（更快，lab 08 用）、注入 clock 函数
  （依赖注入式，最干净）。测试里时间永远是"被测输入"。

## 8. 总结

外部依赖现在都在你掌心：网络可断、时间可停、故障可造。下一篇
[05_coverage](../05_coverage/README.md)：用覆盖率找出你没测到的分支，并让门禁拦截它。
