# ⛓️ 14 · pre-commit 本地门禁链：提交前一秒，四道闸全过一遍

> 静态检查只在 CI 跑，意味着提交之后几分钟才知道坏了一个 F401（ruff 对
> 「未用导入」的缺陷代号）——来回改一趟趟磨。

> 本实验把项目 10-13 的四道检查**编排**成 pre-commit 门禁链：快层
> （ruff+mypy+gitleaks）挂进 `git commit`、实测 0.5s 全绿；含假密钥的提交
> 被真实阻断（终端证据留档）；重层（反模式检测+semgrep）手动深查。

## Background

之前的做法：静态检查全在 CI——提交 → 排队 → 装环境 → 全量扫描 → 报红 →
本地改 → 再提交，一个 F401 折腾一整圈。

痛点的核心是**反馈延迟放大修复成本**（项目 1 漏斗的铁律：拦截越靠左越
便宜），而提交阶段恰好是编码与 CI 之间还没人把守的闸门。且四道检查分散
在四个实验目录里，没有一键入口。

本实验只做**编排不写检查器**：ruff/mypy（项目 11）、反模式检测器（项目
10）、semgrep 规则（项目 12）、gitleaks（项目 13）全部复用，pre-commit
把它们串成「快层挡提交、重层管深查」的本地链。

## What

pre-commit 门禁链是用 pre-commit（一个把检查脚本挂进 git 提交流程、
commit 时自动执行的框架）编排的本地检查链：快层挂进 `git commit`（秒级、
阻断、必过），重层挂 manual stage（按需触发、更细更深）。

可以把快层想成登机口的随身行李安检——秒级、人人必过；重层是托运深检——
按需触发、查得更细。但和机场不同的是，这里的「安检规则」与 CI 完全同一
份——本地放行的，CI 不会翻脸。

编排表（`.pre-commit-config.yaml`，规则全部复用前序项目；项目 11 的检查
拆成 ruff、mypy 两个钩子，故四道检查对应 5 个钩子：快层 3 + 重层 2）：

| 钩子 | 层 | 来源 | 触发 |
|:--|:--|:--|:--|
| ruff check / mypy | ⛔ 快层 | 项目 11 | commit 自动 |
| gitleaks protect --staged | ⛔ 快层 | 项目 13 | commit 自动 |
| 反模式检测 detector | 🔍 重层 | 项目 10 | manual 手动 |
| semgrep scan --error | 🔍 重层 | 项目 12 | manual 手动 |

![快层挡提交、重层管深查，四道检查编排复用](images/precommit_chain.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/14_precommit_chain/images/precommit_chain.html)
> （或本地打开 [`images/precommit_chain.html`](images/precommit_chain.html)）。
> 链仓库是独立 git 操练场（同项目 8 的隔离纪律），labs/11 零接触。

## When to Use

- 四道检查的日常入口：写完代码 `pre-commit run --all-files` 一键自查。
- 团队统一钩子：config 进 git 全组同款，`git commit` 自动过门禁。
- 何时不用：重层挂上 commit 会拖慢提交——「磨叽的门禁会被 --no-verify 绕过」。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| CI-only 检查 | 反馈分钟级 | 兜底他律层（保留） |
| 本实验（本地链） | 秒级反馈，编排复用 | 日常开发主入口 |
| 各检查手动单跑 | 无编排，容易漏 | 一次性排查 |

## Quick Start

前置：仓库根 `.venv` 与 pre-commit/ruff/mypy/semgrep/gitleaks（apply 步
自检补装；gitleaks 走 brew，需有 Homebrew）。链仓库每次重跑自动重建。
一条命令跑完整动线：

```bash
./precommit_chain.sh   # apply → observe（快层/阻断/重层/对比）→ clean
```

快层全量实测（三个钩子全绿，秒级）：

```text
ruff 快层（风格与缺陷）...........Passed
mypy 快层（类型检查）.............Passed
gitleaks 快层（密钥闸·暂存区扫描）.Passed
>>> 快层实测耗时 1s（<15s 达标；精确口径见 measure.py）
```

验收②：含假密钥的提交被真实阻断——

```text
gitleaks 快层（密钥闸·暂存区扫描）.......Failed
- hook id: gitleaks-protect
- exit code: 1
>>> 已按预期阻断（exit 1，gitleaks 出手）——终端证据在 reports/blocked_evidence.txt
```

验收③：本地 vs CI 反馈延迟对比（CI 为文档化估算口径）：

```text
本地快层（ruff+mypy+gitleaks，实测）：0.7s，PASS
本地重层（antipattern+semgrep，实测）：3.4s，PASS
CI 参考口径（文档化估算，architect/10 快反馈层预算）：300s
快层相对 CI 预算：约 458× 反馈提速（本地秒级 vs CI 分钟级）
验收自检：快层 <15s ✓ 达标
产物：reports/chain_timing.json
……（秒数与倍数为作者机器当次实测，量级参考；你的数字会不同，
300s 估算口径与 PASS 判定不变）
```

诚实预期：重层 manual 触发时快层钩子也会跑（pre-commit 4 默认 stages=全量）
——这是特性：手动深查顺带再过一遍快闸。链仓库与报告会被 clean 删除，想
自己翻历史就分步跑 `apply` 与 `observe`。

## How It Works

**编排复用三要素**：local repo（本仓库内的本地钩子声明块）+ entry（可执行
命令）+ language: system（用当前环境跑，不另装）。

跨目录引用保持单一维护源——反模式引擎直接调 `../../10_antipattern/
detector.py`、semgrep 规则直接用 `../../12_sast_rules/rules`：规则改一处，
门禁链与 CI 同步生效。

**快重分层靠 stages**：快层钩子不写 stages（默认全量触发），重层钩子声明
`stages: [manual]`——只有 `pre-commit run --hook-stage manual` 才跑。
gitleaks 用 `protect --staged`：只扫暂存区 diff，秒级且精准。

**证据链双文件**：`blocked_evidence.txt`（阻断时的完整终端输出，含 gitleaks
判定）与 `chain_timing.json`（快/重层实测秒数 + CI 估算口径 + 达标布尔）——
验收不靠截图，靠留档文件。

## Pitfalls & Q&A

常见故障与解法：

- **`--all-files` 的边界是「所在 git 仓库」**：在链仓库外的目录跑
  `pre-commit run`，pre-commit 会找到外层仓库并把 labs、performance 等全库目录
  拉进来扫（本实验首跑真踩）。所有 pre-commit 命令必须 `cd` 进链仓库。
- **阻断演示删文件不退暂存区**：`rm` 掉工作区文件后，staged blob 还在
  index 里，`protect --staged` 会继续报红——必须 `git restore --staged`。
- **bash 3.2 两个坑**：`${PIPESTATUS[0]}` 在 set -u 下不可靠（退出码改用
  重定向文件单独取）；`$var` 紧跟多字节字符时变量名解析吞字节（一律
  `${var}`）。

Q&A：

- **重层为什么不挂 commit？** 秒级纪律：快层 0.5s 无感，重层 2.6s 起步——
  磨叽的门禁会被 `--no-verify` 绕过，快重分层保住「没人关闸」。
- **`--no-verify` 绕过本地链怎么办？** 本地链是自律工具，他律在 CI：CI
  保留同款快层检查（同一份规则），绕过本地的人会在 CI 原形毕露。
- **为什么编排复用而不是重写一遍规则？** 单一维护源：安全规则、分级表改
  一处，本地链与 CI 同时生效——两套规则迟早漂移，一套规则才叫门禁。
