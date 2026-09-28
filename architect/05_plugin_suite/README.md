# 05 · 公司级 pytest 插件套件：从「会用插件」到「会造基建」

> labs/10 学过怎么写一个 pytest 插件；本实验是它的架构师版本——把三个团队的
> 通用诉求（失败留现场、慢用例可见、用例分层）沉淀成一个可 `pip install -e`
> 的公司级包。与 labs/10 的本质区别不在功能在纪律：**默认零行为，配置了才生效**
> ——别的团队装了它，他们的套件必须原样跑。

## Background

排查失败靠「我本地再跑一次试试」是最大的时间黑洞——失败瞬间的现场（traceback、参数、marker——用例的分类标签、耗时）应该自动落盘，而不是靠人复现。慢是漂移来的：没有排行，没人知道套件是哪天开始变慢的。

分层分发（冒烟/全量）是流水线快反馈的地基——但三件事每个团队都在自己的 conftest（pytest 约定的目录级配置文件，其中的 fixture 与钩子对同目录用例自动生效）里重写一遍，实现质量参差。


公司级基建的回答是做成**一个包**：entry point 挂载、统一配置、统一行为。
难点不在功能（labs/10 已证明单个 hook 会写），在纪律——装进共享 venv 的
插件，默认必须对无关套件完全隐形。

## What

qa_kit 是一个公司级 pytest 插件包：pytest 启动时经 entry point 自动加载，
三个钩子（pytest 暴露给插件的扩展函数，在测试执行的固定时机被回调）各管一段
——失败落现场（evidence/）、慢用例排行、分层统计与圈选。

可以把 qa_kit 想成写字楼的物业套餐：租户（各团队的测试套件）不装修也有基础服务（消防、保洁——默认行为里的"什么都不做"也是服务），要增值服务（门禁、绿植）自己去前台登记（`--qa-*` 配置开关）。

但和物业不同的是，这里的"不登记就零行为"是硬纪律——插件经 entry point 全局加载，装上即影响所有套件，任何默认行为都会在别人仓库里变成「升级后套件行为变了」的事故。


entry point 是插件被自动加载的唯一正道：`[project.entry-points.pytest11]`
让 pytest 启动时自动发现插件——不需要 conftest 拷贝、不需要 `-p` 参数。
公司级基建的分发问题在打包层解决。

## When to Use

典型场景：

- 多团队共享一个 venv/CI 池：统一失败取证与慢用例治理的口径。
- 流水线分层：快反馈层消费 `-m smoke`（项目 10 直接使用）。
- 度量看板的数据源：慢用例排行 JSON 喂给项目 23/27 的看板。

何时不用：单一团队、约定可以靠口头同步时，conftest 更轻；
插件功能还在频繁变化的探索期也不适合做成"公司级"——
发布纪律（兼容、卸载还原）会拖慢迭代。

## Quick Start

前置条件：labs/00 体检通过；脚本会 `pip install -e` 本包并在 clean 时卸载还原。

```bash
cd architect/05_plugin_suite
./plugin_suite.sh apply     # pip install -e qa_kit + entry point 识别检查
./plugin_suite.sh observe   # 零侵入跑演示套件 → evidence → 慢排行 → -m smoke 圈选
./plugin_suite.sh clean     # 卸载插件还原 venv + 删产物
```

实测输出（6 条用例：2 smoke / 3 full / 1 无标记，含 1 故意失败 + 1 故意慢）：

```
1 failed, 5 passed in 0.74s
=====> [qa_kit] 分层统计：smoke=2 full=3 unmarked=1
=====> [qa_kit] 慢用例排行（≥0.5s，共 1 条）：
         0.613s  test_store_flow.py::test_slow_report_query

evidence/
└── test_store_flow.py__test_deliberate_failure.txt   # nodeid/耗时/markers/traceback 全套现场

-m smoke → 2 passed, 4 deselected in 0.08s
```

