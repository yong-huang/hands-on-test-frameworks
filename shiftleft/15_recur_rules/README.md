# 15 · 缺陷防复发规则库：让每个修过的 bug 都留下一条自动拦路

> 「这个 bug 修过了怎么又犯？」——因为修复只改了那一行，没留下任何会再拦
> 一次的资产。

> 本实验取三个真实 bug 域（金额精度 float / 并发超卖竞态 / 时区 naive——
> 「裸」datetime，调 now() 不带时区参数）：先写复现测试（缺陷态 3 红、修复
> 态 3 绿），再沉淀为防复发资产（2 条 semgrep 规则 + 1 个并发模板）——同类
> 新缺陷代码喂入即自动拦下，不靠人眼。

## Background

之前的做法：bug 修完就翻篇——修复 commit 里只有那一行 diff，测试如果补了
也只覆盖当时的写法；下次有人用新写法犯同一个错，没有任何东西会拦。

痛点的核心是**修复没有沉淀为资产**：金额精度、超卖、时区这类 bug 的复发率
极高，因为「错法」有很多种写法，而防复发只覆盖了被修的那一种。

本实验把修复链延长一步：复现测试先行（红→绿证明 bug 被治好）→ 语义沉淀
（把 bug 的「错法本质」写成规则或模板）→ 用写法全新的同类缺陷代码实测
拦截——资产生效才算修复完成。

## What

缺陷防复发规则库是一组「从历史 bug 沉淀出来的自动拦截资产」：能被模式
描述的缺陷沉淀为 semgrep 规则，不能被语法描述的（如竞态）沉淀为复现测试
模板——新代码触发同类缺陷即被自动拦下。

可以把规则库想成疫苗接种记录：每个得过并治好的病（bug）留一条抗体
（规则/模板），同类病原再进来直接被拦。但和疫苗不同的是，病原会变异
（新写法犯同种错）——所以沉淀的对象是「错法本质」（float 承接金额、
无锁的 check-then-act、裸 now()），不是某个具体写法。

三个 bug 域与资产的映射：

| bug | 错法本质 | 防复发资产 |
|:--|:--|:--|
| bug01 金额精度 | float 承接金额 | semgrep：`money-float-arith` |
| bug03 时区 | 裸 `datetime.now()` | semgrep：`naive-datetime-now` |
| bug02 并发超卖 | 无锁 check-then-act | 复现模板：60 并发抢 10 名额 |

![坏修双实现、复现测试先行、资产拦截同类新代码](images/recur_rules.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/15_recur_rules/images/recur_rules.html)
> （或本地打开 [`images/recur_rules.html`](images/recur_rules.html)）。
> 三条通路对应三段验收：坏红、修绿、拦截。竞态没有语法形状，走模板通路。

## When to Use

- 每修一个非平凡 bug：修复 PR 里必须带上「沉淀物」（规则或模板），否则
  修复只完成一半。
- 事故复盘的最后一环：复盘报告的 action item 里加一条「沉淀为规则 #N」。
- 何时不用：一次性环境问题、无法归因出「错法本质」的 bug——硬沉淀会
  产出永远不命中的死规则。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 只修 bug 不沉淀 | 下次同错再犯 | 永远不要（本实验的反面教材） |
| 规则/模板沉淀（本实验） | 一次沉淀，同类永拦 | 可归因错法本质的 bug |
| 逃逸分析报告 | 分析深刻但不拦截 | 归因阶段（architect 26，其下游即本实验） |

## Quick Start

前置：仓库根 `.venv`（pytest + semgrep，apply 步自检补装）。三个 bug 域的
坏修实现都在 `bugs/`（业务背景是订单的金额、库存与截单）。一条命令跑完整动线：

```bash
./recur_rules.sh   # apply → observe（坏红/修绿/拦截）→ clean
```

第一段，缺陷态复现：3 个复现测试对缺陷实现全红——

