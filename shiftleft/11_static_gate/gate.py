#!/usr/bin/env python3
"""gate.py —— 静态分析分级门禁的统一入口：ruff（缺陷与风格）+ mypy（类型），
发现按配置表分级——error 阻断（exit 1），warning 放行但记录。

分级即治理：某个规则码该不该阻断是团队决策，引擎只读表执行——
把码从 [warning] 挪进 [error]（或反向）即完成升降级，改配置立即生效。

用法：
    python gate.py --path fixtures                       # 全量 fixtures（坏的全拦）
    python gate.py --path fixtures/clean.py              # 干净文件（放行）
    python gate.py --path fixtures/bad_style.py \\
        --config configs/gate_rules_strict.toml          # 升级演示：F401 变阻断
产出：reports/static_gate.json
"""
import argparse
import json
import subprocess
import sys
import tomllib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
PY = str(REPO / ".venv/bin/python")


def run_ruff(path: Path) -> list[dict]:
    proc = subprocess.run(
        ["ruff", "check", "--select", "E,F,B", "--output-format", "json", str(path)],
        cwd=ROOT, capture_output=True, text=True)
    if proc.returncode not in (0, 1):  # 0=干净 1=有发现，其余是工具故障
        sys.exit(f"ruff 运行失败：\n{proc.stderr}")
    return [{"tool": "ruff", "code": x["code"], "msg": x["message"],
             "loc": f"{Path(x['filename']).name}:{x['location']['row']}"}
            for x in json.loads(proc.stdout or "[]")]


def run_mypy(path: Path) -> list[dict]:
    proc = subprocess.run(
        [PY, "-m", "mypy", "--no-error-summary", "--show-error-codes", str(path)],
        cwd=ROOT, capture_output=True, text=True)
    out = []
    for line in proc.stdout.splitlines():
        # 形如：fixtures/bad_type.py:4: error: Incompatible return value ...  [return-value]
        if ": error: " not in line:
            continue
        loc, rest = line.split(": error: ", 1)
        msg, _, code = rest.rpartition("  [")
        code = code.rstrip("]").removeprefix("mypy:")  # mypy 2.x 自带 mypy: 前缀，去重
        out.append({"tool": "mypy", "code": f"mypy:{code}",
                    "msg": msg, "loc": Path(loc).name})
    return out


def classify(code: str, tiers: dict) -> str:
    if code in tiers["error"]["ruff"] or code in tiers["error"]["mypy"]:
        return "error"
    if code in tiers["warning"]["ruff"] or code in tiers["warning"]["mypy"]:
        return "warning"
    return "warning(未分级)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=str(ROOT / "fixtures"))
    ap.add_argument("--config", default=str(ROOT / "configs/gate_rules.toml"))
    args = ap.parse_args()

    tiers = tomllib.loads(Path(args.config).read_text())
    findings = run_ruff(Path(args.path)) + run_mypy(Path(args.path))
    for f in findings:
        f["tier"] = classify(f["code"], tiers)

    blockers = [f for f in findings if f["tier"] == "error"]
    warnings = [f for f in findings if f["tier"].startswith("warning")]

    print(f"静态门禁（分级表：{Path(args.config).name}）——"
          f"error {len(blockers)} / warning {len(warnings)}\n")
    for f in findings:
        mark = "⛔ 阻断" if f["tier"] == "error" else "⚠️ 放行"
        print(f"  {mark} [{f['tier']}] {f['loc']} {f['code']}  {f['msg'][:52]}")
    if not findings:
        print("  （零发现）")

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    (out / "static_gate.json").write_text(json.dumps(
        {"generated_at": datetime.now().isoformat(timespec="seconds"),
         "config": Path(args.config).name, "path": args.path,
         "blockers": blockers, "warnings": warnings,
         "exit": 1 if blockers else 0}, ensure_ascii=False, indent=2))

    if blockers:
        codes = sorted({f["code"] for f in blockers})
        print(f"\n⛔ 门禁判定：{len(blockers)} 个 error 级发现（规则码 {', '.join(codes)}），"
              f"阻断（exit 1）")
        sys.exit(1)
    print(f"\n✅ 门禁判定：无 error 级发现，放行（exit 0）"
          f"{f'；warning 已记录在 reports/static_gate.json' if warnings else ''}")


if __name__ == "__main__":
    main()
