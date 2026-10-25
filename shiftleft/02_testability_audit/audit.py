#!/usr/bin/env python3
"""audit.py —— 需求可测性审计器：在需求进编码前，量化每个用户故事「能不能被测试」。

规则即配置（configs/rules.yaml）：五类检测器（歧义词 / 可观察预期 / 可自动化线索 /
依赖 / 多行为连接）+ 两个结构性封顶（无验收条件、故事过大）。评分模型：

    score = 100 − Σ 扣分（下限 0）
    无验收条件 → 封顶 40；验收条件 > max_acs → 封顶 55（先拆分再谈测试）
    分档：≥80 良好 | 60-79 需修订 | <60 不可测（打回重写）

用法：
    python audit.py                          # 审计全部样例故事
    python audit.py --story US-B1            # 单条深看：全部违规明细与改写建议
    python audit.py --gate                   # 评审门禁：存在"不可测"则退出码 1
    python audit.py                          # 默认：规则分 + LLM 语义分双引擎
    python audit.py --no-ai                  # 跳过 AI（CI/离线）
产出：reports/testability_report.md / .json
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent

# 每类违规的改写建议（{word}/{max} 为占位符）；改写建议是本工具的核心产出——
# 只报"不合格"不给改法的需求审计，在评审会上推不动任何修改。
SUGGESTIONS = {
    "vague_word": "把「{word}」换成可断言的量化指标，例如：p95 ≤ 500ms、错误率 < 0.1%",
    "no_observable": "补一个可观察的预期值：具体数字、状态码或终态（如返回 200、列表为空）",
    "no_automation": "写明被测入口（调用哪个接口 / 操作哪个字段），让测试知道从哪里驱动",
    "dependency": "去掉对其他故事的依赖：本条应在单独交付时也成立，否则合并进被依赖的故事",
    "connector": "一条验收条件只说一件事：把「{word}」前后的行为拆成两条",
    "too_many": "验收条件超过 {max} 条：按业务对象拆分为多个故事，每个 1-5 条",
    "empty_acs": "验收条件为空：至少写出 1 条可观察、可断言的验收条件，否则无法进入开发",
}


class RuleEngine:
    """读入规则配置，对单个用户故事输出（分数, 档位, 违规明细）。"""

    def __init__(self, rules: dict):
        self.r = rules
        self.good = rules["thresholds"]["good"]
        self.reject = rules["thresholds"]["reject"]
        self.max_acs = rules["thresholds"]["max_acs"]

    def _finding(self, rule: str, ac: int | None, detail: str, **fmt) -> dict:
        return {"rule": rule, "ac": ac, "detail": detail,
                "deduction": self.r["deductions"][rule],
                "suggestion": SUGGESTIONS[rule].format(**fmt, max=self.max_acs)}

    def tier_of(self, score: int) -> str:
        """分档映射单独成方法：audit_story 用它，单测对边界值直测它。"""
        return "良好" if score >= self.good else ("需修订" if score >= self.reject else "不可测")

    def audit_story(self, story: dict) -> dict:
        d = self.r["deductions"]
        acs = story.get("acceptance_criteria") or []
        findings: list[dict] = []

        if not acs:
            findings.append(self._finding("empty_acs", None, "验收条件为 0 条"))

        for i, raw in enumerate(acs, start=1):
            text = " ".join(str(raw).split())
            for w in self.r["vague_words"]:
                if w in text:
                    findings.append(self._finding("vague_word", i, f"歧义词「{w}」", word=w))
            if not any(ch.isdigit() for ch in text):
                findings.append(self._finding("no_observable", i, "无可观察预期值（不含任何数字）"))
            hints = self.r["automation_hints"]
            if not any(h.lower() in text.lower() for h in hints):
                findings.append(self._finding("no_automation", i, "无可自动化线索（未提接口/字段/输入输出）"))
            for w in self.r["dependency_words"]:
                if w in text:
                    findings.append(self._finding("dependency", i, f"依赖词「{w}」", word=w))
            for w in self.r["connector_words"]:
                if w in text:
                    findings.append(self._finding("connector", i, f"连接词「{w}」", word=w))

        if len(acs) > self.max_acs:
            findings.append(self._finding(
                "too_many", None, f"验收条件 {len(acs)} 条，超出单故事上限 {self.max_acs} 条"))

        score = max(0, 100 - sum(f["deduction"] for f in findings))
        if not acs:                       # 结构性封顶：没有可断言的东西
            score = min(score, 40)
        if len(acs) > self.max_acs:       # 结构性封顶：故事过大，先拆分
            score = min(score, 55)
        tier = self.tier_of(score)
        return {"id": story["id"], "title": story["title"], "n_acs": len(acs),
                "score": score, "tier": tier, "findings": findings}


def w(s: str, width: int) -> str:  # 中文按 2 列宽对齐（终端汉字占两格）
    pad = width - sum(2 if ord(c) > 0x2E7F else 1 for c in str(s))
    return str(s) + " " * max(pad, 1)


def print_report(results: list[dict], engine: RuleEngine, only: str | None):
    print(f"{'ID':<8}{'标题':<24}{'AC':>3}{'分数':>5}  档位")
    for r in results:
        print(f"{w(r['id'], 8)}{w(r['title'], 24)}{r['n_acs']:>3}{r['score']:>5}  {r['tier']}")
    shown = [r for r in results if r["tier"] != "良好"
             and (only is None or r["id"] == only)]
    for r in shown:
        print(f"\n⛔ {r['id']} {r['title']}（{r['score']} 分，{r['tier']}）")
        for f in r["findings"]:
            loc = f"AC{f['ac']}" if f["ac"] else "结构"
            print(f"  ⛔ [{loc}] {f['detail']}（−{f['deduction']}）")
            print(f"     ↳ 改写建议：{f['suggestion']}")
    tiers = [r["tier"] for r in results]
    print(f"\n汇总：良好 {tiers.count('良好')} / 需修订 {tiers.count('需修订')} / "
          f"不可测 {tiers.count('不可测')}（共 {len(results)} 条）")
    print(f"评分口径：score = 100 − Σ扣分；无 AC 封顶 40，AC>{engine.max_acs} 封顶 55；"
          f"档位线 {engine.good}/{engine.reject}")


def save_reports(results: list[dict], engine: RuleEngine, out_dir: Path):
    out_dir.mkdir(exist_ok=True)
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "formula": "score = 100 - sum(deductions); no-AC cap 40; "
                          f"over-{engine.max_acs}-ACs cap 55; tiers {engine.good}/{engine.reject}",
               "stories": results}
    (out_dir / "testability_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2))
    with (out_dir / "testability_report.md").open("w") as f:
        f.write(f"# 需求可测性审计报告（{payload['generated_at']}）\n\n"
                f"| ID | 标题 | AC | 分数 | 档位 |\n|:--|:--|--:|--:|:--|\n")
        for r in results:
            f.write(f"| {r['id']} | {r['title']} | {r['n_acs']} | {r['score']} | {r['tier']} |\n")
        for r in results:
            if r["tier"] == "良好":
                continue
            f.write(f"\n## {r['id']} {r['title']}（{r['score']} 分）\n")
            for x in r["findings"]:
                loc = f"AC{x['ac']}" if x["ac"] else "结构"
                f.write(f"- [{loc}] {x['detail']}（−{x['deduction']}）→ {x['suggestion']}\n")


def _run_ai_comparison(stories: list[dict], results: list[dict]):
    """AI 双引擎对比：规则分 vs LLM 语义分，差异可见即价值。"""
    try:
        from ai_engine import assess_story
    except ImportError:
        print("\n⚠️ ai_engine.py 不存在，AI 对比跳过")
        return

    print("\n===== AI 双引擎对比（规则层 + LLM 语义层）=====")
    print(f"{'ID':<8}{'标题':<20}{'规则分':>6}{'AI分':>6}{'差异':>6}  AI 要点")
    print("-" * 78)

    for story, rule_result in zip(stories, results):
        ai = assess_story(story)
        if ai.get("score") is None:
            print(f"{story['id']:<8}{story['title']:<20}{'—':>6}{'—':>6}{'—':>6}  "
                  f"⚠️ {ai.get('error', '未知错误')}")
            continue
        ai_score = ai["score"]
        diff = ai_score - rule_result["score"]
        delta = f"{diff:+d}" if diff else "= "
        top = ""
        if ai["findings"]:
            f0 = ai["findings"][0]
            top = f0.get("issue", "")[:36]
        elif ai_score >= 80:
            top = "AI 确认可测"
        print(f"{story['id']:<8}{story['title']:<20}{rule_result['score']:>6}{ai_score:>6}{delta:>6}  {top}")

    print(f"\n差异解读：规则分与 AI 分接近 → 两层一致（高置信）；差异大 → "
          f"规则层有盲区或 AI 误判，人工复核后可补规则。")


def main():
    ap = argparse.ArgumentParser(description="需求可测性审计器")
    ap.add_argument("--stories", default=str(ROOT / "configs/stories.yaml"))
    ap.add_argument("--rules", default=str(ROOT / "configs/rules.yaml"))
    ap.add_argument("--story", default=None, help="只深看指定故事 ID 的全部违规明细")
    ap.add_argument("--gate", action="store_true",
                    help="评审门禁模式：存在「不可测」故事则退出码 1")
    ap.add_argument("--no-save", action="store_true", help="不写 reports/ 产物")
    ap.add_argument("--no-ai", action="store_true",
                    help="跳过 AI 语义评估（CI/离线用；默认调本地 Ollama qwen3.8）")
    args = ap.parse_args()

    rules = yaml.safe_load(Path(args.rules).read_text())
    stories = yaml.safe_load(Path(args.stories).read_text())["stories"]
    engine = RuleEngine(rules)
    results = [engine.audit_story(s) for s in stories]

    if args.story:
        hit = next((r for r in results if r["id"] == args.story), None)
        if hit is None:
            sys.exit(f"未找到故事 {args.story}")
        results = [hit]
    print_report(results, engine, only=args.story)
    if not args.no_save and not args.story:
        save_reports(results, engine, ROOT / "reports")
        print("产物：reports/testability_report.md、reports/testability_report.json")
    if not args.no_ai:
        _run_ai_comparison(stories, results)

    if args.gate and any(r["tier"] == "不可测" for r in results):
        print("门禁判定：存在不可测故事，需求打回（exit 1）")
        sys.exit(1)


if __name__ == "__main__":
    main()
