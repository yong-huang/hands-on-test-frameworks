# 11 · 静态分析分级门禁：error 拦在门外，warning 记在账上

> linter（静态检查代码、批量报出问题清单的工具）报出来的每一项都要修吗？
> 不——该不该阻断是团队决策。本实验给 ruff（Python 代码检查工具，查风格
> 与常见缺陷）+ mypy（Python 类型检查器，查注解与代码是否相符）做一个
> 分级门禁的统一入口 `gate.py`：发现按配置表分级，
> error 级阻断（exit 1）、warning 级放行但记录；把 F401 从 warning 升到
> error，重跑立即阻断——升降级只动配置，引擎零改动。

## Background

之前的做法：CI（持续集成，代码合并前自动跑检查的服务）里挂一条 `ruff check`，
规则集是工具默认的——要么全阻断
（风格问题也拦合并，团队很快学会绕过门禁），要么只出报告没人看。

痛点的核心是**「发现的严重度」和「处置的力度」没有对齐**：类型错误和
行长超限在默认门禁里是同一种待遇。门禁失效不是因为规则不好，是因为
分级权不在团队手里。

本实验把分级做成配置表：error（阻断）/ warning（放行记录）两档、
ruff 与 mypy 统一编目（`mypy:` 前缀），升降级 = 改一张表。

## What

静态分析（不运行代码、只扫描源码的检查方式）分级门禁是一个统一入口：跑
ruff 与 mypy、把全部发现按团队分级表
归类，error 级阻断（exit 1）并逐条给出规则码，warning 级放行但写进报告。

可以把分级表想成医院的分诊台：挂号病人（发现）按病情分急诊（error，
立刻处理）与门诊（warning，记录随访）。但和分诊不同的是，病情等级不是
医生现场判断，而是团队事先写在表里的治理决策——表改了，分诊结果立即变。

分级表（默认档）与 fixtures（预先写好的样例代码，专门用来触发各类发现）的
对应关系：

| fixture | 发现 | 级别 |
|:--|:--|:--|
| bad_type.py | mypy:return-value（返回类型不符） | ⛔ error |
| bad_bug.py | B006 可变默认值 / F821 未定义名 | ⛔ error |
| bad_bug.py | E711 与 None 比较 | ⚠️ warning |
| bad_style.py | E501 超长行 / F401 未用导入 | ⚠️ warning |

![ruff+mypy 发现经分级表分流：error 阻断、warning 放行、升降级即改表](images/static_gate.svg)

