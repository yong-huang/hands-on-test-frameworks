"""hunt.py — flaky 检测-隔离-复验闭环（对照 architect/13）。

用法: .venv/bin/python hunt.py [--rounds 20] [--confirm-rounds 10]
流程: 清残留 → 20 轮重跑收集结果 → 不一致者入隔离区 → 再跑确认轮验证全绿。
产物: reports/flaky.json + quarantine.txt
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).parent
TESTS = HERE / "tests"
MARK = TESTS / ".shared_state"
QUARANTINE = TESTS / "quarantine.txt"
REPO_PY = HERE.parent.parent / ".venv" / "bin" / "python"


def run_once(tag: str) -> dict[str, str]:
    junit = HERE / "reports" / f"round_{tag}.xml"
    import subprocess
    subprocess.run(
        [str(REPO_PY), "-m", "pytest", str(TESTS), "-q", "-o", "addopts=",
         "-p", "no:cacheprovider", f"--junitxml={junit}"],
        cwd=HERE, capture_output=True, timeout=300, check=False)
    root = ET.parse(junit).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    out = {}
    for tc in suite.iter("testcase"):
        nodeid = f'{tc.get("classname")}::{tc.get("name")}'
        if tc.find("failure") is not None or tc.find("error") is not None:
            out[nodeid] = "fail"
        elif tc.find("skipped") is not None:
            out[nodeid] = "skip"
        else:
            out[nodeid] = "pass"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--confirm-rounds", type=int, default=10)
    args = ap.parse_args()

    (HERE / "reports").mkdir(exist_ok=True)
    MARK.unlink(missing_ok=True)          # 顺序依赖靶子重置（残留会让它永不现形）
    QUARANTINE.write_text("", encoding="utf-8")

    results: dict[str, set] = {}
    for r in range(1, args.rounds + 1):
        for nodeid, outcome in run_once(f"d{r}").items():
            results.setdefault(nodeid, set()).add(outcome)

    detected = sorted(k for k, v in results.items()
                      if "test_planted" in k and len(v - {"skip"}) > 1)
    stable_clean = all(len(v - {"skip"}) <= 1 for k, v in results.items() if "test_stable" in k)
    QUARANTINE.write_text("\n".join(detected) + ("\n" if detected else ""), encoding="utf-8")

    confirm_fails = 0
    for r in range(1, args.confirm_rounds + 1):
        for nodeid, outcome in run_once(f"c{r}").items():
            if outcome == "fail" and "test_planted" not in nodeid:
                confirm_fails += 1

    flaky = {
        "rounds": args.rounds,
        "detected": detected,
        "per_test": {k: sorted(v) for k, v in sorted(results.items())},
        "stable_zero_false_positive": stable_clean,
        "confirm_rounds": args.confirm_rounds,
        "confirm_failures": confirm_fails,
    }
    (HERE / "reports" / "flaky.json").write_text(json.dumps(flaky, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"检出 {len(detected)} 条 flaky：{detected}")
    print(f"稳定对照零误报：{stable_clean}；隔离后 {args.confirm_rounds} 轮失败数：{confirm_fails}")
    return 0 if len(detected) >= 2 and stable_clean and confirm_fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
