#!/usr/bin/env python3
"""verify_history.py —— 用 git 历史机械核验 TDD 纪律（验收①③的脚本化）。

五条断言，全部由 git log + runs.log + 当场重跑支撑：
  1. 红 ≥5、绿 ≥5：每轮先有失败测试提交，再有实现提交
  2. 配对顺序：按时间线，任何 GREEN 提交之前必须存在未消费的 RED（先红后绿）
  3. 节奏留档：runs.log 与提交一一对应——RED 全 FAIL、GREEN/REFACTOR 全 PASS
  4. 重构保绿：REFACTOR 提交存在，且其提交后的测试运行记录为 PASS
  5. 终局全绿：当场再跑一次全量测试
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT / "repo"
PY = str(ROOT.parent.parent / ".venv/bin/python")


def git(args: list[str]) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True).stdout.strip()


def main():
    failures = []

    subjects = git(["log", "--reverse", "--format=%s"]).splitlines()
    reds = [s for s in subjects if s.startswith("🔴")]
    greens = [s for s in subjects if s.startswith("🟢")]
    refactors = [s for s in subjects if s.startswith("🔵")]

    if len(reds) >= 5 and len(greens) >= 5:
        print(f"✅ 断言1 红 {len(reds)} 轮 / 绿 {len(greens)} 轮（≥5）")
    else:
        failures.append(f"红 {len(reds)} / 绿 {len(greens)} 不足 5 轮")

    unconsumed = 0
    ordered = True
    for s in subjects:
        if s.startswith("🔴"):
            unconsumed += 1
        elif s.startswith("🟢"):
            unconsumed -= 1
            if unconsumed < 0:
                ordered = False
    if ordered and unconsumed == 0:
        print("✅ 断言2 先红后绿：每个实现提交之前都有对应的失败测试提交")
    else:
        failures.append(f"红绿配对错乱（余量 {unconsumed}）")

    log_lines = (ROOT / "reports/runs.log").read_text().strip().splitlines()
    entries = [line.split("|") for line in log_lines]
    ok_rhythm = (len(entries) == len(subjects)
                 and all((e[0] == "🔴 RED") == (e[2] == "FAIL") for e in entries)
                 and all(e[2] == "PASS" for e in entries if e[0] != "🔴 RED"))
    if ok_rhythm:
        print(f"✅ 断言3 节奏留档：{len(entries)} 条运行记录与提交一一对应"
              f"（RED 全 FAIL、GREEN/REFACTOR 全 PASS）")
    else:
        failures.append("runs.log 与提交不对应或红绿判定不符")

    if refactors:
        idx_ref = subjects.index(refactors[0])
        greens_before = sum(1 for s in subjects[:idx_ref] if s.startswith("🟢"))
        refactor_pass = any(e[0] == "🔵 REFACTOR" and e[2] == "PASS" for e in entries)
        if greens_before == len(greens) and refactor_pass:
            print(f"✅ 断言4 重构保绿：REFACTOR 在全部 {len(greens)} 个 GREEN 之后，"
                  f"提交后测试运行 PASS")
        else:
            failures.append("REFACTOR 位置或提交后状态不符")
    else:
        failures.append("没有 REFACTOR 提交")

    final = subprocess.run([PY, "-m", "pytest", "-q"], cwd=REPO,
                           capture_output=True, text=True)
    if final.returncode == 0:
        print("✅ 断言5 终局全绿：当场重跑全量测试通过")
    else:
        failures.append("终局测试红了")

    if failures:
        print("\n❌ 核验失败：")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\nTDD 纪律核验全部通过（exit 0）")


if __name__ == "__main__":
    main()
