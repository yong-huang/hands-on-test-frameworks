# 10 · 测试反模式检测器：把「全绿但没在测」的测试找出来

> 测试全绿不等于在测。本实验用纯标准库（ast + re）写了九类测试反模式的
> 只读检测器：坏样本 10 个埋点（故意写进样本的反模式点，各对应一条规则）
> 全部命中、好样本零误报；对 labs 全量 37 个测试文件实跑出 22 个真实反模式
> 点——每一条都可人工核对，是治理清单，不是分数。`--gate` 一键变 CI 卡点。

## Background

之前的做法：测试质量靠 code review 人眼，「这个测试到底在测什么」的争论
没有机器证据；`assert True` 这类测试和精确断言的测试在覆盖率报表里长得
一模一样。

痛点的核心是**静态可辨的坏味道没有静态工具**：变异测试能证明「断言缺口」
但太贵，不能天天跑。而 `assert True`、`pytest.raises(Exception)`、`time.sleep`
这些结构性反模式，用 AST（抽象语法树——源码解析成的节点树，可程序化检查）
毫秒级就能扫完整个仓库。

本实验把九类常见反模式做成表驱动的 AST 规则（九条规则集中定义在一张
RULES 字典表里，加规则就是加一行），交付一个只读、零第三方依赖、可当
CI 卡点的检测器。

## What

测试反模式检测器是用 AST 静态分析找出「全绿但没在测」模式的只读工具：
九类规则（空断言、永真比较、恒真数学、裸 Exception、裸 except、无断言
测试、测试内 sleep、调试 print、注释掉的断言），`--gate` 时发现即退出码 1。

可以把检测器想成机场安检的 X 光机：只看形状（语法结构）不看内容（业务
语义）。但和 X 光不同的是它只报「形状可疑」，液体到底是什么仍要人开箱——
`assert total >= 100` 是否合理断言它不判断，只抓结构性反模式。

九类规则与 labs 实测命中（37 个文件）：

| 规则 | 含义 | labs 命中 |
|:--|:--|--:|
| assert_constant | 空断言/恒真断言 | 6 |
| sleep_in_test | 测试内真实等待 | 6 |
| no_assert | 无断言测试 | 6 |
| raises_base | 裸 Exception 吞一切异常 | 2 |
| print_debug / tautology_math | 调试残留 / 恒真数学 | 各 1 |

![九类反模式的 AST 检测：靶场全命中、对照零误报、真实资产出清单](images/antipattern.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/10_antipattern/images/antipattern.html)
> （或本地打开 [`images/antipattern.html`](images/antipattern.html)）。
> 三条验收路径就是图上的三条通路：靶场、对照、真实资产。

## When to Use

- 测试套件例行体检：毫秒级扫全仓库，与项目 9 的变异测试互补——变异找
  深水缺口（贵），本工具扫面上反模式（便宜）。
- CI 快层卡点：`--gate` 让新增反模式进不了主干。
- 何时不用：拿它替代变异测试或人审——静态规则只覆盖结构类坏味道，
  「断言了错误的期望值」这类语义问题它看不见。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| ruff/flake8 插件 | 生态成熟，规则同源可迁移 | 已有 lint 体系的团队 |
| 本实验（自研 AST） | 零依赖、规则表驱动、教学透明 | 理解原理与定制规则 |
| 变异测试（项目 9） | 度量断言强度，成本高 | 核心域深水体检 |

## Quick Start

前置：仓库根有 `.venv`（脚本用它启动 Python；本实验自身零第三方依赖，纯
标准库 ast/re——没装任何包，但没这个解释器脚本起不来）。一条命令跑完整动线：

```bash
./antipattern.sh   # apply → observe（靶场/对照/labs 全量）→ clean
```

第一段，坏样本靶场：10 个埋点全部命中（≥9/10 达标）——

```text
扫描 samples/bad：2 个测试文件，10 个反模式点
  ⛔ samples/bad/test_bad_more.py:6 [sleep_in_test] sleep 真实等待（time.sleep(0.01)）
……（其余 9 条命中；规则统计：assert_constant 2 / tautology 1 / tautology_math 1 /
  sleep_in_test 1 / print_debug 1 / commented_assert 1 / raises_base 1 / bare_except 1 / no_assert 1）
```

第二段，好样本零误报（gate 模式退出码 0）；第三段，labs 全量真实报告：

```text
扫描 samples/good：1 个测试文件，0 个反模式点
>>> 零误报 ✓
扫描 ../../labs：37 个测试文件，22 个反模式点
  ⛔ ../../labs/01_pytest_basics/tests/test_temperature.py:82 [print_debug] print 调试残留
……（assert_constant 6 / sleep_in_test 6 / no_assert 6 / raises_base 2 / 其余 2）
```

诚实预期：labs 的 22 条里有几条是**教学故意**——labs/17 的 antipattern
教学文件、labs/09 用 sleep 模拟慢任务做并行训练。检测器只报事实，
「哪些该修、哪些是教具」的判断在人。

## How It Works

**断言有三张脸**：assert 语句、`pytest.raises(...)`、playwright 的
`expect(...)`——无断言规则必须三张都认，否则 playwright 测试全线误报
（本实验真踩过：labs/17 一口气误报 5 条，修复后清零）。

**规则即遍历 + 谓词**：谓词（predicate）是一个只做真假判断的函数，如「这条
assert 的目标是不是常量」。每个测试函数 walk 一遍，命中谓词就记
`{file, line, rule, detail}`。

「注释掉的断言」不走 AST，用行级正则 `#\s*assert\b`（缩进友好）；
`--gate` 把发现数变成退出码。

```python
for node in ast.walk(fn):
    if isinstance(node, ast.Assert):
        if isinstance(node.test, ast.Constant):        # assert True / assert 1
            findings.append({"rule": "assert_constant", ...})
```

**扫真实仓库要设边界**：第一版把 `labs/.venv` 里第三方库（gevent 等）
的两千多个测试也扫了进来——验证对象是本系列实验，不是依赖包。过滤
`.venv`/`node_modules`/点目录（注意保留 `..` 相对路径部分）。

## Pitfalls & Q&A

常见故障与解法：

- **playwright 测试被误报 no_assert**：`expect(...)` 是断言的第三种形态，
  has_assert 只认 `ast.Assert` 就会全线误报。三形态合一后 labs 误报清零。
- **rglob 扫进依赖目录**：`labs/.venv` 里第三方测试套件贡献 2000+ 噪音；
  过滤路径部件时别把 `..`（相对路径的父目录）也当点目录滤掉。
- **海象运算符笔误**：`out = ROOT := ...` 这类低级语法错让脚本第一秒就崩，
  先 `python -m py_compile` 再跑。

Q&A：

- **为什么不用 ruff 插件？** 规则完全可迁移成 ruff/flake8 插件；自研是为了
  零依赖、规则表驱动透明，以及——读懂 AST 规则本身就是本实验的教学目标。
- **labs 的 22 条都要修吗？** 分两类：真坏味道（`assert True`、裸 Exception）
  与教学故意（sleep 模拟慢任务）。报告给的是事实清单，治理优先级人来排。
- **和项目 9 什么关系？** 变异测试度量断言强度（深、贵），本工具抓结构性
  反模式（浅、毫秒级）；先扫面上再钻深水，是同一件事的两个粒度。
