# 10 · 写一个自己的 pytest 插件：把套路沉淀成基础设施

> 前九个实验里你反复做三类事：给慢用例记账、给失败用例留现场、校验团队约定。
> 每个项目复制粘贴一遍？不如做成**插件**——`pip install` 之后全团队即插即用。
> 本实验产出可安装的 `pytest-ministore-report`，并在另一个真实项目里复用它。

## 1. 为什么需要它

- 插件是 pytest 生态的货币：conftest 只属于一个目录，插件属于所有项目。
- 写插件 = 学 pytest 的**钩子体系**——理解框架在何时把控制权交给你。
- 本插件三个能力都是真实团队刚需：分层约定校验、慢用例发现、失败现场自动落盘。

## 2. 总览：插件钩入 pytest 执行流的四个时机

<!-- 图: images/plugin.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/10_plugin/images/plugin.html)
> （或本地打开 [`images/plugin.html`](images/plugin.html)）。

收集期（marker 校验）→ 执行期（makereport 记账与落盘）→ 会话收尾（写 JSON 报告）
→ 终端摘要（terminal_summary）。四个钩子各管一段。

## 3. 快速开始

```bash
./plugin_lab.sh            # 装 → 四能力验证 → 跨项目复用
cat ministore-report.json  # 插件产出：slow 列表 + failed 列表
```

## 4. 核心概念

### 4.1 入口点：pytest11

`pyproject.toml` 里声明 `[project.entry-points.pytest11]`，装进环境即被 pytest
自动发现。**礼貌插件的自我修养**：所有功能包在 `--ministore` 开关里，
不开就完全隐形——本插件在共享 venv 里装着，其他 29 个实验毫无感知。

### 4.2 marker 校验：配置错误在收集期炸出来

`pytest_collection_modifyitems` 里检查 `ministore_tier(tier=...)` 的合法性，
非法直接 `pytest.UsageError`——**退出码非 0、一条用例都没跑**。
演示：`tier="prod"` 被拦，报错信息直接指出文件与合法值。

### 4.3 runtest_makereport：失败留痕的标准插桩点

`@pytest.hookimpl(hookwrapper=True)` 拿到每阶段的 TestReport：`rep.when == "call"`
且 `rep.failed` 时，把 nodeid、耗时、异常回溯（`rep.longreprtext`）、marker 清单
落成 `contexts/<用例名>.json`。CI 失败后不用复跑，现场已在盘里。

### 4.4 慢用例自动打标

同一钩子里读 `rep.duration`，超过阈值（默认 0.1s，可调）就 `item.add_marker("slow")`
并记入报告——"slow"从人肉声明变成度量事实。

### 4.5 易错点（本实验真实踩过）

- pytest 9 移除了 `config._terminalreporter` 私有属性——终端输出必须走
  `pytest_terminal_summary` 官方钩子。
- 平铺布局的包要用 `[tool.setuptools] packages=[...]` 显式声明，否则 setuptools 拒装。
- 演示"校验失败"的坏用例别放进默认收集目录，否则整个套件被它拦停。

## 5. 关键字段（pyproject.toml）

```toml
[project.entry-points.pytest11]          # pytest 插件入口点组
ministore_report = "pytest_ministore_report.plugin"
[tool.setuptools]
packages = ["pytest_ministore_report"]   # 平铺布局必须显式声明
```

## 6. 文件结构

```
10_plugin/
├── README.md
├── plugin_lab.sh                 # 装 → 验证 → 复用 → 清理
├── pyproject.toml                # 入口点与打包元数据
├── configs/pytest.ini
├── pytest_ministore_report/
│   ├── __init__.py
│   └── plugin.py                 # 全部钩子逻辑（约 120 行，注释即教材）
├── badcase/test_bad_marker.py    # 非法 tier 演示（不进默认收集）
├── tests/test_demo.py            # 快/慢/挂/分层 四种形态
└── images/
```

## 7. 深入要点

- **Q: conftest 和插件怎么选？** 单项目用 conftest；跨项目/需版本化分发用插件。
- **Q: hookwrapper 和普通钩子的区别？** wrapper 包裹原实现（yield 前后插逻辑、
  可拿到结果对象），普通实现是并联多播。需要"结果"时必须 wrapper。
- **Q: 怎么保证插件不干扰不相关项目？** 功能全挂显式开关下；注册 marker 但不注入
  行为；不碰任何私有 API。

## 8. 总结

你已经有能力为团队生产测试基础设施。阶段二毕业。下一篇进入阶段三：
[11_sut_app](../11_sut_app/README.md)——造一个后面 19 个实验共用的被测应用。