```text
FAILED tests/test_repro.py::test_bug03_timezone_boundary[buggy] - AssertionEr...
3 failed, 3 deselected in 0.10s
>>> 缺陷态退出码 1（非零即红 ✓）——复现测试先行留档
```

第二段，修复态回归：同一套测试对修复实现全绿（红→绿 = bug 被治好）：

```text
3 passed, 3 deselected in 0.05s
```

第三段，规则库拦截写法全新的同类缺陷代码：

```text
  ⛔ naive-datetime-now  newcode/cutoff_new_bad.py:6
  ⛔ money-float-arith  newcode/money_new_bad.py:7
  semgrep 拦截类别：2 / 3
=====> [observe] ④ 第三类（并发超卖）由复现模板拦截：喂新代码 → 当场红（预期失败）
1 failed in 0.09s
>>> 已按预期红：并发模板把 bug02 的同类新实现拦在门外
```

（输出块内秒数为当次实测，你的机器数字会不同。）

诚实预期：semgrep 只拦「有语法形状」的两类；竞态没有形状走并发模板——两类资产各管各的形状，缺一不可。

## How It Works

**坏修双实现是复现的载体**：每个 bug 域一对模块（`money_buggy.py` /
`money_fixed.py`，同接口异实现），复现测试按实现参数化——`-k buggy` 全红
证明测试真的在测缺陷，`-k fixed` 全绿证明修复真的有效。两趟运行由脚本
分别核验退出码（1/0）。

**沉淀的颗粒度是「错法本质」**：bug01 的本质是「金额变量被 float 承接」，
规则聚焦落在金钱命名赋值目标内的 `float($Y)` 调用——新写法照旧命中：
`subtotal = subtotal + float(raw)`，因为命中的是本质不是写法：

```yaml
patterns:
  - pattern: float($Y)          # 罪证：float 承接
  - pattern-inside: |
      $X = ...                  # 且它流向金钱命名的变量
  - metavariable-regex:
      metavariable: $X
      regex: (?i).*(price|total|amount|discount|money|subtotal|payable).*
```

**竞态走模板不走模式**：超卖的本质是「check 与 act 之间有窗口」，AST（抽象
语法树——源码解析成的结构树，semgrep 的模式匹配就发生在它上面）里没有这个形状——沉淀为并发复现模板（60 线程过 barrier 抢 10 名额，
断言成功数恰为 10），喂入任何带同类窗口的新实现，模板当场红。

## Pitfalls & Q&A

常见故障与解法：

- **复现测试在缺陷版上「偶绿」**：竞态用例不施压就测不出来——模板用
  Barrier 让 60 线程同抢、缺陷版在 check 与 act 之间留窗口（复刻真实
  「查库存要走一次读库」），把偶发变成必现。
- **semgrep 模式只匹配直接赋值**：`$X = float($Y)` 漏掉
  `subtotal = subtotal + float(raw)` 这种嵌套写法——改为聚焦 `float($Y)`
  调用 + `pattern-inside` 约束赋值目标。
- **`$rcode（` 让 bash 报 unbound variable**：多字节字符紧跟 `$var` 会被
  并进变量名（bash 3.2）。本实验脚本两次踩同一坑后全量改 `${var}`——
  与项目 13 同款教训。

Q&A：

- **沉淀物会不会变成死规则？** 会，验收第四段专门用「写法全新的同类缺陷」
  实测拦截——命不中就不算沉淀完成，死规则在评审时删。
- **三个 bug 为什么选这三个？** 订单域复发率最高的三类，且恰好覆盖资产
  形态：模式、模式、模板——「竞态必须用模板」是本实验最重要的认知。
- **和 architect 26 什么关系？** 26 做逃逸缺陷的归因分析（哪些 bug 该
  沉淀）；本实验是归因结论的下游落地（怎么沉淀、怎么验证沉淀有效）——
  分析与拦截，上下游互补。
