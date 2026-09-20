#!/usr/bin/env python3
"""strategy.py — 风险驱动的测试策略生成器。

架构师视角的一句话：**测试不可能穷尽，测多少由风险说了算，而风险必须算得出来。**
本工具回答三个问题：
  1. 排序——哪些功能风险最高？（重要性 × 失效概率，1-25 分制）
  2. 策略——每个等级该测什么层、什么用例类型、什么准出标准？（规则在 risk_matrix.yaml）
  3. 缺口——目标策略对照现有用例资产（labs/），差在哪几层？

方法论对应面试标准答题链：
  需求分析 → 范围/目标/退出标准 → 风险识别（本工具的核心）→ 分层设计 → 准出门禁

用法：
  python strategy.py                                    # 默认输入 configs/，输出 reports/
  python strategy.py --features reports/features_mutated.yaml   # 用变异后的输入重跑
产物：
  reports/strategy.json / strategy.md（风险总览 + 分级策略 + 缺口分析 + 方法说明）
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import yaml

# labs/NN 前缀 → 层级（与 architect/01 的分层口径一致，单一事实源原则下的复制品：
# 跨 lab 引用是静态映射，不需要真跑一次审计）
LAB_LAYER = (
    [(f"labs/{n:02d}", "unit") for n in range(1, 11)]
    + [(f"labs/{n:02d}", "integration") for n in (11, 12, 13, 14, 15)]
    + [(f"labs/{n:02d}", "e2e") for n in (16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 28)]
)


def lab_layer(entry: str) -> str | None:
    prefix = re.match(r"^labs/(\d{2})", entry)
    if not prefix:
        return None
    n = int(prefix.group(1))
    for known, layer in LAB_LAYER:
        if int(known.split("/")[1]) == n:
            return layer
    return None


# ---------------------------------------------------------------- 打分
def score_feature(f: dict, matrix: dict) -> dict:
    """风险 = 重要性(影响) × 失效概率(频率+缺陷加成，变更放大，封顶)。"""
    freq = matrix["scale"]["freq"][f["freq"]]
    impact = matrix["scale"]["impact"][f["impact"]]
    churn = matrix["scale"]["churn"][f["churn"]]
    prob_cfg = matrix["probability"]
    boost = min(f.get("defects_90d", 0) * prob_cfg["defect_boost_per_case"], prob_cfg["defect_boost_cap"])
    lo, hi = prob_cfg["clamp"]
    probability = min(max(round((freq + boost) * churn, 1), lo), hi)
    importance = impact
    risk = round(importance * probability)

    band = "P3"
    for name in ("P0", "P1", "P2", "P3"):        # 从高到低匹配等级带
        if risk >= matrix["bands"][name]["min"]:
            band = name
            break
    return {
        "id": f["id"], "name": f["name"], "desc": f.get("desc", ""),
        "importance": importance, "probability": probability, "risk": risk, "band": band,
        "freq": f["freq"], "impact": f["impact"], "churn": f["churn"],
        "defects_90d": f.get("defects_90d", 0),
    }


def apply_policy(scored: dict, matrix: dict) -> dict:
    """等级 → 测试层级 / 用例类型 / 优先级 / 准出标准 + 现有资产缺口。"""
    policy = matrix["band_policy"][scored["band"]]
    target_layers = policy["layers"]
    covered: dict[str, list[str]] = {ln: [] for ln in matrix["layer_names"]}
    for entry in scored.pop("covered_by", []):
        layer = lab_layer(entry)
        if layer:
            covered[layer].append(entry)

    gaps = [matrix["layer_names"][ln] for ln in target_layers if not covered[ln]]
    scored.update({
        "layers": [matrix["layer_names"][ln] for ln in target_layers],
        "case_types": policy["case_types"],
        "priority": policy["priority"],
        "exit_criteria": policy["exit_criteria"],
        "existing": {ln: v for ln, v in covered.items() if v},
        "gaps": gaps,
        "new_feature": scored["desc"].startswith("迭代新增"),
    })
    return scored


# ---------------------------------------------------------------- 报告渲染
def render_md(rows: list[dict], matrix: dict) -> str:
    total = len(rows)
    counts = {b: sum(1 for r in rows if r["band"] == b) for b in ("P0", "P1", "P2", "P3")}
    gap_rows = [r for r in rows if r["gaps"]]
    lines = [
        "# 🎯 风险驱动的测试策略（订单应用 vNext）",
        f"> 生成于 {time.strftime('%Y-%m-%d %H:%M:%S')} · 输入 {total} 个功能 · "
        f"风险模型：重要性×失效概率（25 分制）· 等级带 "
        + " / ".join(f"{b}≥{matrix['bands'][b]['min']}" for b in ("P0", "P1", "P2", "P3")),
        "",
        "## 风险总览（测多少，先看这张表）",
        "",
        "| 功能 | 重要性 | 失效概率 | 风险分 | 等级 | 测试层级 | 优先级 |",
        "|:---|---:|---:|---:|:---:|:---|:---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['name']} | {r['importance']} | {r['probability']} | {r['risk']} | {r['band']} "
            f"| {' + '.join(r['layers']) if r['layers'] else '不设门禁，探针兜底'} | {r['priority']} |"
        )
    lines += ["", f"> 分布：{' · '.join(f'{b}×{n}' for b, n in counts.items())}。"
              "P0=阻塞发布，P1=随版本必测，P2=主路径抽样，P3=不测但右移兜底。", ""]

    lines += ["## 策略明细（按等级与风险分排序）", ""]
    for r in rows:
        lines.append(f"### [{r['band']}·{r['risk']}分] {r['name']}" + ("（迭代新增）" if r["new_feature"] else ""))
        lines.append(f"- **打分依据**：重要性 {r['importance']}（impact={r['impact']}）× "
                     f"失效概率 {r['probability']}（freq={r['freq']}, 缺陷 {r['defects_90d']} 个, churn={r['churn']}）——{r['desc']}")
        if r["layers"]:
            lines.append(f"- **测试层级**：{' + '.join(r['layers'])}")
            for ln, ct in r["case_types"].items():
                lines.append(f"  - {matrix['layer_names'][ln]}：{ct}")
        else:
            lines.append("- **测试层级**：不投入用例（低频低影响），靠生产探针兜底")
        lines.append("- **准出标准**：" + "；".join(r["exit_criteria"]))
        if r["existing"]:
            lines.append("- **现有资产**：" + "、".join(
                f"{ln}（{'、'.join(v)}）" for ln, v in r["existing"].items()))
        lines += ["" if not r["gaps"] else f"- **⚠️ 策略缺口**：{'、'.join(r['gaps'])}层无任何现有用例", ""]

    lines += [f"## 缺口分析（{len(gap_rows)} 个功能存在目标与资产的落差）", "",
              "| 功能 | 等级 | 目标层级 | 缺口 |", "|:---|:---:|:---|:---|"]
    for r in gap_rows:
        lines.append(f"| {r['name']} | {r['band']} | {' + '.join(r['layers']) or '—'} | {'、'.join(r['gaps'])} |")
    lines += [
        "", "## 方法说明（面试可讲：测多少怎么决定）",
        "",
        "1. **需求分析**：功能清单 + 每功能的频率/影响/缺陷史/变更率四项输入（需求文档、缺陷库、git churn 都拿得到）；",
        "2. **风险识别**：重要性=失败影响定级；失效概率=(基础频率+历史缺陷加成)×变更放大，封顶 5——"
        "「高频但无关紧要」与「低频但一挂就死」被两个因子分开，不会糊成一个数；",
        "3. **分层设计**：等级带映射到测试层级与用例类型（P0 三层全覆盖、P1 双层、P2 单层、P3 不测）；",
        "4. **退出标准**：每等级给可门禁的准出语言（覆盖率阈值/必过集/逃逸率），策略直接变成流水线规则。",
        "",
        "> 规则全部在 `configs/risk_matrix.yaml`：改打分参数或等级策略，重跑即得新策略——"
        "**策略是推导出来的，不是抄来的**。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="风险驱动的测试策略生成器")
    base = Path(__file__).parent
    ap.add_argument("--features", default=str(base / "configs/features.yaml"))
    ap.add_argument("--matrix", default=str(base / "configs/risk_matrix.yaml"))
    ap.add_argument("--out", default=str(base / "reports"))
    args = ap.parse_args()

    features = yaml.safe_load(Path(args.features).read_text(encoding="utf-8"))["features"]
    matrix = yaml.safe_load(Path(args.matrix).read_text(encoding="utf-8"))

    rows = [apply_policy(score_feature(f, matrix) | {"covered_by": f.get("covered_by", [])}, matrix)
            for f in features]
    rows.sort(key=lambda r: (-r["risk"], r["name"]))          # 风险分降序

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "strategy.json").write_text(
        json.dumps({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "features": rows,
                    "distribution": {b: sum(1 for r in rows if r["band"] == b)
                                     for b in ("P0", "P1", "P2", "P3")}},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    md = render_md(rows, matrix)
    (out / "strategy.md").write_text(md, encoding="utf-8")
    print(md)
    print(f">>> 策略已写入 {out/'strategy.md'} 与 {out/'strategy.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
