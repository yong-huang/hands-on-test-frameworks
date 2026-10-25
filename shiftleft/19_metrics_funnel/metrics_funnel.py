#!/usr/bin/env python3
"""metrics_funnel.py —— 左移度量漏斗看板：把缺陷发现阶段分布变成可审计的漏斗。

左移率 = CI 及以前拦截的缺陷数 ÷ 总缺陷数——这个数字越大，说明越多缺陷
被拦在了生产之前。看板按七个阶段从左到右排列，每阶段列出拦截手段与数量。

用法：
    python metrics_funnel.py                       # 读 data/defects.yaml
    python metrics_funnel.py --data path/to/x.yaml # 自定义数据集
产出：reports/funnel_report.md / .json
"""
import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent

# 七个阶段从左到右；位置越靠左拦截成本越低（项目 1 已量化：5 min vs 480 min）
STAGES = ["需求评审", "设计", "编码", "提交", "CI", "测试", "生产"]
CI_INDEX = STAGES.index("CI")  # ≤ CI 索引的 = 左移拦截

BAR_WIDTH = 40


def bar(n: int, total: int) -> str:
    w = int(n / max(total, 1) * BAR_WIDTH)
    return "█" * max(w, 1) if n else "·"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data/defects.yaml"))
    args = ap.parse_args()

    defects = yaml.safe_load(Path(args.data).read_text())
    total = len(defects)
    stage_counts = Counter(d["stage"] for d in defects)
    left_shifted = sum(stage_counts.get(s, 0) for s in STAGES[:CI_INDEX + 1])
    left_rate = left_shifted / total

    print("===== 左移度量漏斗 =====\n")
    print(f"{'阶段':<8}{'拦截数':>5}  {'占比':>6}  漏斗")
    print("-" * (BAR_WIDTH + 24))
    for s in STAGES:
        n = stage_counts.get(s, 0)
        pct = f"{n / total:.0%}"
        print(f"{s:<8}{n:>5}  {pct:>6}  {bar(n, total)}")

    methods = Counter(d.get("detected_by", "未知") for d in defects)
    print(f"\n拦截手段排行：")
    for m, n in methods.most_common(5):
        print(f"  {n:>2} × {m}")

    print(f"\n左移率：{left_shifted}/{total} = {left_rate:.0%}"
          f"（CI 及以前拦截；生产逃逸 {total - left_shifted} 条）")

    by_experiment = Counter(d["experiment"] for d in defects if d.get("experiment"))
    exp_str = "、".join(f"项目 {e}×{n}" for e, n in by_experiment.most_common(5))
    print(f"前序实验贡献：{exp_str}")

    conclusion = (
        f"结论：{left_rate:.0%} 的缺陷在 CI 及以前被拦截（本系列实验贡献了主要拦截手段），"
        f"生产逃逸 {total - left_shifted} 条——每一条都对应一个未建闸的盲区。"
    )
    print(f"\n{conclusion}")

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "total": total, "left_shifted": left_shifted,
               "left_rate": round(left_rate, 4),
               "stage_counts": dict(stage_counts),
               "defects": defects}
    (out / "funnel_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    md = [f"# 左移度量漏斗（{payload['generated_at']}）\n",
          f"| 阶段 | 拦截数 | 占比 |", "|:--|--:|--:|"]
    md += [f"| {s} | {stage_counts.get(s, 0)} | {stage_counts.get(s, 0) / total:.0%} |"
           for s in STAGES]
    md += [f"\n**左移率 {left_rate:.0%}**（CI 及以前拦截 {left_shifted}/{total}）\n",
           f"\n{conclusion}"]
    (out / "funnel_report.md").write_text("\n".join(md))
    print(f"产物：reports/funnel_report.md、reports/funnel_report.json")


if __name__ == "__main__":
    main()
