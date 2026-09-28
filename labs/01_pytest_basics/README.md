# 01 · pytest 起步：断言重写与运行规则，一切测试的地基

> Python 标准库 unittest 写断言要背几十个方法，失败输出只有一行干巴巴的 `AssertionError`；
> pytest 直接写 `assert`，失败时自动展开中间值。读完本篇你能写出并运行第一批 pytest 用例、
> 读懂失败报告，并用 `-k` / `-x` 等参数精准控制运行范围。

## Background

Python 自带 unittest：测试写成类，断言靠 `self.assertEqual` 这类方法（xUnit 风格框架——
测试代码长得像生产代码，断言是方法调用而不是语句）。这套约定下，写测试前要先记住方法名，
失败时报告只给一行 `AssertionError`，表达式两侧的值是多少要自己加 print 去看。

痛点是**写测试的心理成本**：样板代码多（类、`self`、`setUp`）、断言方法要背、
失败信息不展开。成本越高，人越不愿意写测试——测试覆盖不足往往不是不会写，
而是每个用例的启动成本太高。

pytest 对这三点各给出一个反向设计：断言直接写原生 `assert`、用例按命名约定自动发现
（不写类不写样板）、其余能力交给插件生态。本实验之后的 29 个实验全部构建在 pytest 之上，
所以先把它的运行规则吃透。

## What

pytest 是一个 Python 测试框架：按命名约定自动发现用例、用原生 `assert` 断言、
以插件机制扩展功能。

可以把 pytest 想象成一台自动阅卷机：按命名约定收卷（只收 `test_*.py`）、逐题批改（逐个运行 `test_*` 函数）、错题展开讲（断言失败时把表达式的中间值印出来）。

但和阅卷机不同的是，它还支持只重考指定的题（`-k` 按名字圈选）、第一题错就停（`-x` 早停）、以及把评分规则写成配置文件（`pytest.ini`）。


一次 pytest 运行的完整流程：从项目根目录出发按收集规则找测试文件 → 逐函数收集 →
逐条执行 → 断言失败时重写成带中间值的报告 → 汇总退出码（0 表示全绿）。

## When to Use

典型场景：

- 给纯函数或模块写单元测试：本实验的温度换算模块就是最小样本。
- 接手老代码先补回归测试：行为变化会以失败报告的形式展开，比人工比对输出可靠。
- 搭 CI（持续集成，提交后自动跑检查的服务）门禁：pytest 的非 0 退出码就是流水线的红灯信号（见 Pitfalls 的退出码表）。

何时不用：浏览器端到端测试要用 pytest-playwright 之类插件配合（lab 16 起）；
只有两三个一次性检查脚本的小工具，直接写 `assert` 的 Python 脚本更轻。
一旦测试文件超过几个，pytest 的自动发现和失败报告就开始回本。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| unittest | 标准库自带、xUnit 风格、断言靠方法 | 不能引入第三方依赖时 |
| pytest | 原生 assert + 自动发现 + 插件生态 | 默认选择，也是本系列的选择 |
| 直接 `assert` 脚本 | 无框架，无报告无发现 | 一次性检查，不进 CI |

## Quick Start

前置条件：labs/00 体检通过（pytest 在共享的 `.venv` 虚拟环境里）。

```bash
cd labs/01_pytest_basics
./pytest_basics.sh          # 全流程：收集确认 → 4 组观察 → 清理
./pytest_basics.sh observe  # 只看 4 组运行对比
```

全量运行的真实输出（2026-09-28 实测，节选）：

```
=================================== FAILURES ===================================
___________________ test_regression_demo_deliberately_wrong ____________________

    def test_regression_demo_deliberately_wrong():
        """【故意失败】需求说冰点是 32°F，写错成 0——看断言重写如何展开中间值。
    
        这是全实验唯一预期失败的用例：pytest 会把 `==` 两侧算出来，
        在报告里显示 `assert 32.0 == 0`，比 unittest 的 AssertionError 直观得多。
        """
>       assert celsius_to_fahrenheit(0) == 0, "冰点应该是 0（故意写错，演示失败输出）"
E       AssertionError: 冰点应该是 0（故意写错，演示失败输出）
E       assert 32.0 == 0
E        +  where 32.0 = celsius_to_fahrenheit(0)

tests/test_temperature.py:95: AssertionError
=========================== short test summary info ============================
FAILED tests/test_temperature.py::test_regression_demo_deliberately_wrong - A...
========================= 1 failed, 16 passed in 0.10s =========================
```

`-k` 圈选排除故意失败用例后的真实输出（同一次 observe，节选）：

```
collected 17 items / 1 deselected / 16 selected

tests/test_temperature.py ................                               [100%]

======================= 16 passed, 1 deselected in 0.06s =======================
```

