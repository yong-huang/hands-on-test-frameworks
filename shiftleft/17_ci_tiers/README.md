# 17 · CI 左移分层与反馈预算：给流水线装上秒表

> 所有检查挤一个 job 串行跑——一个 F401 让后面全部白等，还没人知道每层
> 花了多久。本实验把左移检查编排成三层流水线（快层 → 安全层 → 接口层）：
> needs 链失败短路、每层带预算、耗时写进 job summary 报表；真 GitHub
> Actions YAML 过 actionlint，本地模拟器（读同一份 YAML）实测全绿与短路
> 两条路径——配置即真相，双引擎同源。

## Background

之前的做法：CI（持续集成，代码合并前自动跑检查的机制）一个 job 从 lint
跑到接口测试，串行全量；挂了只有一个红叉，分不清哪层慢、哪层先坏。

痛点的核心是**分层没有预算就没有纪律**：左移检查（shift-left：把上线前才
做的检查提前到开发/提 Pull Request 阶段）全靠三层流水线落地；没有
预算与报表就退化成「什么都往快层里塞」。

本实验交付真 Actions YAML + 本地模拟器——不启动 Docker 也能验证分层、
短路、预算。

## What

CI 分层流水线是把左移检查按反馈速度分层的编排，跑在 GitHub Actions
（内置 CI：YAML 描述流水线，一个 job 是一次独立检查单元）：快层 →
安全层（SAST——静态应用安全测试，扫缺陷与密钥泄漏）→ 接口层；
`needs` 链失败短路，`timeout-minutes` 即预算，实测比对进报表。

可以把三层想成医院的分诊加科室：分诊台（快层）先拦，过了才进专科
（安全/接口），急诊丢了号（失败）专科直接不给看。但和医院不同的是，
这里的「病情等级」是 needs 链的拓扑顺序（按依赖关系排出的先后次序）——机器执行，不看人情。

双引擎：真 workflow 用 actionlint 校验；act 0.2.89（本地用 Docker 容器
真跑 CI 的开源工具）能解析三层 job，
但跑容器需 Docker daemon（本机未运行）——本地验证由模拟器承担。

![三层 needs 编排：失败短路、预算报表、双引擎同源](images/ci_tiers.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/17_ci_tiers/images/ci_tiers.html)
> （或本地打开 [`images/ci_tiers.html`](images/ci_tiers.html)）。
> 三层节点即三个 job；needs 边就是短路边界——上游红，下游全部跳过。

## When to Use

- 左移检查的 CI 落地：项目 11-13 的四道检查按层编排，项目 5 的契约测试
  做接口层。
- 预算治理：每层实测耗时进报表，防「流水线越来越慢」的熵增。
- 何时不用：单层就够的小仓库（一个 job + timeout 即可）；没有分层
  诉求时不要为了分层而分层。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 单 job 全串行 | 无短路无预算，一个红叉糊脸 | 检查项 <3 的小仓库 |
| 三层 needs（本实验） | 短路省算力，预算防熵增 | 左移检查成体系的仓库 |
| act 本地真跑 | 容器级保真，需 Docker | 有 Docker 的验证环境 |

## Quick Start

前置：仓库根 `.venv`（pyyaml/ruff/mypy/pytest/semgrep 已装）、actionlint、gitleaks
与 act（brew，apply 步自检补装）。一条命令跑完整动线：

```bash
./ci_tiers.sh   # apply → observe（校验/探活/全绿/短路）→ clean
```

注意 `clean` 会删掉 reports/ 的报表与日志；想事后核对证据就分步跑
`./ci_tiers.sh apply` 与 `./ci_tiers.sh observe`，看完再 clean。

验收①：workflow 语法与语义校验，actionlint 零告警；act 探活（`-l` 列
job，不跑容器）：

```text
>>> actionlint 零告警 ✓
Stage  Job ID    Job name               Workflow name  Workflow file  Events
0      fast      快层 lint+单测             shiftleft-pr   ci.yml         pull_request
1      security  安全层 SAST+密钥            shiftleft-pr   ci.yml         pull_request
2      api       接口层契约测试                shiftleft-pr   ci.yml         pull_request
```

