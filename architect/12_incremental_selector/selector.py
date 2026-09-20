#!/usr/bin/env python3
"""selector.py — 静态增量测试选择器：AST 依赖图 + git 变更 → 受影响测试集。

架构师视角的一句话：**静态路线的价值是「零执行成本」**——不用跑任何测试就能回答
「这次变更可能影响谁」。代价是天然过近似：
  - 只看得见 import 关系，HTTP 层的依赖（API 测试打 SUT）对它不可见；
  - 「import 了就可能受影响」是保守判定，宁多选不漏选。
与项目 4（运行时覆盖率路线）构成精准测试的两条腿，本实验报告会并列对比两条路线的选择差。

用法：
  python selector.py                    # 对工作区当前 git diff 做静态选择
  python selector.py --compare-p4      # 附加运行时路线（项目 4）的对比
产物：reports/selection.md + selection.json
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TEST_RE = re.compile(r"labs/\d{2}_[a-z0-9_]+/tests/(conftest|test_.+)\.py$")


# ---------------------------------------------------------------- 扫描与注册
def scan() -> tuple[dict[str, list[str]], list[str]]:
    """module 名 → 定义文件列表；同时返回全部候选测试/conftest 文件。"""
    registry: dict[str, list[str]] = {}
    test_files: list[str] = []
    for p in REPO.rglob("*.py"):
        rel = p.relative_to(REPO).as_posix()
        if any(seg in rel for seg in (".venv", "node_modules", "__pycache__", "site-packages")):
            continue
        registry.setdefault(p.stem, []).append(rel)
        if TEST_RE.search(rel):
            test_files.append(rel)
    return registry, sorted(test_files)


def imports_of(rel: str, registry: dict[str, list[str]]) -> set[str]:
    """AST 提取顶层 import 的模块名（仅保留仓内注册过的）。"""
    path = REPO / rel
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return set()
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    return {m for m in mods if m in registry}


# ---------------------------------------------------------------- 影响分析
def affected_tests(changed: list[str], registry, test_files) -> tuple[set[str], dict[str, list[str]]]:
    """从变更文件出发沿「被 import」反向 BFS，收集可达的测试文件与理由链。"""
    file_imports = {f: imports_of(f, registry) for f in set(changed) | set(test_files)}
    # 反向边：module → 哪些文件 import 了它
    rev: dict[str, list[str]] = {}
    for f, mods in file_imports.items():
        for m in mods:
            rev.setdefault(m, []).append(f)

    affected: set[str] = set(changed)
    frontier = list(changed)
    chains: dict[str, list[str]] = {}
    while frontier:
        cur = frontier.pop()
        cur_mods = {Path(cur).stem} | {m for m, files in registry.items()
                                       if any(f == cur for f in files)}
        for m in cur_mods:
            for user in rev.get(m, []):
                if user not in affected:
                    affected.add(user)
                    chains[user] = chains.get(cur, [cur]) + [user]
                    frontier.append(user)
    tests = {f for f in affected if f in set(test_files) and "test_" in Path(f).name}
    return tests, chains


def git_changed() -> list[str]:
    r = subprocess.run(["git", "diff", "--name-only"], cwd=REPO,
                       capture_output=True, text=True)
    return [f for f in r.stdout.split() if f.endswith(".py")]


# ---------------------------------------------------------------- 报告
def render(changed: list[str], tests: set[str], chains, p4: set[str] | None, secs: float) -> str:
    lines = [
        "# 🔎 静态增量测试选择报告（AST 依赖图路线）",
        f"> {time.strftime('%Y-%m-%d %H:%M:%S')} · 变更文件 {len(changed)} 个 · "
        f"选中测试 {len(tests)} 个 · 计算 {secs:.2f}s（零测试执行）", "",
        "## 变更文件", *([f"- `{c}`" for c in changed] or ["- （无变更）"]), "",
        "## 选中测试（含理由链）", "",
    ]
    for t in sorted(tests):
        chain = " → ".join(chains.get(t, [t])[-3:])
        lines.append(f"- `{t}`\n  - 理由链：{chain}")
    if not tests:
        lines.append("- （无测试 import 变更模块——注意：HTTP 层测试对静态路线不可见）")
    if p4 is not None:
        only_static = sorted(tests - p4)
        only_runtime = sorted(p4 - tests)
        lines += ["", "## 与运行时路线（项目 4）的对比", "",
                  f"- 静态选中 {len(tests)} 条 / 运行时推荐 {len(p4)} 条",
                  f"- 仅静态命中（保守过近似）：{len(only_static)} 条",
                  f"- 仅运行时命中（执行过变更行）：{len(only_runtime)} 条",
                  "- 结论：静态是「可能受影响」的超集（宁多选不漏选），运行时是「真实碰过」的",
                  "  精确子集；HTTP 层依赖只有运行时/契约路线看得见。", ""]
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="静态增量测试选择器")
    ap.add_argument("--compare-p4", action="store_true",
                    help="加载项目 4 的运行时推荐做对比（需先跑过 precise_testing）")
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    args = ap.parse_args()

    t0 = time.perf_counter()
    registry, test_files = scan()
    changed = git_changed()
    tests, chains = affected_tests(changed, registry, test_files)
    secs = time.perf_counter() - t0

    p4 = None
    if args.compare_p4:
        p4f = Path(__file__).parent.parent / "04_precise_testing" / "reports" / "recommendation.json"
        if p4f.exists():
            rec = json.loads(p4f.read_text(encoding="utf-8"))
            p4 = {f"labs/13_db_tests/tests/{r.split('::')[0].split('/')[-1]}::{r.split('::')[-1]}"
                  for r in rec["recommended"]}

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "selection.json").write_text(json.dumps(
        {"changed": changed, "selected": sorted(tests), "chains": chains},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "selection.md").write_text(render(changed, tests, chains, p4, secs), encoding="utf-8")
    print(render(changed, tests, chains, p4, secs))
    print(f">>> 报告已写入 {out/'selection.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
