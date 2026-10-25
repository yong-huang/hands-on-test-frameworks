#!/usr/bin/env python3
"""example_mapping.py —— Example Mapping 工作台：把三色卡片转成 Gherkin 骨架与疑问清单。

Example Mapping（三 amigos 协作法）：评审一个故事时用三种卡片拆解——
蓝卡=业务规则、绿卡=每条规则的具体例子、红卡=答不上来的疑问（未决问题）。
本工具把「蓝卡→场景大纲、绿卡→Examples 表、红卡→待认领问题清单」的转化自动化，
产出能被官方 gherkin 解析器校验的 feature 骨架——语义精修是三 amigos 的事，
本工具保证"结构合法、例子不丢、疑问不漏"。

检测三类未完成状态并告警：空规则（蓝卡没写字）、无例子（绿卡缺失）、
例子列名不一致（同一规则内的例子必须共用列名，才能组成 Examples 表）。

用法：
    python example_mapping.py --story configs/story_clean.yaml
    python example_mapping.py --story configs/story_dirty.yaml --strict   # 有告警退出码 1
产出：reports/<story-id>.feature + reports/<story-id>-questions.md
"""
import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
STEP_KEYWORDS = ["假如", "当", "那么", "并且", "而且"]  # 步骤关键词按列循环分配


def esc(cell: str) -> str:
    """Gherkin 表格单元格转义：竖线与换行是表格结构字符，必须处理。"""
    return " ".join(str(cell).split()).replace("|", "\\|")


def build_feature(story: dict, rules: list):
    """三色卡片 → feature 文本 + 告警列表。（纯函数：单测与 CLI 共用）"""
    warnings = []
    lines = ["# language: zh-CN", f"功能: {story['title']}", f"  {story.get('goal', '')}", ""]
    for rule in rules:
        text = " ".join(str(rule.get("text", "")).split())
        if not text:
            warnings.append(f"空规则 [{rule.get('id', '?')}]：蓝卡没写字，已跳过不进 feature——"
                            "先回 Example Mapping 把规则写出来")
            continue
        examples = rule.get("examples") or []
        rid = rule.get("id", "")
        if not examples:
            warnings.append(f"无例子 [{rid} {text}]：绿卡缺失——没有例子的规则无法翻译成测试，"
                            "场景骨架里留了待补占位")
            lines += [f"  场景: {rid} {text}",
                      "    那么 (TODO) 例子待补：回到 Example Mapping 补绿卡", ""]
            continue
        cols = list(examples[0].keys())
        for k, ex in enumerate(examples[1:], start=2):
            if list(ex.keys()) != cols:
                warnings.append(f"列名不一致 [{rid}] 第 {k} 条例子 {list(ex.keys())} "
                                f"≠ 第 1 条 {cols}——以第 1 条为准，不一致的键已丢弃")
        lines.append(f"  场景大纲: {rid} {text}")
        for i, col in enumerate(cols):
            lines.append(f"    {STEP_KEYWORDS[i % len(STEP_KEYWORDS)]} <{esc(col)}>")
        lines += ["", "    例子:", "      | " + " | ".join(esc(c) for c in cols) + " |"]
        for ex in examples:
            lines.append("      | " + " | ".join(esc(ex.get(c, "")) for c in cols) + " |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", warnings


def build_questions(story: dict, questions: list) -> str:
    """红卡 → 待认领问题清单：逐条带 owner 与状态，评审会现场认领。"""
    qs = questions or []
    out = [f"# 未决问题清单 · {story['id']} {story['title']}", "",
           "评审会上逐条认领：填 Owner、改状态，全部 closed 才能进迭代。", "",
           "| # | 问题 | Owner | 状态 |", "|--:|:--|:--|:--|"]
    for i, q in enumerate(qs, start=1):
        out.append(f"| {i} | {q.get('q', '')} | {q.get('owner', '待定')} | {q.get('status', 'open')} |")
    if not qs:
        out.append("| - | （本故事无未决问题） | - | - |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Example Mapping 工作台")
    ap.add_argument("--story", required=True, help="三色卡片 YAML 路径")
    ap.add_argument("--out", default=str(ROOT / "reports"))
    ap.add_argument("--strict", action="store_true", help="存在告警则退出码 1（评审门禁）")
    args = ap.parse_args()

    doc = yaml.safe_load(Path(args.story).read_text())
    story = doc["story"]
    rules = doc.get("rules") or []
    questions = doc.get("questions") or []
    feature, warnings = build_feature(story, rules)
    qmd = build_questions(story, questions)

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    fpath = out / f"{story['id']}.feature"
    qpath = out / f"{story['id']}-questions.md"
    fpath.write_text(feature)
    qpath.write_text(qmd)

    print(f"[Example Mapping] {story['id']} {story['title']}："
          f"{len(rules)} 条规则 / "
          f"{sum(len(r.get('examples') or []) for r in rules)} 个例子 / "
          f"{len(questions)} 个疑问")
    for w in warnings:
        print(f"  ⚠️ {w}")
    print(f"产物：{fpath.relative_to(ROOT)}（待 gherkin 解析校验）、{qpath.relative_to(ROOT)}")
    if warnings and args.strict:
        print("strict 模式：存在未完成卡片，故事不能进迭代（exit 1）")
        sys.exit(1)


if __name__ == "__main__":
    main()