验收②③（全绿路径）：三层全过、每层耗时对预算、record 步写 summary。
输出为节选（fast 层逐行；各层前有 ⏭️ uses checkout 模拟行，略；秒数为
当次实测，你的机器数字会不同）：

```text
▶️  [fast] 快层 lint+单测（预算 2min）
    ⏭️  uses actions/checkout@v4（本地模拟：工作目录即已 checkout）
    ✅ lint: All checks passed!
    ✅ types:
    ✅ tests: 1 passed in 0.01s
    ✅ record:
    耗时 0.7s / 预算 2min（达标）
……（security 层 ✅ sast / ✅ secrets 耗时 1.9s；api 层 ✅ contract 5 passed 耗时 2.3s）
===== 预算报表（job summary 模拟）=====
（以下报表数据行同步打印在控制台与 reports/summary.md）
| 层 | 结果 | 实测 | 预算 | 达标 |
|:--|:--|--:|--:|:--:|
| fast | 通过 | 0.7s | 2min | ✅ |
| security | 通过 | 1.85s | 3min | ✅ |
| api | 通过 | 2.31s | 4min | ✅ |
```

短路路径：埋 F401 的样例让快层变红——下游两层被跳过，退出码非零
（控制台与 reports/bad_run.log 节选，秒数略）：

```text
    ❌ lint: [*] 1 fixable with `--fix`.
    ❌ 失败——下游层将被短路
⏭️  [security] 跳过（依赖失败：fast）——短路生效，不浪费后层算力
⏭️  [api] 跳过（依赖失败：fast, security）——短路生效，不浪费后层算力
>>> 已按预期退出 1：埋 lint 错误后两层被短路（日志留档 reports/bad_run.log）
```

## How It Works

**needs 链就是短路边界**：security `needs: fast`、api `needs: [fast,
security]`——上游任一失败，下游在真实 CI 里自动 skipped。模拟器按同一
语义拓扑排序执行并显式打出 ⏭️ 跳过行，报表里单独成行可审计。

**预算来自 yml 的 timeout-minutes**：这是 Actions 的真实字段（超时强杀），
模拟器把它同时当「耗时预算」读——实测秒数对预算写达标列，超支 ❌ 显形。

**summary 写入走 `$GITHUB_STEP_SUMMARY`**：模拟器把它指到本地文件，
record 步真实执行并写入（reports/step_summary.md 就是证据）。

**双引擎同源**：模拟器读的就是 ci_workflow.yml 本身，改 YAML 两边同时
生效。差异三处并显式标注（checkout 由工作目录代替、auto 映射为本地规则、
gitleaks 补 --source）。

## Pitfalls & Q&A

常见故障与解法：

- **PyYAML 把标量 needs 原样给字符串**：`needs: fast` 解析成 `'fast'`，
  逐字符迭代出现「假依赖环」——归一化 `isinstance(needs, str)` 包成列表。
- **GH 表达式在本地是 bad substitution**：`${{ job.status }}` 会被 bash
  当变量展开——模拟器替换为占位符并把 `GITHUB_STEP_SUMMARY` 指到本地文件。
- **`$bcode` 紧跟全角字符时 bash 报 unbound variable**：bash 3.2 把多字节
  并进变量名——`$var` 一律 `${var}`（本系列铁律，首跑即踩）。

Q&A：

- **act 为什么不是主引擎？** 跑容器需要 Docker daemon（本机未运行）；
  `-l` 探活证明 act 0.2.89 能正确解析三层编排。有 Docker 可 `act push` 真跑。
- **预算数值怎么定？** timeout-minutes 先按经验拍（2/3/4 分钟），报表跑
  两周看实测分布再收紧——预算是治理工具不是一次性配置。
- **和 architect/10 什么关系？** 10 设计「快反馈/全量/夜间」三层蓝图；
  本实验把「左移检查进 PR」做成可执行资产——蓝图在前，落地在后。