诚实预期：`1 failed` 是演示套件里的故意失败用例——它恰好是 evidence 留痕
的演示对象，不是插件故障。验收核对点：测试代码里没有任何 `import qa_kit`
——全部能力来自 entry point 自动加载 + `--qa-*` 配置开关，这就是「零侵入」。

配置字段（这段在做什么：把行为全部挂到显式开关上）：

| 配置 | 作用 | 坑 |
|:---|:---|:---|
| `--qa-evidence-dir` | 开启失败留现场 | 不配置必须完全无行为（公司级插件的生命线） |
| `--qa-slow-threshold` | 慢用例阈值（秒） | 太小全在排行里=没有排行 |
| `--qa-slow-report` | 排行 JSON 落盘路径 | 给后续看板（项目 23/27）喂料 |
| `markers smoke/full` | 分层注册 | 未注册的 marker 会告警——注册本身就是文档 |

## How It Works

**三个钩子各管一段**。

`pytest_runtest_protocol`（wrapper）记录每条用例的协议级耗时（含 fixture——
pytest 为用例准备前置资源的夹具——的 setup，比 call duration 更接近真实成本）
并做分层计数。

`pytest_runtest_makereport`（hookwrapper）在失败时拿报告落 evidence；
`pytest_sessionfinish` 汇总排行与统计——你在上面输出里看到的三段
（分层统计、慢排行、evidence 文件）分别来自这三个钩子。


**协议级耗时和 call 耗时差在哪**：protocol 含 setup/teardown（fixture 是
测试成本大头）；call 只含测试体。慢排行用前者，因为「fixture 里 sleep」
同样是团队的时间。

**evidence 的内容边界**：存能复现的最小现场——nodeid、traceback、markers、
耗时、时间戳。不该存敏感数据（生产连接串、真实用户数据）——evidence 目录
会进 CI 产物归档，泄漏面等于归档系统的可见范围。

**hookwrapper 必须显式声明（本次踩的真坑）**：`pytest_runtest_makereport`里用 `outcome = yield` 的旧式写法，**必须**加`@pytest.hookimpl(hookwrapper=True)`。

漏了装饰器，pytest 会把它当普通hook 实现，函数 yield 出的 generator 对象直接漏进下游插件链，报`INTERNALERROR: 'generator' object has no attribute 'skipped'`——而且炸的是别人的插件，不是你的。


## Pitfalls & Q&A

踩坑清单：

- **hookwrapper 漏装饰器**。现象：`INTERNALERROR` 且炸在无关插件上。
  解法：yield 式写法必须配 `hookwrapper=True`（见 How It Works）。
- **默认行为偷偷开启**。现象：别的团队升级后套件多出文件/变慢。
  解法：一切行为挂 `--qa-*` 开关，不配置 = 零行为。
- **慢用例阈值设太小**。现象：排行里一大半用例，排行失去信号价值。
  解法：阈值按「排行 ≤ 10 条」校准。
- **evidence 里混入敏感数据**。现象：CI 归档泄漏连接串。
  解法：evidence 白名单字段，测试数据用替身。

深入问答：

- **Q：为什么「默认零行为」是公司级插件的生命线？**
  插件经 entry point 全局加载，装上即影响所有套件。任何默认行为
  （比如自动写文件、自动跳过）都会在别人仓库里变成「升级后套件行为变了」
  的事故。开关式设计把变化权留给使用方的配置评审。
- **Q：分层标记和项目 10 流水线怎么接？**
  快反馈层 = `-m smoke`（本实验实测 2/6 条、0.08s）；全量层 = 不带 `-m`。
  分层本身免费，贵的是保持 smoke 集合小而准——这正是 01 审计里
  「冒烟层 ≤ 总量 20% 且覆盖 P0 路径」验收的执行手段。
- **Q：labs/10 的插件和 qa_kit 什么关系？**
  labs/10 证明「会写一个 hook」；qa_kit 证明「会发布一个包」——entry point、
  打包、零侵入纪律、跨套件兼容（和 venv 里已有的 ministore-report 插件共存）、
  卸载后环境还原。功能是插件的事，纪律是平台的事。
