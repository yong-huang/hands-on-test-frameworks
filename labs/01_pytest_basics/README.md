# 01 · pytest 起步：断言重写与运行规则，一切测试的地基

> 你可能用过 `python -m unittest`：断言方法几十个、失败输出只有一行干巴巴的
> `AssertionError`。pytest 换了个思路——**直接写 `assert`，失败时帮你展开中间值**。
> 本实验把运行规则吃透：发现、圈选、早停、配置文件。

## 1. 为什么需要它

- 测试框架的选择决定"写测试的心理成本"：成本越低越愿意写。
- pytest 的三个立身之本：`assert` 重写、用例自动发现、插件生态（后面 29 个实验全是它）。
- 本实验产出：对温度换算模块的 **15 条用例**（含 1 条故意失败），并看懂失败回溯。

## 2. 总览：一次 pytest 运行发生了什么

<!-- 图: images/pytest_basics.svg -->

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://example.github.io/hands-on-test-frameworks/labs/01_pytest_basics/images/pytest_basics.html)
> （或本地打开 [`images/pytest_basics.html`](images/pytest_basics.html)）。

pytest 按图中的流水线走：从 rootdir 出发按收集规则找 `test_*.py` → 逐函数收集
`test_*` → 逐条执行 → 断言失败时**重写**成带中间值的报告 → 汇总退出码（0=全绿）。

## 3. 快速开始

```bash
./pytest_basics.sh          # 全流程：收集确认 → 4 组观察 → 清理
./pytest_basics.sh observe  # 只看 4 组运行对比
```

## 4. 核心概念

### 4.1 用例发现规则

文件 `test_*.py` / `*_test.py`，类 `Test*`（无 `__init__`），函数 `test_*`。
所以 `temperature.py` 不会被误收集——本实验的 `configs/pytest.ini` 还显式圈了 `testpaths`。

### 4.2 断言重写（assertion rewriting）

`assert celsius_to_fahrenheit(0) == 0` 失败时，报告显示
`assert 32.0 == 0`——**两侧表达式的值被算出来**。这是 import 时对字节码做手脚实现的，
代价是首次 import 稍慢，换来全生态最好读的失败输出。验证方法：跑
`./pytest_basics.sh observe` 的第 ① 步看回溯。

### 4.3 圈选与早停：`-k` / `-x` / `-v` / `-s`

| 参数 | 作用 | 本实验验证 |
|:---|:---|:---|
| `-k "not regression_demo"` | 按名字表达式圈选用例 | 圈掉故意失败后 14 条全绿 |
| `-x` | 首个失败立即停 | 在 regression_demo 处刹车 |
| `-v` | 逐条显示用例名 | pytest.ini 里已设为默认 |
| `-s` | 关闭输出捕获，print 直达终端 | 第 ④ 步演示 |

### 4.4 预期失败的用法

`test_regression_demo_deliberately_wrong` 是刻意的错误断言。脚本里对应命令加了
`|| true` 并注释原因——**预期失败也是教材**，但要显式标注，不能让读者以为脚本挂了。

## 5. 配置文件关键字段（pytest.ini）

```ini
[pytest]
testpaths = tests        # 只在 tests/ 里收集，防止误收被测代码
addopts = -v             # 每次运行自动附加的参数
markers = slow: ...      # 自定义 marker 必须先注册，否则告警（lab 09 会用到）
```

坑清单：
- 在包外运行时 pytest 找不到被测模块 → 因为 rootdir 注入了 sys.path；`pytest -c` 指定配置即可稳定 rootdir。
- `pytest.ini` / `pyproject.toml [tool.pytest.ini_options]` / `setup.cfg` 都能当配置，**同目录多个并存时 pytest.ini 优先**。

## 6. 文件结构

```
01_pytest_basics/
├── README.md              # 本文件
├── pytest_basics.sh       # 主演示脚本：apply/observe/clean
├── configs/pytest.ini     # pytest 配置（rootdir 锚点）
├── temperature.py         # 被测模块：4 函数 + 1 分支类
├── tests/test_temperature.py  # 15 条用例（含 1 条故意失败）
└── images/                # 架构图三件套
```

## 7. 深入要点

- **Q: pytest 断言重写的原理？** import 时对测试模块字节码改写，把 `assert expr` 展开为
  记录子表达式求值的形式，失败时报告中间值；仅对测试模块生效。
- **Q: `-k` 和 `-m` 的区别？** `-k` 按名字匹配表达式；`-m` 按 marker（标签）过滤，
  语义化分层（smoke/e2e）用 `-m` 更可维护（lab 09 实战）。
- **Q: 退出码有什么用？** 0=全过、1=有用例失败、2=中断、4=用法错误、5=没收集到用例。
  CI 门禁靠的就是非 0 退出码。
- **Q: 为什么收集结果和预期不符？** 先 `pytest --collect-only` 看收集了什么——
  命名规则、conftest、配置文件都会影响收集（本实验脚本 apply 步骤就是这么做的）。

## 8. 总结

你现在已经会：跑全量、圈选、早停、读失败回溯、写配置。下一篇
[02_fixtures](../02_fixtures/README.md) 解决"用例之间共享准备/清理"的问题——fixture。
