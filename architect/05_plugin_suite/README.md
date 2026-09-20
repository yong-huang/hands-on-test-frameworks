# 05 · 公司级 pytest 插件套件：从「会用插件」到「会造基建」

> labs/10 学过怎么写一个 pytest 插件；本实验是它的架构师版本——把三个团队的通用诉求
> （失败留现场、慢用例可见、用例分层）沉淀成**一个可 `pip install -e` 的公司级包**。
> 与 labs/10 的本质区别不在功能在纪律：**默认零行为，配置了才生效**——别的团队装了它，
> 他们的套件必须原样跑。清单第 5/28 项。

## 1. 为什么需要它

- 排查失败靠「我本地再跑一次试试」是最大的时间黑洞——失败现场应该自动存在 evidence/。
- 慢是漂移来的：没有排行，没人知道套件是哪天开始变慢的。
- 分层分发（冒烟/全量）是流水线快反馈的地基（项目 10 直接消费 `-m smoke`）。

## 2. 总览：核心机制一图看懂

![qa_kit 插件](images/plugin_suite.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/architect/05_plugin_suite/images/plugin_suite.html)
> （或本地打开 [`images/plugin_suite.html`](images/plugin_suite.html)）。

心智模型一句话：**entry point 挂载（pytest11），三个钩子各管一段**——runtest_protocol
计时与分层计数、makereport 失败落现场、sessionfinish 汇总输出；配置不开启就什么都不做。

## 3. 快速开始

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

验收核对：测试代码里没有任何 `import qa_kit`——全部能力来自 entry point 自动加载 +
`--qa-*` 配置开关，这就是「零侵入」。

## 4. 核心概念

### 4.1 entry point：插件被自动加载的唯一正道
`[project.entry-points.pytest11]` 让 pytest 启动时自动发现插件——不需要 conftest 拷贝、
不需要 `-p` 参数。公司级基建的分发问题在打包层解决。

### 4.2 三个钩子各管一段
`pytest_runtest_protocol`（wrapper）记录每条用例的协议级耗时（含 fixture setup，比
call duration 更接近真实成本）并做分层计数；`pytest_runtest_makereport`（hookwrapper）
在失败时拿报告落 evidence；`pytest_sessionfinish` 汇总排行与统计。

### 4.3 hookwrapper 必须显式声明（本次踩的真坑）
`pytest_runtest_makereport` 里用 `outcome = yield` 的旧式写法，**必须**加
`@pytest.hookimpl(hookwrapper=True)`。漏了装饰器，pytest 会把它当普通 hook 实现，
函数 yield 出的 generator 对象直接漏进下游插件链，报 `INTERNALERROR: 'generator'
object has no attribute 'skipped'`——而且炸的是别人的插件，不是你的。

## 5. 配置字段

| 配置 | 作用 | 坑 |
|:---|:---|:---|
| `--qa-evidence-dir` | 开启失败留现场 | 不配置必须完全无行为（公司级插件的生命线） |
| `--qa-slow-threshold` | 慢用例阈值（秒） | 太小全在排行里=没有排行 |
| `--qa-slow-report` | 排行 JSON 落盘路径 | 给后续看板（项目 23/27）喂料 |
| `markers smoke/full` | 分层注册 | 未注册的 marker 会告警——注册本身就是文档 |

## 6. 文件结构

```
architect/05_plugin_suite/
├── README.md
├── plugin_suite.sh                # apply(装) → observe(跑+验收) → clean(卸载)
├── qa_kit/                        # 可安装包
│   ├── pyproject.toml             # entry point pytest11 = qa_kit.plugin
│   └── src/qa_kit/plugin.py       # 三钩子实现（约 120 行）
├── demo_tests/
│   ├── pytest.ini
│   └── test_store_flow.py         # SUT 数据层演示套件（零侵入消费插件）
└── images/                        # 图三件套
```

## 7. 深入要点

**Q1：为什么「默认零行为」是公司级插件的生命线？** 插件经 entry point 全局加载，
装上即影响所有套件。任何默认行为（比如自动写文件、自动跳过）都会在别人仓库里变成
「 upgrading 后套件行为变了」的事故。开关式设计把变化权留给使用方的配置评审。

**Q2：evidence 里该存什么、不该存什么？** 存能复现的最小现场：nodeid、traceback、
markers、耗时、时间戳。不该存敏感数据（生产连接串、真实用户数据）——evidence 目录
会进 CI 产物归档，泄漏面等于归档系统的可见范围。

**Q3：协议级耗时和 call 耗时差在哪？** protocol 含 setup/teardown（fixture 是测试成本
大头）；call 只含测试体。慢排行用前者，因为「fixture 里 sleep」同样是团队的时间。

**Q4：分层标记和项目 10 流水线怎么接？** 快反馈层 = `-m smoke`（本实验实测 2/6 条、
0.08s）；全量层 = 不带 `-m`。分层本身免费，贵的是保持 smoke 集合小而准——这正是
01 审计里「冒烟层 ≤ 总量 20% 且覆盖 P0 路径」验收的执行手段。

**Q5：labs/10 的插件和 qa_kit 什么关系？** labs/10 证明「会写一个 hook」；qa_kit 证明
「会发布一个包」——entry point、打包、零侵入纪律、跨套件兼容（和 venv 里已有的
ministore-report 插件共存）、卸载后环境还原。功能是插件的事，纪律是平台的事。

## 8. 总结

一个 120 行的包，把团队三件高频小事变成自动基建；「默认零行为」与「entry point 分发」
两条纪律让它有资格叫公司级。慢用例排行 JSON 也为度量看板（项目 23/27）预埋了数据源。
下一篇是清单项目 6「YAML DSL 接口用例引擎」：DSL 和代码写用例的权衡，做完就有资格回答。
