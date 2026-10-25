#!/usr/bin/env python3
"""measure.py —— 门禁链耗时实测与「本地 vs CI」反馈延迟对比。

口径：本地=pre-commit 实测墙钟（快层/重层各一次）；CI=文档化估算——
参考本系列 architect/10 分层流水线的快反馈层预算（5 分钟：排队+装环境+全量），
非本机实测，报告里显式标注估算。
产出：reports/chain_timing.json
"""
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT / "chain_repo"
PY = str(ROOT.parent.parent / ".venv/bin/python")
CI_REFERENCE_SECONDS = 300  # 文档化估算：architect/10 快反馈层预算（5 分钟）


def timed(args: list[str]) -> tuple[float, int, str]:
    t0 = time.perf_counter()
    proc = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    return time.perf_counter() - t0, proc.returncode, proc.stdout[-400:]


def main():
    fast_t, fast_code, fast_out = timed([PY, "-m", "pre_commit", "run", "--all-files"])
    heavy_t, heavy_code, heavy_out = timed(
        [PY, "-m", "pre_commit", "run", "--hook-stage", "manual", "--all-files"])

    print("===== 本地 vs CI 反馈延迟对比 =====")
    print(f"本地快层（ruff+mypy+gitleaks，实测）：{fast_t:.1f}s，{'PASS' if fast_code == 0 else 'FAIL'}")
    print(f"本地重层（antipattern+semgrep，实测）：{heavy_t:.1f}s，{'PASS' if heavy_code == 0 else 'FAIL'}")
    print(f"CI 参考口径（文档化估算，architect/10 快反馈层预算）：{CI_REFERENCE_SECONDS}s")
    speedup = CI_REFERENCE_SECONDS / max(fast_t, 0.1)
    print(f"快层相对 CI 预算：约 {speedup:.0f}× 反馈提速（本地秒级 vs CI 分钟级）")
    ok = fast_t < 15 and fast_code == 0
    print(f"验收自检：快层 <15s {'✓ 达标' if ok else '✗ 未达标'}")

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    (out / "chain_timing.json").write_text(json.dumps(
        {"generated_at": datetime.now().isoformat(timespec="seconds"),
         "fast_seconds": round(fast_t, 2), "fast_pass": fast_code == 0,
         "heavy_seconds": round(heavy_t, 2), "heavy_pass": heavy_code == 0,
         "ci_reference_seconds": CI_REFERENCE_SECONDS,
         "ci_reference_is_estimate": True,
         "fast_under_15s": ok}, ensure_ascii=False, indent=2))
    print("产物：reports/chain_timing.json")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
