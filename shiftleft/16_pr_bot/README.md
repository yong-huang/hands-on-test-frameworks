# 16 · PR 评审机器人：把评审清单交给脚本盯

> 「改了实现怎么没带测试？」「新端点怎么没更新契约？」——这些评审意见每条
> PR 都要人肉问一遍。本实验写一个 Danger 风格（评论不阻断）的评审机器人：
> 解析 unified diff（即 `git diff` 输出的那种以 `+++`/`-`/`+` 标记增删行的
> 文本格式）、跑四条评审规则，5 个预制 PR 靶场上 4 个问题 PR 全部
> 命中、干净 PR 零警告，单次运行亚秒级。

## Background

之前的做法：评审靠人盯清单——「带测试了吗」「契约更新了吗」「TODO 挂
issue 了吗」，每个 PR 问一遍，漏问一次就漏进主干。

痛点的核心是**机械可查的评审项占用了人肉评审时间**：这四类问题不需要
理解业务，只需要看 diff 的形状——把它们交给脚本，人的时间留给架构与
语义判断。

本实验的机器人只做「形状检查」：解析 diff 文件、按规则输出结构化警告，
本地 diff 模拟（不依赖 GitHub），接真实平台只是换个 diff 来源。

## What

PR 评审机器人是对 diff 做「形状级评审清单检查」的自动化工具：四条规则
分别盯大变更、缺测试、契约漂移、无主 TODO，命中即输出结构化警告——
Danger 风格（评论呈现，不直接阻断，阻断由项目 11 的门禁负责）。

可以把机器人想成评审会的预习助教：机器先把清单项过一遍并做上标记，
人上来直接讨论标记过的点。但和助教不同的是，它只认 diff 形状——
「测试写得对不对」「契约改得合不合理」仍然归人。

四条规则与靶场命中：

| 规则 | 判据 | 靶场命中 |
|:--|:--|:--|
| large-diff | 变更 > 400 行 | pr_huge（420 行）✓ |
| missing-tests | 改 src/ 无测试伴随 | pr_no_tests / pr_huge ✓ |
| contract-drift | 新增端点但契约文件（API 规格文件，如 openapi.yaml）未动 | pr_new_endpoint ✓ |
| todo-no-issue | TODO/FIXME 无 #issue 号 | pr_todo ✓ |

![diff 解析后四条规则分流，靶场全命中、干净对照零警告](images/pr_bot.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/16_pr_bot/images/pr_bot.html)
> （或本地打开 [`images/pr_bot.html`](images/pr_bot.html)）。
> 五个 PR 两两对照：四个各踩一条规则（huge 踩两条），clean 全躲开。

## When to Use

- 评审会前置过滤：机器标记清单项，评审会只讨论语义与架构。
- 团队约定固化：「TODO 必须挂 issue」「端点必须动契约」从口头变成规则。
- 何时不用：需要理解业务语义的评审项（边界条件对不对）机器判不了；
  规则太密会把真问题淹没在警告里——先从四条起步。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| Danger.js/CI bot | 平台集成深，配置重 | 已有成熟 CI 体系 |
| 本实验（本地 diff 模拟） | 零依赖、规则透明可改 | 理解原理与团队定制 |
| 人肉清单 | 灵活但必漏 | 规则尚未固化时 |

## Quick Start

前置：仓库根目录已有 `.venv`（脚本固定用 `../../.venv/bin/python`）；机器人
零第三方依赖（纯标准库）。`diffs/` 内置 5 个预制 PR（4 问题 + 1 干净；大
diff 由引擎按需生成）。一条命令跑完整动线：

```bash
./pr_bot.sh   # apply → observe（单 PR/五连/计时）→ clean
```

单 PR 演示与五 PR 连跑：

```text
🤖 PR 评审 · pr_new_endpoint.diff
  ⚠️ [contract-drift] 新增/改动 1 个端点但契约文件未更新：@app.post("/api/orders/export")

===== 五 PR 汇总 =====
  pr_clean.diff: 0 条（零警告）
  pr_huge.diff: 2 条（large-diff, missing-tests）
  pr_new_endpoint.diff: 1 条（contract-drift）
  pr_no_tests.diff: 1 条（missing-tests）
  pr_todo.diff: 1 条（todo-no-issue）
验收自检：4 个问题 PR 全部命中 ✓；干净 PR 零警告 ✓
……（--all 连跑的其余 4 个 PR 逐条输出略）
```

验收③：单次运行耗时实测——

```text
>>> 实测耗时 0s（<5s 达标）；5 个 PR 命中明细见 reports/pr_bot_report.json
```

诚实预期：pr_huge 命中两条（large-diff + missing-tests）是规则联动的真实
行为——大 PR 通常也没带测试；「每个 PR 恰好一条」不是设计目标。

## How It Works

**解析只需认三种行**：`+++ b/路径` 定界当前文件、`+`/`-` 累计增删行、
`+` 行内容进 added_lines 供内容类规则（端点/TODO）复用——十几行解析器
就是全部基础设施：

```python
def parse_diff(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:].strip()
            files.setdefault(cur, {"added": 0, "deleted": 0, "added_lines": []})
        elif line.startswith("+") and cur:
            files[cur]["added"] += 1
            files[cur]["added_lines"].append(line)
```

**规则是「文件集合 × 行内容」的两层检查（谓词 = 只返回真/假的判断函数）**：
missing-tests 只看文件集合
（src/ 有动、tests/ 没动）。

contract-drift 看新增行里的端点装饰器（`@app.(get|post|...)`）加「契约文件
不在变更集合」；todo-no-issue 看新增行的 `TODO/FIXME` 且不含 `#\d+`。

**规则联动是特性**：大 diff 通常也没带测试（pr_huge 两条齐发）——机器
把相关缺口一次列全，评审时一并讨论，这正是清单自动化的价值。

## Pitfalls & Q&A

常见故障与解法：

- **`---` 与 `+++` 的前缀判断顺序**：`+++ b/...` 也是 `+` 开头——必须先判
  `+++` 文件头再判新增行，否则文件头会被计成一次「新增」。
- **正则锚定要贴行首**：`TODO_RE` 用 `^\+.*\bTODO\b` 锚定「新增行里的
  TODO」，漏了 `^` 会把上下文行（diff 头部）也算进来。
- **测试文件的判定范围**：`tests/` 目录与根级 `test_*.py` 两种布局都要认，
  只认目录会漏根级测试（本实验正则两种都覆盖）。

Q&A：

- **为什么评论不阻断？** Danger 风格的定位是「评审意见自动化」；阻断
  是门禁的职责（项目 11 的分级 gate）——意见与门禁分离，误报不会错杀。
- **接真实 GitHub 要多少工作？** 只换 diff 来源（GitHub API 拉 PR diff
  塞给 `review()`），规则与输出零改动——本地模拟正是为这一步留的接口。
- **为什么只有四条规则？** 四条 = 评审会上出现频率最高且纯看形状的项；
  规则按「评审会重复问过的」渐进添加，堆规则不如养规则。
