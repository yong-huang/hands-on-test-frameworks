# 07 · 可测性设计重构：把「说不准的东西」变成构造参数

> 测试写不动（要真睡 1 秒）、写得脆（monkeypatch 模块常量、手动清全局），
> 根因多半不在测试，在被测代码把时间/随机/存储焊死了。本实验取 labs/11
> 会话域的真实痛点做依赖注入重构：同一套行为测试跑双实现全绿（不改行为），
> 过期测试从真睡 1.05s 变成拨针 5µs，模块全局触碰 2→0，报告数字全部可复核。

## Background

之前的做法：测试在代码外面「撬」——`monkeypatch.setattr` 改模块常量、
`time.sleep` 真实等待、`dict.clear()` 清模块级状态。能跑，但每条测试都在
还债，写得越多人越不想写。

痛点的核心是**可测性问题实际是设计问题**：时间从 `time.monotonic()` 来、
随机从 `secrets` 来、状态藏在模块字典里——这三个「说不准的东西」焊死在
实现里，测试就只能撬。撬的代价随用例数放大：过期语义每条真睡 1 秒，
十条就是十秒起。

本实验做依赖注入（DI，把依赖从内部硬编码改为构造参数）+ 端口适配器：
时间、随机源、存储定义成端口（Protocol，只约定方法的类型），业务只依赖
端口；生产注入 SystemXxx 实现，测试注入假钟与固定随机源。

## What

可测性设计重构是在**不改行为**的前提下，把被测代码的不确定依赖变成构造
参数，让测试用替身瞬时代替真实机制。

三个端口：Clock（时间）、IdGenerator（随机）、SessionStore（存储），各配
生产实现（SystemClock / SystemIdGenerator / InMemorySessionStore）；测试
替身只有 FixedClock——只有时间真正「说不准」，随机与存储测试直接复用生产实现。

可以把重构想成给手表开后盖：原来机芯和表壳焊死，换电池要砸开（monkeypatch
撬模块）；开后盖之后（构造参数）电池随便换。但和换电池不同的是——开后盖
不会让表走得更准：DI 不修业务 bug，它把「测不到」变成「随便测」。

![硬编码三件套 vs 端口注入：行为等价、代价剧减](images/dft_refactor.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/07_dft_refactor/images/dft_refactor.html)
> （或本地打开 [`images/dft_refactor.html`](images/dft_refactor.html)）。
> 左右两列是同一业务语义的两种机制；中间行为测试是等价性的裁判。

## When to Use

- 测试需要真实等待/真实随机/真实文件才能写的域（本实验的过期语义就是典型）。
- 任何重构之前：先立行为等价测试（本实验 4 用例 × 双实现），改完跑绿。
- 何时不用：纯函数没有可注入的依赖；一次性脚本不值得为它建端口。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| monkeypatch 撬 | 零重构，但真等待+全局污染照旧 | 临时验证、不能改的第三方 |
| DI 重构（本实验） | 一次重构，测试快且隔离 | 长期演进的核心域 |
| 只靠集成测试兜底 | 真实但慢，过期类场景等不起 | 端到端验收层 |

## Quick Start

前置：仓库根 `.venv`（pytest 即可）。`legacy/` 是 labs/11 会话语义的复刻
（labs/11 本体零改动），`refactored/` 是 DI 版。一条命令跑完整动线：

```bash
./dft_refactor.sh   # apply → observe（等价+对照+度量）→ clean
```

行为等价：同一套 4 用例（签发/校验/角色/唯一性）× 两个实现全绿：

```text
8 passed in 0.03s
>>> 双实现全绿 = 重构不改行为的证明；行为与机制（时间/随机/存储）已分离
```

度量报告（全部数字机械可复核：墙钟（真实流逝时间）取自 pytest durations
的 call 阶段，行数与全局触碰由 AST（抽象语法树）统计）：

```text
指标                        重构前 legacy        重构后 DI
过期测试墙钟（实测/条）              1.06s             5µs
测试触碰模块全局（处）               2                 0
测试函数行数（AST）               7 行               8 行
行为等价（4 用例×2 实现）           8 passed           8 passed

过期测试加速：>10000×（1.06s → 5µs，✓ <100ms 达标；legacy ✓ ≥1s）
……（节选：略去「assert 前语句数」一行与「说明」列，完整输出以实机为准）
```

诚实预期：DI 版测试函数**更长**（8 行 vs 7 行）——显式构造注入对象是代价；
可测性买到的不是行数，是 5µs 的速度与零全局污染的隔离，两个数字报告里都给。

## How It Works

**端口三件套**：时间、随机、存储各定义一个 Protocol（只约定方法签名），
业务类 `SessionService` 只依赖端口；生产实现（SystemClock/SystemIdGenerator/
InMemorySessionStore）与测试替身（FixedClock）都从端口外插进来：

```python
class FixedClock:                       # 测试替身：手动拨针（节选自 refactored/sessions.py）
    def __init__(self, start: float = 0.0):
        self._now = start
    def now(self) -> float:             # 业务只问 now()，时间从哪来它不关心
        return self._now
    def advance(self, seconds: float) -> None:
        self._now += seconds

clock = FixedClock()
svc = SessionService(clock=clock, ids=SystemIdGenerator(),
                     store=InMemorySessionStore(), ttl=3600.0)
clock.advance(3601.0)                   # 「一小时后」不再需要真等一小时
```

**等价性用「插头」证明**：LegacyAdapter 把 legacy 的模块函数包装成与
`SessionService` 相同的接口，conftest 的 `make_service` 工厂按参数返回两个
实现——同一套行为测试对两个实现都绿，就是「不改行为」的机械证明。

labs/11 是语义复刻的对象而非被改的文件，其原有测试不受任何影响。

**度量口径全部机械**：墙钟（wall clock，真实流逝的时间，区别于 CPU 时间）取
自 pytest `--durations` 的 call 阶段（即测试函数
体）；fake 测试小于 5ms 会被 durations 隐藏，改在进程内实测函数体，同口径
取 3 次最小值。

行数与「模块全局触碰处数」（`monkeypatch.setattr` 或 `legacy._xxx` 清场）由
AST（抽象语法树——Python 把源码解析成的结构化树，可程序化统计行数与语句）
统计——「触碰 2→0」就是行为与机制解耦的机械证据。

## Pitfalls & Q&A

常见故障与解法：

- **构造参数错位**：`SessionService(clock, store, ttl)` 漏了 ids，位置参数
  全体右移。注入对象 ≥3 个时一律关键字传参。
- **fake 测试的耗时在 --durations 里消失**：<5ms 被 pytest 隐藏，`-vv` 也
  不显示。进程内实测函数体（与 durations 的 call 阶段同口径），取 3 次最小。
- **import 写在测试函数体内**：会灌水 AST 行数/语句统计，import 一律在模块顶。

Q&A：

- **为什么不直接 monkeypatch TTL（time-to-live，token 有效期秒数，即 legacy 的
  模块常量）凑合？** 能跑：patch 常量→真睡→复原，每条
  测试三件套。但真睡随用例数线性放大（10 条过期用例 = 10 秒起），且模块
  全局被反复触碰——DI 一次性付清重构成本，测试永久快且隔离。
- **4 个行为用例能证明等价吗？** 覆盖签发/校验/角色/唯一性主干，是抽样证明
  而非穷举；配合「既有接口测试全绿」（本实验即行为套件本身）构成双保险。
- **DI 版测试更长，赚什么？** 赚 5µs 与零隔离成本，还赚一个隐含红利：换
  存储实现（内存→Redis）不动业务与测试——端口的第二收益。
