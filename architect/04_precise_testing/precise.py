#!/usr/bin/env python3
"""precise.py — 精准测试原型：代码变更 → 最小回归用例集。

架构师视角的一句话：**回归测试的成本问题，本质是「变更影响分析」问题。**
工业界两条路线：
  A. 运行时路线（本工具）：coverage 上下文记录「哪条用例碰过哪行」→ 变更行反查用例；
  B. 静态路线：AST 依赖图做「改了谁 → 谁可能受影响」（对应清单项目 12）。
本工具是 A：`--cov-context=test` 记录每个用例的行级覆盖，git diff 取变更行，
交集即最小回归集。无覆盖数据时如实降级为「需全量回归」，绝不瞎推荐。

用法：
  python precise.py --refresh          # 先跑一次套件建立行级覆盖档案（--cov-context=test）
  python precise.py                    # 对工作区当前 git diff 推荐回归集
产物：reports/recommendation.md + recommendation.json；退出码 0 正常 / 2 需全量
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TARGET_MODULE = "labs/11_sut_app/app/store.py"      # 被度量模块（与 03 门禁同口径）
SUITE_DIR = Path(__file__).parent / "../../labs/13_db_tests"


def refresh_coverage() -> None:
    """跑一次门禁套件，用 --cov-context=test 建立「用例→行」覆盖档案。"""
    print("== 建立覆盖档案：跑 labs/13 套件（--cov-context=test）==")
    subprocess.run(
        [sys.executable, "-m", "pytest", "-c", "configs/pytest.ini", "--rootdir=.", "-q",
         "--cov=store", "--cov-context=test", "--cov-report="],
        cwd=SUITE_DIR.resolve(), check=True, capture_output=True, text=True, timeout=300)


def changed_lines() -> dict[str, list[int]]:
    """git diff -U0 解析工作区变更行（新文件行号）。"""
    r = subprocess.run(["git", "diff", "-U0", "--", TARGET_MODULE],
                       cwd=REPO, capture_output=True, text=True)
    lines: dict[str, list[int]] = {}
    for m in re.finditer(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", r.stdout):
        start, count = int(m.group(1)), int(m.group(2) or 1)
        lines.setdefault(TARGET_MODULE, []).extend(range(start, start + count))
    return lines


def load_contexts() -> dict[int, list[str]]:
    """从 coverage JSON 读行级上下文：行号 → 覆盖过它的用例列表。"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        tmp = tf.name
    r = subprocess.run([sys.executable, "-m", "coverage", "json", "--show-contexts",
                        "-o", tmp], cwd=SUITE_DIR.resolve(), capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("coverage json 失败（无 .coverage 数据？先 --refresh）")
    data = json.loads(Path(tmp).read_text(encoding="utf-8"))
    Path(tmp).unlink(missing_ok=True)
    f = next(p for p in data["files"] if p.endswith("store.py"))
    return {int(ln): ctxs for ln, ctxs in data["files"][f]["contexts"].items()}


def recommend(lines_by_file: dict[str, list[int]], contexts: dict[int, list[str]]) -> dict:
    touched: set[str] = set()
    uncovered: list[int] = []
    for ln in lines_by_file[TARGET_MODULE]:
        ctxs = contexts.get(ln)
        if not ctxs:
            uncovered.append(ln)
            continue
        for c in ctxs:
            if c and "::" in c:          # 过滤模块加载期的空上下文
                touched.add(c.split("|")[0])   # 去掉 coverage 上下文的 |run 相位后缀
    total_suite = 10                       # labs/13 全量用例数（与审计口径一致）
    return {
        "changed_lines": sorted(lines_by_file[TARGET_MODULE]),
        "uncovered_lines": uncovered,
        "recommended": sorted(touched),
        "total_suite": total_suite,
        "shrink_pct": round((1 - len(touched) / total_suite) * 100) if total_scope_ok(total_suite) else None,
        "risk_note": (f"{len(uncovered)} 行无覆盖数据（漏测风险）" if uncovered else "变更行均有覆盖档案"),
    }


def total_scope_ok(n: int) -> bool:
    return n > 0


def render(res: dict, secs: float) -> str:
    lines = [
        "# 🎯 精准测试推荐（运行时路线：覆盖上下文反查）",
        f"> {time.strftime('%Y-%m-%d %H:%M:%S')} · 变更文件 store.py "
        f"{len(res['changed_lines'])} 行 · 全量 {res['total_suite']} 条",
        "",
        f"- **最小回归集（{len(res['recommended'])} 条）**：",
        *([f"  - `{t}`" for t in res["recommended"]] or ["  - （无——变更行从未被任何用例覆盖）"]),
        f"- **回归集压缩比**：全量 {res['total_suite']} → {len(res['recommended'])}"
        + (f"（省 {res['shrink_pct']}%）" if res["shrink_pct"] is not None else ""),
        f"- **风险提示**：{res['risk_note']}",
        f"- **耗时**：推荐计算 {secs:.2f}s（不含建档案）",
        "",
        "复现命令：",
        "```bash",
        ("cd labs/13_db_tests && ../../.venv/bin/python -m pytest -c configs/pytest.ini --rootdir=. "
         + " ".join(res["recommended"])) if res["recommended"] else "# 无推荐用例（变更行无覆盖档案）",
        "```", "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="精准测试原型（运行时路线）")
    ap.add_argument("--refresh", action="store_true", help="先建立/刷新覆盖档案")
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    args = ap.parse_args()

    if args.refresh:
        refresh_coverage()

    if not (SUITE_DIR.resolve() / ".coverage").exists():
        print("⚠️  无覆盖数据（.coverage 不存在）：精准推荐不可用，**降级为全量回归**。\n"
             "   先执行 `python precise.py --refresh` 建立档案。宁全量、不瞎推。")
        return 2

    t0 = time.perf_counter()
    changed = changed_lines()
    if not changed:
        print("✅ 工作区对 store.py 无变更，无需回归。")
        return 0
    res = recommend(changed, load_contexts())
    secs = time.perf_counter() - t0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "recommendation.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render(res, secs)
    (out / "recommendation.md").write_text(md, encoding="utf-8")
    print(md)
    print(f">>> 推荐结果已写入 {out/'recommendation.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
