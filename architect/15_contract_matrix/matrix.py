#!/usr/bin/env python3
"""matrix.py — 契约测试平台化：provider 版本矩阵 + can-i-deploy 发布检查。

架构师视角的一句话：**契约测试的终点不是「一对 consumer/provider 变绿」，是回答
「这个版本的 provider 能不能发布」**——把全部契约对每个 provider 候选版本跑验证矩阵，
全绿才放行，这就是本地版 can-i-deploy（Pact Broker 的核心语义，零付费实现）。

矩阵：
  v1 = 真 SUT（当前主干）
  v2 = 故意破坏契约的变体（中间件把响应里的 customer 改名为 clientName）
每个 pact 文件 × 每个 provider 版本 = 一次独立验证 → PASS/FAIL 矩阵表。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = str(REPO / ".venv" / "bin" / "python")
PACTS_DIR = REPO / "labs/15_pact/pacts"
CONSUMER_DIR = REPO / "labs/15_pact/consumer"

VERSIONS = {
    "v1-sut-8899": "http://localhost:8899",
    "v2-broken-8902": "http://localhost:8902",
}


def ensure_pacts() -> list[Path]:
    """consumer 测试生成/合并契约文件（幂等：pact write_file 合并语义）。"""
    if not list(PACTS_DIR.glob("*.json")):
        subprocess.run([PY, "-m", "pytest", "test_pact_consumer.py", "-q",
                        "-c", "../configs/pytest.ini", "--rootdir=."],
                       cwd=CONSUMER_DIR, check=True, capture_output=True, text=True, timeout=300)
    return sorted(PACTS_DIR.glob("*.json"))


def verify_one(pact_file: Path, base_url: str) -> tuple[bool, str]:
    """对单个 provider 实例验证单个 pact 文件。返回 (ok, 摘要)。"""
    code = (
        "import sys; sys.path.insert(0, %r);"
        "from pact.verifier import Verifier;"
        "v = Verifier('ministore-api');"
        "v.add_source(sys.argv[1]);"
        "v.add_transport(url=sys.argv[2]);"
        "v.verify();"
        "print('RESULT: PASS')"
    ) % (str(REPO / "labs/15_pact/provider"),)
    r = subprocess.run([PY, "-c", code, str(pact_file), base_url],
                       capture_output=True, text=True, timeout=300, check=False)
    tail = (r.stdout + r.stderr).strip().splitlines()
    note = next((ln for ln in reversed(tail) if "RESULT" in ln or "mismatch" in ln.lower()),
                tail[-1] if tail else "")
    return r.returncode == 0, note[:90]


def build_matrix(pact_files: list[Path]) -> list[dict]:
    rows = []
    for ver, base in VERSIONS.items():
        for p in pact_files:
            ok, note = verify_one(p, base)
            rows.append({"version": ver, "pact": p.name, "ok": ok, "note": note[:80]})
            print(f"  {'✅' if ok else '❌'} {ver} × {p.name}")
    return rows


def can_i_deploy(matrix: list[dict], version: str) -> bool:
    return all(r["ok"] for r in matrix if r["version"] == version)


def main() -> int:
    ap = argparse.ArgumentParser(description="契约版本矩阵 + can-i-deploy")
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    args = ap.parse_args()

    pact_files = ensure_pacts()
    print(f"契约文件 {len(pact_files)} 个；开始矩阵验证（{len(VERSIONS)} 个 provider 版本）")
    matrix = build_matrix(pact_files)

    print("\n# 📜 provider 版本兼容性矩阵")
    print("| 契约 | v1 主干 | v2 破坏变体 |")
    print("|:---|:---:|:---:|")
    for p in pact_files:
        cells = []
        for ver in VERSIONS:
            row = next(r for r in matrix if r["version"] == ver and r["pact"] == p.name)
            cells.append("✅" if row["ok"] else "❌")
        print(f"| {p.name} | {cells[0]} | {cells[1]} |")

    verdicts = {v: can_i_deploy(matrix, v) for v in VERSIONS}
    print("\n# 🚦 can-i-deploy 发布检查")
    for v, ok in verdicts.items():
        print(f"- {v}: {'✅ 可发布（全部契约满足）' if ok else '❌ 禁止发布（存在契约破坏）'}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "matrix.json").write_text(json.dumps(
        {"matrix": matrix, "can_i_deploy": verdicts,
         "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")},
        ensure_ascii=False, indent=2), encoding="utf-8")

    ok = verdicts.get("v1-sut-8899") is True and verdicts.get("v2-broken-8902") is False
    print(f"\n{'✅ 验收通过' if ok else '❌ 验收未过'}（v1 全绿可发布；v2 破坏契约被拦截）")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