> 🌐 **交互版**：[在线打开（GitHub Pages）](https://yong-huang.github.io/hands-on-test-frameworks/shiftleft/11_static_gate/images/static_gate.html)
> （或本地打开 [`images/static_gate.html`](images/static_gate.html)）。
> 引擎只认表不认死规则——右侧两条出口由左侧配置决定。

## When to Use

- 团队级静态门禁落地：error/warning 分级让门禁「拦得住真问题、烦不到人」。
- 规则治理：升降级走配置 diff 评审，分级历史可追溯（本系列项目 14「pre-commit
  本地门禁链」会复用，见 docs/shiftleft.md）。
- 何时不用：只有几个人的早期项目，全量 warning 报表足矣；门禁分级需要
  团队对「什么必须拦」先有共识。

同类方案对比：

| 方案 | 差异 | 什么时候选它 |
|:---|:---|:---|
| 工具默认门禁 | 全阻断或全放行，无分级 | 一次性脚本仓库 |
| 本实验（配置分级） | 团队决策驱动，升降级即改表 | 有共识要落地的团队 |
| 商用质量平台 | 报表丰富，治理逻辑黑盒 | 预算充足的大团队 |

## Quick Start

前置：仓库根 `.venv`，ruff 与 mypy 已装入（缺则 `pip install ruff mypy`；
apply 步自检并补装）。一条命令跑完整动线：

```bash
./static_gate.sh   # apply → observe（拦截/放行/升降级三连）→ clean
```

第一段，全量 fixtures：四个 error 级发现逐条给出规则码，阻断——

```text
静态门禁（分级表：gate_rules.toml）——error 4 / warning 4
  ⛔ 阻断 [error] bad_bug.py:4 B006  Do not use mutable data structures for argument defa
……（中间省略 5 条：E711、F821、两条 E501、mypy:name-defined）
  ⚠️ 放行 [warning] bad_style.py:3 F401  `os` imported but unused
  ⛔ 阻断 [error] bad_type.py:6 mypy:return-value  Incompatible return value type (got "str", expected
⛔ 门禁判定：4 个 error 级发现（规则码 B006, F821, mypy:name-defined, mypy:return-value），阻断（exit 1）
……（clean 文件单独跑为「零发现，放行 exit 0」）
```

升降级三连：同一份 bad_style.py，改配置不改引擎——

```text
默认档（F401=warning）→ ✅ 放行（exit 0）
严格档（F401 升 error）→ ⛔ 1 个 error 级发现（规则码 F401），阻断（exit 1）
回默认档（降级恢复）  → ✅ 放行（exit 0）
```

诚实预期：升降级的「立即生效」来自引擎每次重读配置；分级表本身需要团队
评审——本实验只证明机制，不替你决定 F401 该不该拦。

## How It Works

**两个工具、一种编目**：ruff 走 `--output-format json`（结构化解析规则码），
mypy 走文本解析（`--show-error-codes` 输出尾码），统一成
`{tool, code, loc, msg}` 后按表分级——mypy 的码加 `mypy:` 前缀与 ruff 码区分。

不同 mypy 版本对错误码的打印格式可能不同（带或不带 `mypy:` 前缀），解析时
先 `removeprefix("mypy:")` 再统一补 `mypy:` 前缀——两种格式都查得上同一张表
（本实验 2.4.0 实测输出裸码，该防御不改变行为，只保兼容）。

**分级是纯查表**，所以升降级零逻辑改动：

```python
def classify(code: str, tiers: dict) -> str:
    if code in tiers["error"]["ruff"] or code in tiers["error"]["mypy"]:
        return "error"
    if code in tiers["warning"]["ruff"] or code in tiers["warning"]["mypy"]:
        return "warning"
    return "warning(未分级)"          # 新规则码默认放行，治理上先观察后定级
```

**警告也要留档**：放行 ≠ 丢弃——warning 全量写进 `reports/static_gate.json`，
分级治理的下一步（观察 → 升级）靠这份账。三类 fixture 的命中即台账初稿。

## Pitfalls & Q&A

常见故障与解法：

- **mypy 错误码查不到分级表**：若你的 mypy 版本把码打印成
  `[mypy:return-value]`，直接查表会落空——解析时先 `removeprefix("mypy:")`
  再统一补 `mypy:` 前缀，两种打印格式都兼容。
- **mypy 默认不查无注解函数体**：坏 fixture 若不带类型注解，mypy 静默通过。
  要么给 fixture 加注解，要么引擎加 `--check-untyped-defs`——本实验选择
  前者（fixture 即示范代码，本该带注解）。
- **管道后的 `$?`（上一条命令的退出码）是 tail 的，恒为 0**：调试门禁退出码
  要么不用管道、要么开 `set -o pipefail` 让管道返回门禁自身的退出码——本
  脚本已开，严查档那步因预期 exit 1 补了 `|| true` 防脚本中断。

Q&A：

- **warning 级发现越积越多怎么办？** 报告 JSON 就是台账：定期评审，把该
  拦的升级、已修复的下线——分级表是活的治理文档，不是一次性配置。
- **「未分级」的新规则码为什么默认放行？** 新工具/新规则先观察影响面再
  定级，避免升级潮；`warning(未分级)` 的标注让它们在报告里显眼。
- **ruff 与 mypy 的规则码会撞吗？** 不会：ruff 是字母+数字（B006），
  mypy 一律 `mypy:` 前缀，配置表里两个清单天然隔离。
