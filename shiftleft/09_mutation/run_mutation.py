#!/usr/bin/env python3
"""run_mutation.py —— 变异测试引擎：逐个变异体替换被测模块、跑指定测试套件，
统计「杀死 / 存活」，产出 mutation score 与 JSON 报告（两轮对比可复算）。

判定口径：变异体被认为是「杀死」当且仅当测试套件在它存在时失败（pytest 非零）；
存活 = 套件照样全绿——即测试对这一处行为改变无感，是断言缺口或等价变异。

用法：
    python run_mutation.py --tests tests/test_weak.py   --round 1 --tag 弱测试
    python run_mutation.py --tests tests/test_strong.py --round 2 --tag 强测试
产出：reports/mutation_round{N}.json（+终端表格；两轮齐了自动打印 score 变化）
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import mutator

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "pricing.py"
PY = str(ROOT.parent.parent / ".venv/bin/python")


def run_pytest(tests: str) -> int:
    # 字节码缓存会让连续写入的变异体互相串味（同秒同大小即复用旧 pyc），
    # 测的可能是上一个变异体——每次运行前清缓存并禁写，结果才确定。
    for cache in (ROOT / "__pycache__", ROOT / "tests" / "__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([PY, "-m", "pytest", tests, "-q", "--no-header", "-x"],
                          cwd=ROOT, capture_output=True, text=True,
                          env=env).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", required=True, help="判定用测试文件（相对本目录）")
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    src = TARGET.read_text()

    baseline = run_pytest(args.tests)
    if baseline != 0:
        sys.exit(f"基线测试就是红的（exit {baseline}）——先让测试全绿再谈变异。")
    print(f"基线：{args.tests} 全绿，开始变异（共 {len(mutator.describe_all(src))} 个变异点）\n")

    points = mutator.describe_all(src)
    results = []
    try:
        for pt in points:
            TARGET.write_text(mutator.build_mutant(src, pt["index"]))
            code = run_pytest(args.tests)
            status = "存活" if code == 0 else "杀死"
            results.append({**pt, "status": status})
            print(f"  {'🫥 存活' if code == 0 else '✅ 杀死'}  #{pt['index']:>2}  {pt['desc']}")
    finally:
        TARGET.write_text(src)  # 无论中途发生什么，被测模块必须还原

    killed = sum(1 for r in results if r["status"] == "杀死")
    total = len(results)
    score = round(killed / total * 100, 1) if total else 0.0
    survivors = total - killed

    print(f"\n===== 变异报告（第 {args.round} 轮 · {args.tag or args.tests}）=====")
    print(f"变异体 {total} 个：杀死 {killed} / 存活 {survivors}  →  mutation score {score}%")
    print(f"（基线全绿 + 上述逐一体实测；被测模块已还原）")

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "round": args.round, "tests": args.tests, "tag": args.tag,
               "total": total, "killed": killed, "survived": survivors,
               "score": score,
               "mutants": results}
    (out / f"mutation_round{args.round}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2))

    r1 = out / "mutation_round1.json"
    r2 = out / "mutation_round2.json"
    if r1.exists() and r2.exists() and args.round == 2:
        s1 = json.loads(r1.read_text())["score"]
        s2 = score
        print(f"两轮对比：{s1}% → {s2}%（提升 {round(s2 - s1, 1)} 个百分点，"
              f"{'✓ ≥20pp 达标' if s2 - s1 >= 20 else '✗ 未达标'}）")
    print(f"产物：reports/mutation_round{args.round}.json")
    sys.exit(0)


if __name__ == "__main__":
    main()
