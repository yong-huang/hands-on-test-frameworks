#!/usr/bin/env python3
"""cost_funnel.py —— 缺陷成本漏斗引擎：把同一个缺陷放进六个关卡，量出拦截成本。

做法：逐个真实运行 gates/gateN_*.py 检测器并计时（自动化时长是实测值，
不是估算）；人工分钟数来自 configs/costs.yaml 的估算模型；两者合成
「该关拦截合计分钟」，并给出最左关相对最右关的杠杆倍数。

用法：
    python cost_funnel.py                # 全量：缺陷实现，6 关全部拦截
    python cost_funnel.py --impl good    # 对照组：好实现，代码关应全放行（零误报）
    python cost_funnel.py --gate 3       # 只复现第 3 关
产出：终端报告 + reports/cost_funnel.md + reports/cost_funnel.json
"""
import argparse
import json
import math
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent  # 引擎在实验根目录；gates/ 下的脚本才用 parents[1]
GATES = {
    1: "gate1_requirements.py",
    2: "gate2_unit.py",
    3: "gate3_static.py",
    4: "gate4_api.py",
    5: "gate5_e2e.py",
    6: "gate6_production.py",
}


def run_gate(n: int, impl: str):
    """运行第 n 关检测器：返回 (结果, 实测秒, 输出文本)。结果 ∈ 拦截/放行/错误。"""
    t0 = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(ROOT / "gates" / GATES[n]), "--impl", impl],
        cwd=ROOT, capture_output=True, text=True)
    seconds = time.perf_counter() - t0
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT:")]
    if proc.returncode != 0 or not lines:
        return "错误", seconds, proc.stdout + proc.stderr
    return ("拦截" if "INTERCEPTED" in lines[-1] else "放行"), seconds, proc.stdout


def bar(total_minutes: float) -> str:
    """漏斗条形：对数刻度（各关成本差两个数量级，线性条左边会缩没了）。"""
    width = max(1, round(math.log10(max(total_minutes, 0.01)) * 12))
    return "▇" * width


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--impl", choices=["good", "bad"], default="bad",
                    help="被注入的定价实现：bad=缺陷版（默认），good=对照版")
    ap.add_argument("--gate", type=int, choices=range(1, 7), default=None,
                    help="只运行指定关卡（复现用）")
    args = ap.parse_args()

    cfg = yaml.safe_load((ROOT / "configs/costs.yaml").read_text())["gates"]
    ns = [args.gate] if args.gate else list(GATES)
    rows = []
    for g in cfg:
        if g["n"] not in ns:
            continue
        result, seconds, output = run_gate(g["n"], args.impl)
        if result == "错误":
            print(output)
            sys.exit(f"关卡 {g['n']} 运行出错")
        total_min = g["human_minutes"] + seconds / 60
        rows.append({"n": g["n"], "stage": g["stage"], "mechanism": g["mechanism"],
                     "result": result, "human": g["human_minutes"],
                     "auto_sec": round(seconds, 1), "total_min": round(total_min, 2)})
        # 检测器输出首行 = 本关在做什么；细节看单关复现，全量跑只留摘要
        first = output.strip().splitlines()[0] if output.strip() else ""
        print(f"[{g['n']}/6] {first or g['stage']} → {result}（自动化实测 {seconds:.1f}s）")

    def w(s, width):  # 中文按 2 列宽对齐（终端里汉字占两格）
        pad = width - sum(2 if ord(c) > 0x2E7F else 1 for c in str(s))
        return str(s) + " " * max(pad, 1)

    if args.gate:  # 单关复现：只出本关结论，完整漏斗看全量运行
        print("\n单关复现完成；完整成本漏斗请运行不带 --gate 的全量命令")
        return

    prod = next(r for r in rows if r["n"] == 6)
    for r in rows:
        r["leverage"] = round(prod["total_min"] / r["total_min"], 1)

    print("\n===== 缺陷成本漏斗（impl=%s）=====" % args.impl)
    print(f"{w('关卡', 5)}{w('阶段', 14)}{w('结果', 6)}{'人工min':>9} {'实测s':>7} "
          f"{'合计min':>8} {'杠杆':>8}  漏斗(条长∝log₁₀)")
    for r in rows:
        print(f"{w(r['n'], 5)}{w(r['stage'], 14)}{w(r['result'], 6)}{r['human']:>9} "
              f"{r['auto_sec']:>7} {r['total_min']:>8} {str(r['leverage']) + '×':>8}  {bar(r['total_min'])}")

    left = rows[0]
    cheapest = min(rows, key=lambda r: r["total_min"])
    print(f"\n左移杠杆：最左关（{left['stage']} {left['total_min']} 分钟）"
          f" vs 最右关（生产 {prod['total_min']} 分钟）→ {left['leverage']}×")
    print(f"拦截成本最低关：{cheapest['stage']}（合计 {cheapest['total_min']} 分钟，"
          f"比生产省 {cheapest['leverage']}×）")
    print(f"复算公式：合计分钟 = 人工分钟 + 实测自动化秒 ÷ 60；杠杆 = 生产合计 ÷ 本关合计")
    print(f"抽查示例：生产合计 = {prod['human']} + {prod['auto_sec']}/60 = {prod['total_min']}；"
          f"需求评审杠杆 = {prod['total_min']} / {left['total_min']} = {left['leverage']}")

    n_caught = sum(1 for r in rows if r["result"] == "拦截")
    print(f"拦截统计：{n_caught}/{len(rows)} 个运行关卡检出缺陷")
    if args.impl == "bad" and n_caught == len(rows):
        print("✅ 验收自检：缺陷实现被全部运行关卡拦下")
    elif args.impl == "good":
        code_gates = [r for r in rows if r["n"] >= 2]
        if all(r["result"] == "放行" for r in code_gates):
            print("✅ 对照自检：好实现在代码关全部放行（检测器零误报）；"
                  "关卡1 拦的是测试计划缺口，与实现无关")

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    report = {"generated_at": datetime.now().isoformat(timespec="seconds"),
              "impl": args.impl, "gates": rows,
              "leverage_leftmost": left["leverage"],
              "formula": "total_min = human_minutes + auto_sec/60; leverage = total_min(gate6)/total_min(gateN)"}
    (out / "cost_funnel.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2))
    with (out / "cost_funnel.md").open("w") as f:
        f.write(f"# 缺陷成本漏斗（impl={args.impl}，{report['generated_at']}）\n\n"
                f"| 关卡 | 阶段 | 结果 | 人工min(估算) | 实测s | 合计min | 杠杆× |\n"
                f"|:--:|:--|:--:|--:|--:|--:|--:|\n")
        for r in rows:
            f.write(f"| {r['n']} | {r['stage']} | {r['result']} | {r['human']} "
                    f"| {r['auto_sec']} | {r['total_min']} | {r['leverage']} |\n")
        f.write(f"\n最左关 vs 最右关杠杆：**{left['leverage']}×**\n\n"
                f"复算：合计分钟 = 人工分钟 + 实测秒÷60；杠杆 = 生产合计 ÷ 本关合计\n")
    print(f"\n产物：reports/cost_funnel.md、reports/cost_funnel.json")


if __name__ == "__main__":
    main()
