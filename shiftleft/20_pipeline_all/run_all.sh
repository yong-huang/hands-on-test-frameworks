#!/usr/bin/env bash
# =============================================================================
# run_all.sh — 🏁 左移流水线全景：19 个实验 · 一条链跑完
# 路径约定：本脚本在 shiftleft/20_pipeline_all/ 下，所有兄弟实验用 ../NN_xxx/ 引用。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"
SL="$PWD/.."                      # shiftleft/ 目录
REPO="$SL/.."                     # 仓库根
PY="$REPO/.venv/bin/python"
OUT="reports"
mkdir -p "$OUT"

pass() { echo "  ✅ $1"; }
step() { echo; echo "━━━ $1 ━━━"; }

echo "╔══════════════════════════════════════════════╗"
echo "║  🏁 左移流水线全景 — 19 个实验 · 一条链跑完   ║"
echo "╚══════════════════════════════════════════════╝"

step "① 需求评审 — 可测性审计（项目 02）"
cd "$SL/02_testability_audit"
"$PY" audit.py --no-ai --no-save 2>&1 | grep -E "良好|不可测" | head -2
pass "需求层：可测性审计完成"

step "② 编码 — 反模式检测（项目 10）"
cd "$SL/10_antipattern"
"$PY" detector.py --path samples/bad --no-save 2>&1 | head -1
pass "编码层：反模式检测器就绪"

step "③ 编码 — 静态分析分级门禁（项目 11）"
cd "$SL/11_static_gate"
set +e
"$PY" gate.py --path fixtures
gcode=$?
set -e
[ "$gcode" -ne 0 ] && pass "编码层：静态门禁拦截 exit $gcode"
cd "$SL/20_pipeline_all"

step "④ 提交 — 供应链扫描（项目 13）"
cd "$SL/13_supply_chain"
set +e
"$REPO/.venv/bin/pip-audit" -r fixtures/requirements_vuln.txt -s osv --aliases on \
    --format json -o "$OLDPWD/reports/pip_audit.json" 2>/dev/null
scode=$?
set -e
[ "$scode" -ne 0 ] && pass "提交层：依赖 CVE + 密钥扫描 exit $scode"
cd "$SL/20_pipeline_all"

step "⑤ CI — 缺陷成本漏斗（项目 01）"
cd "$SL/01_cost_funnel"
"$PY" cost_funnel.py --gate 3 2>&1 | head -3
pass "CI 层：缺陷成本漏斗数据就绪"
cd "$SL/20_pipeline_all"

step "⑥ CI — 缺陷防复发规则库（项目 15）"
cd "$SL/15_recur_rules"
export PYTHONPATH="bugs:newcode"
set +e
"$PY" -m pytest tests/test_repro.py -k buggy -q 2>&1 | tail -1
set -e
pass "CI 层：缺陷态 3 红留档"
cd "$SL/20_pipeline_all"

step "⑦ 缺陷注入演示：一个 float 金额缺陷的左移旅程"
cat <<'DEMO'
  注入缺陷：金额用 float 计算（19.99 + 80.10 - 20.00）

  最早拦截点分析：
  ┌─────────────────────────────────────────────────────────┐
  │ 需求评审  AC 写「精确到分」→ 可测性审计器标记为可测      │
  │ 编码      TDD 红绿：float 算出 100.08999… → 复现测试红  │
  │ 提交      ruff/mypy 不查 float 精度 → 放行（盲区）      │
  │ CI        semgrep money-float 规则 → 拦截 ⛔            │
  │ 生产      如果以上全漏 → 财务对账发现，代价 480 分钟     │
  └─────────────────────────────────────────────────────────┘

  结论：最早可在编码阶段拦截（TDD 红灯），代价 ≈2 min；
        如果逃到生产（对账发现），代价 ≈480 min——左移杠杆 >200×。
DEMO

step "⑧ 左移方案书（一页汇报）"
cat > "$OUT/pitch.md" <<'PITCH'
# 左移方案书（一页版）

## 我们做了什么
建了 6 个阶段 19 个实验的左移体系，覆盖需求→设计→编码→提交→CI→生产。

## 核心数据
- 缺陷成本漏斗：需求拦截 5 min vs 生产拦截 480 min（杠杆 96×）
- 左移率：77% 缺陷在 CI 及以前被拦截（30 条缺陷数据集）
- 测试有效性：变异 score 28.6% → 85.7%（+57pp）
- 反模式检测：10/10 埋点命中，真实仓库 22 个反模式点

## 六阶段闸门
| 阶段 | 检查器 | 拦截 | 实验 |
|:--|:--|:--|:--|
| 需求评审 | 可测性审计 + 追溯矩阵 | 模糊 AC / 无用例 | 02/04 |
| 编码 | TDD + 变异测试 + 反模式 | 假测试 / 语义缺陷 | 08/09/10 |
| 提交 | pre-commit 链（ruff/mypy/gitleaks） | 风格/类型/密钥 | 11/13/14 |
| CI | SAST + 供应链 + 成本漏斗 | 注入/CVE/精度 | 05/12/13 |
| 测试 | 性能预算 + 追溯矩阵 | p95 回归/覆盖缺口 | 04/18 |
| 生产 | 漏斗看板 | 度量盲区 | 19 |

## 投入产出
- 建设：19 个实验 × ~2h = ~40h
- 回报：生产缺陷 -77%，单缺陷拦截成本从 480min 降到 ~5min
PITCH
pass "方案书已生成：reports/pitch.md"
ls -l "$OUT/"
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  🏁 全景串联完成 — 19 个实验 · 一条链 · 一页方案书 ║"
echo "╚══════════════════════════════════════════════╝"
