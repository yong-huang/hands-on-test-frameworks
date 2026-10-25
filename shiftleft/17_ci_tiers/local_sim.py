#!/usr/bin/env python3
"""local_sim.py —— CI 分层流水线的本地模拟器：读 ci_workflow.yml，按同样的
分层/短路/预算语义在本机执行。

与真 GitHub Actions 的关系：job/needs/steps/timeout-minutes 语义一致；
差异有两处并如实标注——① actions/checkout 由「已有工作目录」代替；
② `--config auto`（联网拉社区规则）本地映射为项目 12 的规则目录。
预算取自 yml 的 timeout-minutes，实测耗时与其比对写预算报表。

用法：
    python local_sim.py                # 全绿路径（sample/）
    python local_sim.py --bad          # 短路路径（sample_bad/ 埋 F401）
产出：reports/summary.md / .json
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
BIN = REPO / ".venv/bin"

# 本地映射：yml 里面向真实 CI 的写法 → 本机可执行的等价命令
SUBSTITUTIONS = [
    ("--config auto", "--config ../12_sast_rules/rules"),
    ("gitleaks detect --no-git --redact",
     f"gitleaks detect --no-git --source {ROOT} --redact"),
]


def run_step(cmd: str, sample: str) -> tuple[bool, str]:
    """执行一条 run 步骤：sample 目录替换 + venv 环境，返回 (成功, 输出尾部)。

    GH 表达式（${{ ... }}）替换为占位符；GITHUB_STEP_SUMMARY 指到本地文件
    ——record 步的 summary 写入在本地照常生效。"""
    for old, new in SUBSTITUTIONS:
        cmd = cmd.replace(old, new)
    cmd = cmd.replace("sample/", f"{sample}/")
    cmd = re.sub(r"\$\{\{[^}]*\}\}", "SIMULATED", cmd)  # GH 表达式 → 占位
    env = {"PATH": f"{BIN}:{os.environ['PATH']}", "PYTHONDONTWRITEBYTECODE": "1",
           "HOME": os.environ.get("HOME", ""), "LANG": "en_US.UTF-8",
           "GITHUB_STEP_SUMMARY": str(ROOT / "reports" / "step_summary.md")}
    proc = subprocess.run(["bash", "-c", cmd], cwd=ROOT, env=env,
                          capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    return proc.returncode == 0, tail[-1][:90] if tail else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bad", action="store_true", help="用 sample_bad/（短路演示）")
    args = ap.parse_args()
    sample = "sample_bad" if args.bad else "sample"

    (ROOT / "reports").mkdir(exist_ok=True)  # record 步写 summary 用（项目 14 同款教训）
    wf = yaml.safe_load((ROOT / "ci_workflow.yml").read_text())
    jobs = wf["jobs"]
    # needs 归一化：GitHub Actions 接受标量（needs: fast），PyYAML 会原样给字符串
    for job in jobs.values():
        if isinstance(job.get("needs"), str):
            job["needs"] = [job["needs"]]
    order, pending = [], dict(jobs)
    while pending:  # 按 needs 拓扑排序
        progressed = False
        for name in list(pending):
            if all(n in order for n in pending[name].get("needs", [])):
                order.append(name)
                del pending[name]
                progressed = True
        if not progressed:
            sys.exit("needs 依赖成环")

    results = {}
    failed = set()
    print(f"流水线：{' → '.join(order)}（样例 {sample}/）\n")
    for name in order:
        job = jobs[name]
        needs_ok = all(n in results and results[n]["status"] == "通过" for n in job.get("needs", []))
        if not needs_ok:
            results[name] = {"status": "跳过", "seconds": 0, "budget_min": job.get("timeout-minutes", 0),
                             "note": f"依赖失败：{', '.join(job.get('needs', []))}"}
            print(f"⏭️  [{name}] 跳过（{results[name]['note']}）——短路生效，不浪费后层算力")
            continue

        budget_min = job.get("timeout-minutes", 0)
        print(f"▶️  [{name}] {job['name']}（预算 {budget_min}min）")
        t0 = time.perf_counter()
        ok = True
        for step in job["steps"]:
            if "uses" in step:
                print(f"    ⏭️  uses {step['uses']}（本地模拟：工作目录即已 checkout）")
                continue
            ok, tail = run_step(step["run"], sample)
            mark = "✅" if ok else "❌"
            print(f"    {mark} {step['name']}: {tail}")
            if not ok:
                failed.add(name)
                break
        seconds = time.perf_counter() - t0
        status = "通过" if ok else "失败"
        within = seconds <= budget_min * 60
        results[name] = {"status": status, "seconds": round(seconds, 2),
                         "budget_min": budget_min, "within_budget": within}
        if not ok:
            print(f"    ❌ 失败——下游层将被短路")
        print(f"    耗时 {seconds:.1f}s / 预算 {budget_min}min（{'达标' if within else '超支'}）")

    print("\n===== 预算报表（job summary 模拟）=====")
    header = f"| 层 | 结果 | 实测 | 预算 | 达标 |\n|:--|:--|--:|--:|:--:|\n"
    rows = ""
    for name, r in results.items():
        if r["status"] == "跳过":
            rows += f"| {name} | ⏭️ 跳过（短路） | - | {r['budget_min']}min | - |\n"
        else:
            mark = "✅" if r["within_budget"] else "❌"
            rows += f"| {name} | {r['status']} | {r['seconds']}s | {r['budget_min']}min | {mark} |\n"
    print(header + rows, end="")

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "sample": sample, "jobs": results,
               "failed": sorted(failed),
               "short_circuited": [n for n, r in results.items() if r["status"] == "跳过"]}
    (out / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    (out / "summary.md").write_text(
        f"# 预算报表（{payload['generated_at']}，样例 {sample}/）\n\n" + header + rows)
    print("产物：reports/summary.md、reports/summary.json")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    import os
    main()
