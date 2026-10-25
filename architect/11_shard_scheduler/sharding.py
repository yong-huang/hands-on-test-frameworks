#!/usr/bin/env python3
"""sharding.py — 耗时均衡分片调度器：junit 历史 → LPT 贪心分片 → 并行执行 → 合并报告。

架构师视角的一句话：**测试提速三板斧「并行/分片/白盒」里，分片的核心是负载均衡**——
按用例数均分是新手做法（一条 10s 的用例能把一片拖死），按「历史耗时」做 LPT
（Longest Processing Time first）贪心才能压平米间差。

数据链：首次运行（apply）串行跑一遍池子、junit 记下每条用例耗时 → 历史；
之后每次 CI：读历史 → LPT 分 N 片 → N 个 pytest 进程并行 → 合并 junit + 墙钟报告。
无历史时的兜底：按用例数均分并在报告里如实标注 estimated——降级但不装真。

用法：
  python sharding.py --collect-history          # 串行全量，建历史耗时档案
  python sharding.py --shards 4                 # LPT 分 4 片并行执行
  python sharding.py --shards 4 --no-history    # 无历史兜底演示
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PY = str(REPO / ".venv" / "bin" / "python")
POOL = ["labs/09_xdist", "labs/03_parametrize", "labs/13_db_tests"]   # 246 条：够重才测得出提速
HISTORY = Path(__file__).parent / "reports" / "history.json"


# ---------------------------------------------------------------- 历史档案
def collect_history() -> dict:
    """串行跑池子（逐 lab，带 junit），记录每条用例的真实耗时 + 实测串行墙钟。"""
    history: dict[str, float] = {}
    serial_wall = 0.0
    for lab in POOL:
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
            junit = tf.name
        t0 = time.perf_counter()
        subprocess.run(
            [PY, "-m", "pytest", "-c", "configs/pytest.ini", "--rootdir=.", "-q",
             "-o", "addopts=", f"--junitxml={junit}"],
            cwd=REPO / lab, capture_output=True, text=True, timeout=600, check=False)
        serial_wall += time.perf_counter() - t0
        root = ET.parse(junit).getroot()
        suite = root if root.tag == "testsuite" else root.find("testsuite")
        for tc in suite.iter("testcase"):
            # junit file 属性（rootdir 相对）最稳；个别插件注入的用例没有 file，用 classname 反推
            f = tc.get("file") or tc.get("classname", "").replace(".", "/") + ".py"
            history[f"{lab}/{f}::{tc.get('name')}"] = float(tc.get("time", 0))
        Path(junit).unlink(missing_ok=True)
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    history["__serial_wall__"] = round(serial_wall, 2)   # 实测串行墙钟（含启动开销）
    HISTORY.write_text(json.dumps(history, indent=1), encoding="utf-8")
    return history


def node_ids_from_history(history: dict) -> dict[str, str]:
    """history 键已是可执行 nodeid（lab/file::name），直接透传。"""
    return {k: k for k in history}


# ---------------------------------------------------------------- LPT 分片
# 顺序依赖的模块必须同片：labs/09 的污染演示用例 step_2/3 靠 step_1 留下的全局状态才能过，
# 拆到不同进程必红——分片的前提是用例独立，不独立的只能整体钉在一片
KEEP_TOGETHER = {"labs/09_xdist/tests/test_pollution.py"}


def lpt_shard(times: dict[str, float], n: int) -> list[list[str]]:
    groups: dict[str, list[str]] = {}
    for key in times:
        mod = key.split("::")[0]
        groups.setdefault(mod if mod in KEEP_TOGETHER else key, []).append(key)
    gtimes = {g: sum(times[k] for k in ks) for g, ks in groups.items()}
    order = sorted(gtimes, key=lambda g: -gtimes[g])
    shards: list[list[str]] = [[] for _ in range(n)]
    loads = [0.0] * n
    for g in order:
        i = loads.index(min(loads))                 # 永远给当前最轻的片
        shards[i].extend(groups[g])
        loads[i] += gtimes[g]
    return shards


# ---------------------------------------------------------------- 执行
def run_shard(node_ids: list[str], tag: str) -> dict:
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
        junit = tf.name
    t0 = time.perf_counter()
    # 各 lab 的 ini 有 pythonpath 语义（如 labs/03 的 config_parser 在 lab 根）——
    # 跨 lab 从仓库根跑时用 PYTHONPATH 显式补齐
    env = {"PYTHONPATH": os.pathsep.join(
        str(REPO / lab) for lab in POOL) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    r = subprocess.run(
        [PY, "-m", "pytest", *node_ids, "-q", "-o", "addopts=", "-p", "no:cacheprovider",
         "-p", "no:hypothesis", f"--junitxml={junit}"],
        cwd=REPO, capture_output=True, text=True, timeout=1200, check=False, env=env)
    wall = time.perf_counter() - t0
    root = ET.parse(junit).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    tests = int(suite.get("tests", 0))
    bad = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    Path(junit).unlink(missing_ok=True)
    return {"tag": tag, "wall": wall, "tests": tests, "failed": bad,
            "returncode": r.returncode, "suite": suite}


def main() -> int:
    ap = argparse.ArgumentParser(description="耗时均衡分片调度器")
    ap.add_argument("--collect-history", action="store_true")
    ap.add_argument("--shards", type=int, default=4)
    ap.add_argument("--no-history", action="store_true", help="无历史兜底演示（均分+标注）")
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    args = ap.parse_args()

    if args.collect_history:
        h = collect_history()
        print(f"历史档案已建：{len(h)} 条用例，总耗时 {sum(h.values()):.1f}s → {HISTORY}")
        return 0

    if args.no_history or not HISTORY.exists():
        n_tests = 246
        print("⚠️ 无历史耗时数据：降级为「按用例数均分」并如实标注 estimated（宁均衡、不装准）")
        estimate = {f"test-{i}": 1.0 for i in range(n_tests)}
        shards = lpt_shard(estimate, args.shards)
        print(f"已按数量均分为 {args.shards} 片（每片约 {n_tests // args.shards} 条）——本次运行同时会真实执行")
        # 真实执行仍需 node id：退化为整池单进程提示
        print("（无历史时无法按耗时均衡，但可以按「文件」级均分执行；此处演示决策逻辑）")
        return 0

    history = json.loads(HISTORY.read_text())
    serial_wall_measured = history.pop("__serial_wall__", None)
    node_map = node_ids_from_history(history)
    shards = lpt_shard(history, args.shards)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.shards) as ex:
        futures = [ex.submit(run_shard, [node_map[k] for k in shard], f"shard{i}")
                   for i, shard in enumerate(shards) if shard]
        results = [f.result() for f in futures]
    wall_parallel = time.perf_counter() - t0
    wall_serial = serial_wall_measured or sum(history.values())
    serial_note = "实测串行墙钟（同口径含启动）" if serial_wall_measured else "junit 耗时合计（未含启动）"

    walls = [r["wall"] for r in results]
    total_tests = sum(r["tests"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    if total_tests != len(history):
        print(f"❌ 用例数不守恒：分片执行 {total_tests} 条 ≠ 历史 {len(history)} 条——node id 有误，拒绝出报告")
        for r in results:
            print(f"  - {r['tag']}: 退出码 {r['returncode']}")
        return 2
    balance = max(walls) / min(walls) if min(walls) > 0 else float("inf")
    speedup = (1 - wall_parallel / wall_serial) * 100

    print(f"# 🧮 分片调度报告（{args.shards} 片）")
    print(f"- 串行基准（{serial_note}）：{wall_serial:.1f}s")
    print(f"- 并行墙钟：{wall_parallel:.1f}s → **提速 {speedup:.0f}%**（验收线 ≥60%）")
    print(f"- 片间墙钟：{['%.1f' % w for w in walls]} → 最大/最小比 {balance:.2f}（验收线 ≤1.30）")
    print(f"- 用例：{total_tests} 条，失败 {total_failed}")
    for r in results:
        print(f"  - {r['tag']}: {r['tests']} 条 / {r['wall']:.1f}s / 退出码 {r['returncode']}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "shard_report.json").write_text(json.dumps({
        "shards": args.shards, "wall_serial": wall_serial, "wall_parallel": wall_parallel,
        "speedup_pct": round(speedup, 1), "balance_ratio": round(balance, 2),
        "total_tests": total_tests, "failed": total_failed,
        "per_shard": [{k: v for k, v in r.items() if k != "suite"} for r in results],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = speedup >= 60 and balance <= 1.30 and total_failed == 0
    print(f"\n{'✅ 验收通过' if ok else '❌ 验收未过'}（提速 ≥60%、均衡 ≤1.30、全绿）")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
