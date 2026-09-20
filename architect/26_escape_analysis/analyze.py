#!/usr/bin/env python3
"""analyze.py — 逃逸缺陷分析与策略迭代：从翻车点反推策略改进，改进必须映射到真实产物。

架构师视角的一句话：**复盘的价值不在「知道为什么逃逸」，在「策略因此改了什么」**——
每个归因必须挂接一条可执行改进，且改进要能映射到一个已存在的工程产物
（本清单 architect/01-25 的工具）。映射不存在的改进是愿望，不是行动。
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path

import yaml

BASE = Path(__file__).parent
REPO = BASE.parents[1]
DIMENSIONS = {"漏测层", "环境", "数据", "时序"}


def analyze() -> tuple[list[dict], list[str]]:
    cases = yaml.safe_load((BASE / "configs/cases.yaml").read_text(encoding="utf-8"))["cases"]
    problems: list[str] = []
    for c in cases:
        if c["layer"] not in DIMENSIONS:
            problems.append(f"{c['id']}：归因维度非法（{c['layer']}）")
        if not (REPO / c["improvement"]["maps_to"]).exists():
            problems.append(f"{c['id']}：改进项映射的产物不存在（{c['improvement']['maps_to']}）")
        if not (REPO / c["lab"]).exists():
            problems.append(f"{c['id']}：取材 lab 不存在（{c['lab']}）")
    return cases, problems


def render(cases: list[dict]) -> str:
    by_layer = Counter(c["layer"] for c in cases)
    by_lab = Counter(c["lab"] for c in cases)
    lines = ["# 🔍 逃逸缺陷分析与策略迭代",
             f"> {time.strftime('%Y-%m-%d %H:%M:%S')} · 案例 {len(cases)} 个 · "
             f"归因四维：{'、'.join(DIMENSIONS)} · 全部改进项映射到 architect/ 真实产物", "",
             "## 归因分布（策略迭代的方向盘）", ""]
    for layer, n in by_layer.most_common():
        bar = "█" * n
        lines.append(f"- **{layer}**：{bar} {n} 个")
    lines += ["", "## 案例明细（每条：翻车点 → 归因 → 改进 → 映射产物）", ""]
    for c in cases:
        lines += [f"### {c['id']}：{c['title']}",
                  f"- **取材**：`{c['lab']}`　**归因**：{c['layer']}　**细节**：{c['detail']}",
                  f"- **改进**：{c['improvement']['action']}　→　映射产物：`{c['improvement']['maps_to']}`", ""]
    lines += ["## 策略迭代前后对比（一页纸）", "",
              "| 维度 | 迭代前（只开会） | 迭代后（有机制） |", "|:---|:---|:---|",
              "| UI 稳定性 | 改版全红靠人修 | 自愈策略链 + 档案（ESC-01） |",
              "| 并发/锁 | 上线才知道 | 故障注入常态化（ESC-02） |",
              "| flaky | 重跑掩盖 | 检测隔离+摘牌闭环（ESC-03） |",
              "| 边界覆盖 | 看总覆盖率 | 增量卡点 + 生成评测（ESC-04） |",
              "| 数据治理 | 各造各的 | 命名空间+生命周期（ESC-05） |",
              "| 快照纪律 | 无评审直接 update | 门禁拦截（ESC-06） |",
              "| 接口兼容 | 事后补救 | 版本矩阵发布拦截（ESC-07） |",
              "| 容量 | 空库跑个分 | 流量建模+实测结论（ESC-08） |",
              "| 配置 | 出事才对 | 漂移检测常态（ESC-09） |",
              "| 失败管理 | 人肉排查 | 聚类+先修排序（ESC-10） |", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="逃逸缺陷分析与策略迭代")
    ap.add_argument("--out", default=str(BASE / "reports"))
    args = ap.parse_args()

    cases, problems = analyze()
    if problems:
        print("❌ 分析失败：")
        for p in problems:
            print(f"  - {p}")
        return 1

    md = render(cases)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "escape_analysis.md").write_text(md, encoding="utf-8")
    (out / "escape_analysis.json").write_text(json.dumps(
        {"cases": cases, "layer_distribution": dict(Counter(c["layer"] for c in cases))},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(md)
    print(f">>> 验收：{len(cases)} 案例全归因 ✅ 改进项全部映射到真实产物 ✅ 迭代对比页已生成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
