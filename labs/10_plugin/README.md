# 10 · 写一个自己的 pytest 插件：把套路沉淀成基础设施

> 前九个实验里你反复做三类事：给慢用例记账、给失败用例留现场、校验团队约定。
> 每个项目复制粘贴一遍？不如做成插件——`pip install` 之后全团队即插即用。
> 读完本篇你能写出一个可安装的 pytest 插件（本实验产出 `pytest-ministore-report`）、
> 理解钩子体系在何时把控制权交给你，并在另一个真实项目里复用它。

## Background

每个项目的测试都会沉淀出相同的套路：给慢用例记账、失败时自动保存现场、
校验团队的分层约定。这些逻辑放 `conftest.py`（pytest 的项目级配置文件）只能惠及
一个目录——第二个项目要用，就得整段复制，从此两份代码各自漂移。

框架早已给出答案：插件。pytest 的一切能力——收集规则、报告、并行——都是插件，第三方能力也以插件形式接入（前面用过的 xdist、syrupy、hypothesis 全是）。

写插件的过程就是学 pytest 的**钩子体系**（hook，框架在固定时机回调外部代码的机制）：框架在收集期、执行期、收尾期把控制权交出来，插件在交出来的时机里做事。


本实验的插件有三个能力，都是真实团队刚需：分层约定校验（非法 marker 在收集期拦截）、
慢用例自动打标（`slow` 从人肉声明变成度量事实）、失败现场自动落盘
——CI（持续集成，提交后自动跑检查的服务）失败后不用复跑，上下文已在盘里。

## What

pytest 插件是一个声明了 `pytest11` 入口点（entry point，Python 包元数据里的
"装进环境即被框架自动发现"的注册机制）的包。pytest 启动时扫描环境里所有
`pytest11` 入口点并加载，插件由此获得响应各类钩子的机会。

可以把插件想成理发店的附加服务：顾客（pytest 运行）按流程走完洗剪吹的每一步，
每步之间留有"要不要加个护理"的接口（钩子）。但和附加服务不同的是，
礼貌插件的自我修养是**默认隐形**——所有功能包在 `--ministore` 开关里，
不开就完全不干扰。本插件就装在共享 venv 里，其他 29 个实验毫无感知。

插件的四个钩子各管一段：收集期（`pytest_collection_modifyitems`，marker 校验）→
执行期（`pytest_runtest_makereport`，记账与落盘）→ 会话收尾
（写 JSON 报告）→ 终端摘要（`pytest_terminal_summary`）。

## When to Use

典型场景：

- 团队约定需要强制执行：marker 分层必须合法，错误配置在跑任何用例之前被拦下。
- CI 失败排查要现场：失败用例的 nodeid、耗时、异常回溯自动落成 JSON 文件。
- 慢用例治理要数据：按阈值自动给超时用例打 `slow` 标，报告里排队。

何时不用：逻辑只属于单个项目时，conftest.py 更简单——插件多一层打包与版本管理
的成本；逻辑会随项目频繁变化时也不适合做插件，插件适合"稳定套路"。

同类方式对比：

| 方式 | 差异 | 什么时候选它 |
|:---|:---|:---|
| conftest.py | 零打包成本，只属于一个目录 | 单项目脚本 |
| pytest 插件 | 入口点分发，全环境可用 | 跨项目复用、团队分发 |
| 外部脚本后处理 | 不侵入 pytest，但拿不到执行期上下文 | 只汇总已有产物 |

## Quick Start

前置条件：labs/00 体检通过；本实验的插件以可编辑模式
（`pip install -e .`，源码即安装）装进共享 venv。

```bash
cd labs/10_plugin
./plugin_lab.sh            # 装 → 四能力验证 → 跨项目复用
cat ministore-report.json  # 插件产出：slow 列表 + failed 列表
```

全量运行的真实输出（2026-09-28 实测，节选；含一条故意失败用例）：

```
=====> [observe] ① 全量跑（含一条故意失败）：插件生成 ministore-report.json + contexts/*.json
slow=1  failed=1  -> ministore-report.json
=========================== short test summary info ============================
FAILED tests/test_demo.py::test_failing_case - AssertionError: 预期失败：演示...
==================== 1 failed, 4 passed, 1 warning in 0.39s ====================
--- 报告内容：
{
  "plugin": "pytest-ministore-report",
  "exitstatus": 1,
  "slow_threshold_s": 0.1,
  "slow": [
    {
      "nodeid": "tests/test_demo.py::test_slow_case",
      "duration_s": 0.3063
    }
  ],
  "failed": [
    "tests/test_demo.py::test_failing_case"
  ]
}
```

