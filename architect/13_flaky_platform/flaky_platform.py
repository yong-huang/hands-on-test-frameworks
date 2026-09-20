#!/usr/bin/env python3
"""flaky_platform.py — flaky 检测与隔离平台：检测 → quarantine → 门禁联动 → 摘牌。

架构师视角的一句话：**flaky 的危害不是失败本身，是它把「红色」的信用透支光**——
团队学会无看重跑的那一刻，CI 已经死了。治理闭环四步：
  1. 检测：同 commit 重跑 N 轮，结果不一致的用例即 flaky（定义来自 TesterHome 共识）；
  2. 隔离：写入 quarantine 清单——失败不挡主干，但绝不静默：每次运行都亮 QUARANTINED；
  3. 联动：门禁视角 quarantined 失败不算 blocking；flaky 率作为指标喂给项目 3 门禁；
  4. 摘牌：修复后 --remove 摘牌，恢复全量监视（谁摘的牌要留痕）。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
PY = str(REPO / ".venv" / "bin" / "python")
QUARANTINE = Path(__file__).parent / "reports" / "quarantine.yaml"
FLAKY_JSON = Path(__file__).parent / "reports" / "flaky.json"      # 项目 3 门禁的数据源


# ---------------------------------------------------------------- 执行一轮
def run_suite_once(tag: str) -> dict[str, str]:
    """跑一轮演示套件，返回 {nodeid: passed|failed}。"""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
        junit = tf.name
    subprocess.run(
        [PY, "-m", "pytest", "tests", "-q", "-o", "addopts=",
         "-p", "no:cacheprovider", f"--junitxml={junit}"],
        cwd=Path(__file__).parent, capture_output=True, text=True, timeout=300, check=False)
    root = ET.parse(junit).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    out: dict[str, str] = {}
    for tc in suite.iter("testcase"):
        f = tc.get("file") or (tc.get("classname", "").replace(".", "/") + ".py")
        nodeid = f"{f}::{tc.get('name')}"
        failed = tc.find("failure") is not None or tc.find("error") is not None
        out[nodeid] = "failed" if failed else "passed"
    Path(junit).unlink(missing_ok=True)
    return out


# ---------------------------------------------------------------- 检测
def detect(rounds: int) -> dict:
    results: dict[str, list[str]] = {}
    for i in range(rounds):
        for nodeid, verdict in run_suite_once(f"round{i}").items():
            results.setdefault(nodeid, []).append(verdict)
    flaky = {k: v for k, v in results.items() if len(set(v)) > 1}
    stable_ok = {k for k, v in results.items() if set(v) == {"passed"}}
    # 门禁口径：主干 flaky 率只算「未被隔离管理的」——已入 quarantine 的是被管理的，
    # 管理中的 flaky 不应让主干永远红（它们有摘牌流程盯着）
    managed = set(load_quarantine())
    unmanaged = [k for k in flaky if k not in managed]
    rate = round(len(unmanaged) * 100 / len(results), 2) if results else 0.0
    summary = {"rounds": rounds, "detected": flaky, "stable": sorted(stable_ok),
               "unmanaged": sorted(unmanaged), "managed_count": len(flaky) - len(unmanaged),
               "flaky_rate_pct": rate,
               "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    FLAKY_JSON.parent.mkdir(parents=True, exist_ok=True)
    FLAKY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


# ---------------------------------------------------------------- quarantine
def load_quarantine() -> dict:
    if QUARANTINE.exists():
        return yaml.safe_load(QUARANTINE.read_text(encoding="utf-8")) or {}
    QUARANTINE.parent.mkdir(parents=True, exist_ok=True)
    return {}


def save_quarantine(q: dict) -> None:
    QUARANTINE.write_text(yaml.safe_dump(q, allow_unicode=True, sort_keys=False), encoding="utf-8")


def quarantine_merge(detected: dict) -> list[str]:
    q = load_quarantine()
    now = time.strftime("%Y-%m-%d %H:%M")
    for nodeid in detected:
        if nodeid not in q:
            q[nodeid] = {"detected_at": now, "rounds_inconsistent": "见 flaky.json"}
            print(f"  ➡️  入隔离区：{nodeid}")
        else:
            print(f"  ↻  已在隔离区：{nodeid}")
    save_quarantine(q)
    return list(q)


def quarantine_remove(pattern: str) -> int:
    q = load_quarantine()
    victims = [k for k in q if pattern in k]
    for k in victims:
        del q[k]
        print(f"  🎉 摘牌：{k}")
    save_quarantine(q)
    return len(victims)


# ---------------------------------------------------------------- 门禁联动
def gate() -> int:
    q = load_quarantine()
    results = run_suite_once("gate")
    blocking, quarantined, passed = [], [], 0
    for nodeid, verdict in results.items():
        if verdict == "passed":
            passed += 1
        elif nodeid in q:
            quarantined.append(nodeid)
        else:
            blocking.append(nodeid)
    print(f"# 🚦 flaky 感知门禁：{passed} 过 / {len(quarantined)} 隔离 / {len(blocking)} 阻断")
    for n in quarantined:
        print(f"  ⚠️  QUARANTINED（不挡主干但亮灯）：{n}")
    for n in blocking:
        print(f"  ❌ BLOCKING：{n}")
    verdict = "PASS" if not blocking else "FAIL"
    print(f"裁决：{verdict}（quarantined 失败不挡主干——但摘牌流程必须有人在跟）")
    return 0 if not blocking else 1


# ---------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser(description="flaky 检测与隔离平台")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect"); d.add_argument("--rounds", type=int, default=10)
    sub.add_parser("gate")
    r = sub.add_parser("remove"); r.add_argument("--test", required=True)
    args = ap.parse_args()

    if args.cmd == "detect":
        s = detect(args.rounds)
        print(f"# 🔬 {s['rounds']} 轮重跑检测完成：检出 flaky {len(s['detected'])} 条，"
              f"其中未管理（计入门禁口径）{len(s['unmanaged'])} 条 → flaky 率 {s['flaky_rate_pct']}%")
        for nodeid, verdicts in s["detected"].items():
            print(f"  ❗ {nodeid}：{verdicts.count('passed')}/{s['rounds']} 过（结果不一致）")
        quarantine_merge(list(s["detected"]))
        print(f">>> 检测明细已写入 {FLAKY_JSON}")
        return 0
    if args.cmd == "gate":
        return gate()
    if args.cmd == "remove":
        n = quarantine_remove(args.test)
        print(f"隔离区剩余 {len(load_quarantine())} 条")
        return 0 if n else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
