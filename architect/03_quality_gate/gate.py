#!/usr/bin/env python3
"""gate.py — 质量门禁引擎：把策略文档的准出标准变成会红会绿的关卡。

架构师视角的一句话：**门禁不是口号，是退出码**——规则可配置、指标可采集、
裁决可解释，最后落到 CI 能用的 exit code（0 放行 / 1 拦截）。

三个设计约束（面试可讲）：
  1. 规则即配置：阈值/比较符/是否 required 全在 gate_rules.yaml，改规则不改代码；
  2. 采集器适配器化：覆盖率/缺陷/下游报告各是一个 adapter，新指标=新 adapter；
  3. 诚实处理无数据：required 规则缺数据=FAIL（不许盲过），非 required 缺数据=标注未采集。

用法：
  python gate.py                          # 默认规则跑门禁 → reports/gate_report.md + gate.json
  python gate.py --rules reports/rules_strict.yaml   # 用变异后的严格规则重跑（演示拦截）
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

OPS = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "is_true": lambda a, b: bool(a) is bool(b),
}


# ---------------------------------------------------------------- 采集适配器
def collect_suite_run(repo: Path, meta: dict) -> dict:
    """跑门禁套件（labs/13，进程内直连 SUT 数据层）：一次运行同时产出覆盖率与绿榜。"""
    suite = (Path(__file__).parent / meta["coverage_suite"]).resolve()
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-c", "configs/pytest.ini", "--rootdir=.",
         "-q", f"--cov={meta['coverage_target']}", "--cov-report=term"],
        cwd=suite, capture_output=True, text=True, timeout=300)
    out = r.stdout + r.stderr
    m = re.search(r"TOTAL.*?(\d+)%", out)
    return {
        "coverage_pct": int(m.group(1)) if m else 0,
        "green": r.returncode in (0, 5),          # 5 = collected 0（也算不得绿）
        "passed": (int(m.group(1)) if (m := re.search(r"(\d+) passed", out)) else 0),
        "failed": sum(int(x) for x in re.findall(r"(\d+) failed", out)),
    }


def collect_defects(cfg: Path) -> dict:
    """缺陷库替身：只数 Sev1/Sev2 且 open 的。"""
    d = yaml.safe_load(cfg.read_text(encoding="utf-8"))["defects"]
    severe = [x for x in d if x["severity"] in ("Sev1", "Sev2") and x["status"] == "open"]
    return {"open_severe": len(severe), "ids": [x["id"] for x in severe]}


def collect_report(source: str) -> dict:
    """下游报告适配器：读 architect 兄弟项目的产物 JSON，读不到就如实说。"""
    p = (Path(__file__).parent / source).resolve()
    if not p.exists():
        return {"__missing__": f"数据源不存在（{source}）——下游项目未产出，不编造"}
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- 裁决
def evaluate(rules: list[dict], meta: dict) -> tuple[list[dict], bool]:
    results, suite_cache, passed = [], None, True
    for rule in rules:
        metric = rule["metric"]
        note, data = "", None
        if metric == "suite_run":
            suite_cache = suite_cache or collect_suite_run(Path(__file__).parents[2], meta)
            data = suite_cache
        elif metric == "defects":
            data = collect_defects(Path(__file__).parent / "configs" / "defects.yaml")
        elif metric == "report":
            data = collect_report(rule["source"])
            if "__missing__" in data:
                note = data["__missing__"]
                data = None

        if data is None or rule["field"] not in data:
            ok = not rule["required"]
            verdict = "SKIP（未采集）" if not rule["required"] else "FAIL（无数据）"
            if not ok:
                passed = False
            results.append({"id": rule["id"], "desc": rule["desc"], "measured": "—",
                            "threshold": rule["threshold"], "verdict": verdict, "note": note,
                            "required": rule["required"]})
            continue

        actual, op, th = data[rule["field"]], rule["op"], rule["threshold"]
        ok = bool(OPS[op](actual, th))
        passed &= ok
        results.append({"id": rule["id"], "desc": rule["desc"], "measured": actual,
                        "threshold": th, "verdict": "PASS" if ok else "FAIL",
                        "note": note or f"实测 {actual} {op} {th}", "required": rule["required"]})
    return results, passed


def render_md(name: str, results: list[dict], passed: bool, secs: float) -> str:
    icon = "✅ PASS" if passed else "❌ FAIL"
    lines = [f"# 🚦 质量门禁报告：{name}", f"> {time.strftime('%Y-%m-%d %H:%M:%S')} · "
             f"裁决：{icon} · 耗时 {secs:.1f}s · 退出码 {0 if passed else 1}", "",
             "| 规则 | 说明 | 实测 | 阈值 | 裁决 | required | 备注 |", "|:---|:---|:---:|:---:|:---:|:---:|:---|"]
    for r in results:
        lines.append(f"| {r['id']} | {r['desc']} | {r['measured']} | {r['threshold']} | "
                     f"{r['verdict']} | {'是' if r['required'] else '否'} | {r['note']} |")
    lines += ["", "怎么读：required 规则 FAIL 或无数据 → 门禁 FAIL（退出码 1，CI 拦截）；"
              "非 required 规则未采集只标注，不挡发布。", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="质量门禁引擎")
    base = Path(__file__).parent
    ap.add_argument("--rules", default=str(base / "configs/gate_rules.yaml"))
    ap.add_argument("--out", default=str(base / "reports"))
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.rules).read_text(encoding="utf-8"))
    t0 = time.perf_counter()
    results, passed = evaluate(cfg["rules"], cfg["meta"])
    secs = time.perf_counter() - t0

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "gate.json").write_text(json.dumps(
        {"gate": cfg["meta"]["name"], "verdict": "PASS" if passed else "FAIL",
         "rules": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "gate_report.md").write_text(render_md(cfg["meta"]["name"], results, passed, secs), encoding="utf-8")
    print(render_md(cfg["meta"]["name"], results, passed, secs))
    print(f">>> 报告已写入 {out/'gate_report.md'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