marker 校验拦截非法 tier（observe ③，节选；**预期失败演示**）：

```
collecting ... ERROR: [ministore] badcase/test_bad_marker.py::test_bad_tier 的 tier 必须是 core/slow/smoke，收到的是 'prod'
>>> 退出码非 0：坏配置在跑任何用例之前就被拦下
```

诚实预期：observe ① 的 `1 failed` 与 ③ 的 UsageError 都是脚本故意制造的演示（失败上下文落盘、坏配置拦截），不是插件或环境问题。

observe ④ 展示跨项目复用：在 labs/01 目录直接用 `--ministore`（同 venv 无需再装），lab 01 的故意失败用例同样被落了上下文。


打包声明 `pyproject.toml`（这段在做什么：把包注册成 pytest 插件并声明包列表）：

```toml
[project.entry-points.pytest11]          # pytest 插件入口点组
ministore_report = "pytest_ministore_report.plugin"
[tool.setuptools]
packages = ["pytest_ministore_report"]   # 平铺布局必须显式声明
```

## How It Works

**入口点加载**：pytest 启动时枚举环境里 `pytest11` 组的全部入口点并 import 对应模块——
你在 apply 输出的 plugins 行里看到的 `ministore-report-0.1.0` 就是加载成功的标志。
装进环境即生效，不需要任何配置文件登记。

**marker 校验在收集期拦截**：`pytest_collection_modifyitems` 钩子拿到全部收集到的用例，检查 `ministore_tier(tier=...)` 的合法性，非法直接抛 `pytest.UsageError`——退出码非 0、一条用例都没跑。

**配置错误炸在最早的时刻**，是校验类插件的黄金位置。


**失败留痕的标准插桩点**：

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    rep = (yield).get_result()
    if rep.when == "call" and rep.failed:
        ...  # nodeid / duration / longreprtext / markers 落成 contexts/<用例名>.json
```

为什么这样写：`hookwrapper=True` 包裹原实现——`yield` 之前是执行前、之后是执行后，`get_result()` 拿到框架生成的 `TestReport` 对象。

普通钩子实现是并联多播（拿不到结果对象），需要"结果"时必须用 wrapper 形式。`rep.when == "call"` 精确锁定用例执行阶段，`rep.longreprtext` 就是终端里那段异常回溯的原文。


**慢用例自动打标**：同一钩子里读 `rep.duration`，超过阈值（默认 0.1s，可调）就
`item.add_marker("slow")` 并记入报告——你在输出 JSON 的 `slow` 列表里看到的
`test_slow_case 0.3063s` 就是这条链路的产物。

## Pitfalls & Q&A

踩坑清单（本实验真实踩过）：

- **pytest 9 移除 `config._terminalreporter` 私有属性**。现象：升级后插件在
  终端摘要处崩。解法：终端输出必须走 `pytest_terminal_summary` 官方钩子，
  不碰任何私有 API。
- **平铺布局的包拒装**。现象：`pip install` 报找不到包。
  解法：`pyproject.toml` 里用 `[tool.setuptools] packages=[...]` 显式声明。
- **演示"校验失败"的坏用例放进默认收集目录**。现象：整个套件被它拦停。
  解法：坏用例放 `badcase/` 不进默认收集，只在专门演示时显式指定路径。
- **插件不设开关，污染无关项目**。解法：所有功能包在显式 CLI 开关下，
  注册 marker 但不注入行为——礼貌插件的自我修养。

深入问答：

- **Q：conftest 和插件怎么选？** 单项目用 conftest；跨项目、需要版本化分发
  （pip 安装、独立迭代）用插件。
- **Q：hookwrapper 和普通钩子的区别？** wrapper 包裹原实现（yield 前后插逻辑、
  可拿到结果对象），普通实现是并联多播。需要"结果"时必须 wrapper。
- **Q：怎么保证插件不干扰不相关项目？** 功能全挂显式开关下；不碰私有 API；
  本插件装在共享 venv 里，其他 29 个实验全程无感知就是验证。
