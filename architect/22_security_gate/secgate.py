#!/usr/bin/env python3
"""secgate.py — 安全左移门禁：SCA 依赖扫描 + SAST 代码审计 + 轻量 DAST 三层汇总。

架构师视角的一句话：**安全测试不必是专家专属**——左移三层把 80% 的常见风险拦在
流水线上：SCA 拦已知漏洞依赖（CVE 库比对）、SAST 拦危险代码模式（硬编码/eval）、
轻量 DAST 拦部署层低级失误（安全头缺失/admin 裸奔）。结果汇成一份门禁报告。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
import yaml

REPO = Path(__file__).resolve().parents[2]
SUT = "http://127.0.0.1:8899"
HEADERS_REQUIRED = ["x-content-type-options", "x-frame-options", "content-security-policy"]


# ---------------------------------------------------------------- L1 SCA
def scan_dependencies(req_file: Path) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "pip_audit", "-r", str(req_file),
         "--format", "json", "--no-deps", "--disable-pip"],
        capture_output=True, text=True, timeout=600, check=False)
    # pip-audit 无漏洞时退出 0 且输出 JSON；有漏洞退出 1 也输出 JSON
    try:
        start = r.stdout.index("{")
        data = json.loads(r.stdout[start:])
    except Exception:
        # fail-safe：扫描器崩溃绝不等于「无漏洞」——如实判 FAIL 并留下原因
        return {"ok": False,
                "cves": [{"package": "pip-audit", "cve": "SCANNER-FAILED",
                          "fix": (r.stderr or r.stdout).strip().splitlines()[-1][:80] if (r.stderr or r.stdout).strip() else ""}],
                "raw": (r.stderr or r.stdout)[-300:]}
    cves, seen = [], set()
    for dep in data.get("dependencies", []):
        for vuln in dep.get("vulns", []):
            ids = vuln.get("aliases", []) or [vuln["id"]]
            cve = next((x for x in ids if x.startswith("CVE-")), ids[0])
            if cve in seen:
                continue
            seen.add(cve)
            cves.append({"package": dep["name"], "cve": cve,
                         "fix": (vuln.get("fix_versions") or [""])[0]})
    return {"ok": not cves, "cves": cves}


# ---------------------------------------------------------------- L2 SAST
def scan_code(target: Path) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "bandit", "-q", "-r", str(target), "-f", "json"],
        capture_output=True, text=True, timeout=300, check=False)
    try:
        data = json.loads(r.stdout)
        results = data.get("results", [])
        high = [x for x in results if x["issue_severity"] == "HIGH"]
        med = [x for x in results if x["issue_severity"] == "MEDIUM"]
    except Exception:
        return {"ok": False, "high": [], "medium": [], "raw": r.stderr[-200:]}
    return {"ok": not high, "high": high, "medium": med}


# ---------------------------------------------------------------- L3 轻量 DAST
def scan_runtime(base: str) -> dict:
    findings = []
    with httpx.Client(timeout=5, trust_env=False) as c:
        r = c.get(base + "/")
        missing = [h for h in HEADERS_REQUIRED if h not in {k.lower() for k in r.headers}]
        if missing:
            findings.append(f"首页缺失安全头：{', '.join(missing)}")
        admin = c.get(base + "/admin.html")
        if admin.status_code == 200 and "login" not in admin.text.lower():
            findings.append(f"/admin.html 未登录即可访问（HTTP 200，无鉴权跳转）——真实发现")
    return {"ok": not findings, "findings": findings}


# ---------------------------------------------------------------- 汇总门禁
def main() -> int:
    ap = argparse.ArgumentParser(description="安全左移门禁")
    base = Path(__file__).parent
    ap.add_argument("--reqs", default=str(base / "configs/requirements_scan.txt"))
    ap.add_argument("--out", default=str(base / "reports"))
    args = ap.parse_args()

    t0 = time.time()
    print("L1 SCA 依赖扫描（pip-audit，联网查 CVE 库）...", flush=True)
    sca = scan_dependencies(Path(args.reqs))
    print("L2 SAST 代码审计（bandit）...", flush=True)
    sast = scan_code(REPO / "labs/11_sut_app/app")
    print("L3 轻量 DAST（运行时探针）...", flush=True)
    dast = scan_runtime(SUT)

    # 门禁语义：SCA/SAST 红线必拦；DAST 发现为「部署层提示」，计入报告不拦（阈值可加严）
    blocking = []
    if not sca["ok"]:
        blocking += [f"依赖漏洞 {c['package']}（{c['cve']}，修复版本 {c['fix'] or '无'}）"
                     for c in sca["cves"]]
    if not sast["ok"]:
        blocking += [f"SAST 高危：{x['test_name']} @ {Path(x['filename']).name}:{x['line_number']}"
                     for x in sast["high"]]
    passed = not blocking

    lines = ["# 🛡️ 安全左移门禁报告",
             f"> {time.strftime('%Y-%m-%d %H:%M:%S')} · 耗时 {time.time()-t0:.0f}s · "
             f"裁决 {'✅ PASS' if passed else '❌ FAIL'}（退出码 {0 if passed else 1}）", ""]
    lines.append("## L1 SCA 依赖扫描")
    lines += [f"- {c['package']}: {c['cve']}（修复 {c['fix'] or '无'}）" for c in sca["cves"]] \
        or ["- ✅ 无已知漏洞依赖"]
    lines.append("\n## L2 SAST 代码审计")
    lines += [f"- 高危 {len(sast['high'])} 项 / 中危 {len(sast['medium'])} 项"
              + ("" if sast["ok"] else " → ❌ 存在高危，拦截")] \
        or ["- 无结果"]
    lines.append("\n## L3 轻量 DAST（运行时）")
    lines += [f"- ⚠️ {f}" for f in dast["findings"]] or ["- ✅ 未发现部署层低级失误"]
    if blocking:
        lines.append("\n## ❌ 阻断项")
        lines += [f"- {b}" for b in blocking]
    md = "\n".join(lines) + "\n"

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "sec_report.md").write_text(md, encoding="utf-8")
    (out / "sec.json").write_text(json.dumps(
        {"sca": sca | {"high": None, "medium": None} if isinstance(sca, dict) else sca,
         "sast_high": len(sast["high"]), "sast_medium": len(sast["medium"]),
         "dast": dast, "blocking": blocking, "passed": passed},
        ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(md)
    print(f">>> 报告已写入 {out/'sec_report.md'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