诚实预期：本实验 17 条用例里有 1 条**故意失败**（`test_regression_demo_deliberately_wrong`，
断言把冰点 32°F 写错成 0）。全量运行以 `1 failed` 收尾是设计内行为，不是环境问题；
`-k` 排除它之后应全绿。

被测代码是 `temperature.py`（4 个温度换算函数 + 1 个恒温器类），
用例在 `tests/test_temperature.py`。四个最常用的运行参数：

| 参数 | 作用 | 本实验验证 |
|:---|:---|:---|
| `-k "not regression_demo"` | 按名字表达式圈选用例 | 圈掉故意失败后 16 条全绿 |
| `-x` | 首个失败立即停 | 在 regression_demo 处刹车 |
| `-v` | 逐条显示用例名 | pytest.ini 里已设为默认 |
| `-s` | 关闭输出捕获，print 直达终端 | observe 第 ④ 步演示 |

配置文件 `configs/pytest.ini`（这段在做什么：把运行约定固化成文件，
pytest 启动时自动读取）：

```ini
[pytest]
testpaths = tests        # 只在 tests/ 里收集，防止误收被测代码
addopts = -v             # 每次运行自动附加的参数
markers = slow: ...      # 自定义 marker 必须先注册，否则告警（lab 09 会用到）
```

## How It Works

**断言重写（assertion rewriting）**是 pytest 最核心的一处机制：import 测试模块时，pytest 在字节码（Python 源码编译出的中间表示）层面把 `assert expr` 展开成"记录子表达式求值"的形式，失败时就能报告每个子表达式的值。

你在 Quick Start 节选输出里看到的两行：


```
E       assert 32.0 == 0
E        +  where 32.0 = celsius_to_fahrenheit(0)
```

正是重写的产物——`==` 两侧的值被真的算了出来。代价是首次 import 稍慢，
范围是只对测试模块生效。

**用例发现规则**：文件 `test_*.py` / `*_test.py`，类 `Test*`（且不能带 `__init__`），函数 `test_*`。

所以被测模块 `temperature.py` 不会被误收集——收集入口由配置文件锚定：pytest 从 rootdir（由 `pytest.ini` 所在目录确定的项目根）出发，只在 `testpaths` 指定的`tests/` 里找。


**marker 注册**：`markers = slow: ...` 这行不是摆设。自定义 marker（用例的标签，
配合 `-m` 过滤）必须先在配置里注册，否则 pytest 运行时会发
`PytestUnknownMarkWarning` 告警——lab 09 会大量使用 marker，注册习惯从这里建立。

**收集结果排查**：怀疑收集多了或少了，先跑 `pytest --collect-only` 看它到底收集了什么。
命名规则、conftest.py（pytest 的项目级共享配置文件，lab 02 详述）、配置文件三者都会影响收集结果——本实验脚本 apply 步骤
就是这么做的。

## Pitfalls & Q&A

踩坑清单：

- **在包外运行时找不到被测模块**。现象：`from temperature import ...` 报
  `ModuleNotFoundError`。原因：rootdir 会注入 `sys.path`（Python 的模块搜索路径），
  换目录运行后锚点变了。解法：用 `pytest -c` 指定配置文件，稳定 rootdir。
- **多个配置文件并存时行为和预期不符**。`pytest.ini`、`pyproject.toml` 的
  `[tool.pytest.ini_options]`、`setup.cfg` 都能当配置，同目录并存时 **pytest.ini 优先**。
- **自定义 marker 忘了注册**。现象：运行时出现 `PytestUnknownMarkWarning`。
  解法：在配置文件 `markers` 字段里登记。
- **把预期失败当成脚本坏了**。故意失败的演示用例必须显式标注（本实验用 docstring
  标了【故意失败】），配套命令加 `|| true`——预期失败也是教材，但不能让读者以为挂了。

深入问答：

- **Q：`-k` 和 `-m` 的区别？** `-k` 按名字匹配表达式，适合临时圈选；`-m` 按 marker
  （标签）过滤，适合语义化分层（smoke/e2e）——长期维护的分层用 `-m` 更可读（lab 09 实战）。
- **Q：退出码有什么用？** 0=全过、1=有用例失败、2=中断、4=用法错误、5=没收集到用例。
  CI 门禁靠的就是非 0 退出码，所以"没收集到用例"在 CI 里也算失败而不是成功。
- **Q：unittest 的 `assertEqual` 语义 pytest 都覆盖吗？** 覆盖且更直接：方法调用
  变成原生 `assert` 表达式，中间值展开是 unittest 没有的能力（见 Quick Start 输出）。
