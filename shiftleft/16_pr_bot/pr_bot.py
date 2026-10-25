#!/usr/bin/env python3
"""pr_bot.py —— Danger 风格 PR 评审机器人：解析 unified diff，按规则表输出
结构化评审意见（本地 diff 模拟，不依赖 GitHub）。

四条规则（Danger 风格 = 评论不阻断，发现以 ⚠️ 呈现）：
  large-diff      变更行数超阈值（默认 400）——建议拆分
  missing-tests   改动了 src/ 实现却没有任何测试文件变动
  contract-drift  新增/改动 HTTP 端点但契约文件（contract/openapi）未更新
  todo-no-issue   新增 TODO/FIXME 且未关联 issue 号（#123）

用法：
    python pr_bot.py --diff diffs/pr_no_tests.diff   # 单 PR 评审
    python pr_bot.py --all                           # 五个 PR 连跑 + JSON 留档
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIFFS = ROOT / "diffs"
MAX_LINES = 400

ENDPOINT_RE = re.compile(r"^\+\s*@app\.(get|post|put|delete|patch)\(")
TODO_RE = re.compile(r"^\+.*\b(TODO|FIXME)\b")
TODO_WITH_ISSUE_RE = re.compile(r"#\d+")
CONTRACT_RE = re.compile(r"(contract[\w.-]*\.yaml|openapi[\w.-]*\.(yaml|json))", re.I)
TEST_FILE_RE = re.compile(r"(^|/)(tests?/.+|test_[^/]+\.py)$")
SRC_FILE_RE = re.compile(r"^src/.+\.py$")


def parse_diff(text: str) -> dict:
    """unified diff → {路径: {added, deleted, added_lines}}（只认 +++ b/ 行定界）。"""
    files: dict[str, dict] = {}
    cur = None
    for line in text.splitlines():
        if line.startswith("+++ b/"):
            cur = line[6:].strip()
            files.setdefault(cur, {"added": 0, "deleted": 0, "added_lines": []})
        elif line.startswith("---"):
            continue
        elif line.startswith("+") and cur:
            files[cur]["added"] += 1
            files[cur]["added_lines"].append(line)
        elif line.startswith("-") and cur:
            files[cur]["deleted"] += 1
    return files


def review(files: dict) -> list[tuple[str, str]]:
    """四条规则依次过一遍，返回 [(规则 id, 评审意见)]。"""
    findings = []
    total = sum(f["added"] + f["deleted"] for f in files.values())
    if total > MAX_LINES:
        findings.append(("large-diff",
                         f"变更 {total} 行（>{MAX_LINES}）——按关注点拆成多个 PR"))
    src_changed = [p for p in files if SRC_FILE_RE.match(p)]
    tests_changed = [p for p in files if TEST_FILE_RE.search(p)]
    if src_changed and not tests_changed:
        findings.append(("missing-tests",
                         f"改动 {len(src_changed)} 个实现文件，没有任何测试文件伴随"))
    endpoints = [ln.lstrip("+").strip() for p in src_changed
                 for ln in files[p]["added_lines"] if ENDPOINT_RE.match(ln)]
    contract_touched = [p for p in files if CONTRACT_RE.search(p)]
    if endpoints and not contract_touched:
        findings.append(("contract-drift",
                         f"新增/改动 {len(endpoints)} 个端点但契约文件未更新："
                         f"{endpoints[0][:48]}"))
    for p in src_changed:
        for ln in files[p]["added_lines"]:
            if TODO_RE.match(ln) and not TODO_WITH_ISSUE_RE.search(ln):
                findings.append(("todo-no-issue",
                                 f"TODO/FIXME 未关联 issue：{ln.lstrip('+').strip()[:52]}"))
    return findings


def ensure_fixtures() -> None:
    """生成大 diff 靶场（420 行新增，>400 阈值）；其余四个为手写静态文件。"""
    huge = DIFFS / "pr_huge.diff"
    if huge.exists():
        return
    DIFFS.mkdir(exist_ok=True)
    lines = ["diff --git a/src/bulk.py b/src/bulk.py",
             "--- a/src/bulk.py", "+++ b/src/bulk.py"]
    for i in range(210):
        lines += [f"+def bulk_handler_{i}(payload):", f"+    return payload.get('n', {i})"]
    huge.write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Danger 风格 PR 评审机器人")
    ap.add_argument("--diff", help="单个 PR 的 diff 文件")
    ap.add_argument("--all", action="store_true", help="跑 diffs/ 下全部 PR 并汇总")
    args = ap.parse_args()
    ensure_fixtures()

    targets = sorted(DIFFS.glob("*.diff")) if args.all else [Path(args.diff)]
    all_results = {}
    for diff_file in targets:
        findings = review(parse_diff(diff_file.read_text()))
        all_results[diff_file.name] = findings
        print(f"🤖 PR 评审 · {diff_file.name}")
        if findings:
            for rule, msg in findings:
                print(f"  ⚠️ [{rule}] {msg}")
        else:
            print("  ✅ 零警告")
        print()
        if not args.all:
            continue

    if args.all:
        hit = {name: [r for r, _ in f] for name, f in all_results.items()}
        clean_ok = not hit["pr_clean.diff"]
        targets_ok = all(hit[f"pr_{k}.diff"] for k in ["huge", "no_tests", "new_endpoint", "todo"])
        print("===== 五 PR 汇总 =====")
        for name, rules in hit.items():
            print(f"  {name}: {len(rules)} 条（{', '.join(rules) or '零警告'}）")
        print(f"验收自检：4 个问题 PR 全部命中 {'✓' if targets_ok else '✗'}；"
              f"干净 PR 零警告 {'✓' if clean_ok else '✗'}")
        out = ROOT / "reports"
        out.mkdir(exist_ok=True)
        (out / "pr_bot_report.json").write_text(json.dumps(
            {"generated_at": datetime.now().isoformat(timespec="seconds"),
             "prs": {k: [{"rule": r, "msg": m} for r, m in v]
                     for k, v in all_results.items()},
             "targets_hit": targets_ok, "clean_zero": clean_ok},
            ensure_ascii=False, indent=2))
        print("产物：reports/pr_bot_report.json")
        sys.exit(0 if (targets_ok and clean_ok) else 1)


if __name__ == "__main__":
    main()
