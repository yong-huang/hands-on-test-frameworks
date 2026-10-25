#!/usr/bin/env python3
"""trace_matrix.py —— 需求↔测试双向追溯矩阵：把「哪些需求没人测、哪些测试没人要」变成机械可查。

数据三方对账：
  1. pytest --collect-only 收集的测试节点（真实存在，一条不多）
  2. configs/requirements.yaml 需求清单（要什么）
  3. configs/test_mapping.yaml 外挂映射（测试节点子串 → 覆盖的需求；零侵入共有资产）

四种判定：
  ✓ 机械一致  收集数 = 已映射 + 孤儿，且与 pytest 报告的 collected 数相等
  ⚠️ 孤儿测试 收集到了但没挂任何需求——存量资产的"没人要"测试
  ⛔ 未覆盖需求 没有任何测试挂它的需求——需求侧的漏测缺口
  ⚠️ 陈旧映射 映射键匹配不到任何节点——测试改名/删除后映射没跟着改

用法：
    python trace_matrix.py                    # 全量矩阵：需求覆盖 8/8 → 放行（exit 0）
    python trace_matrix.py --mapping configs/test_mapping_gap.yaml
                                              # 缺口演示：REQ-003 无覆盖 → exit 1（CI 卡点）
产出：reports/trace_matrix.md / .json
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
TEST_ROOTS = [REPO / "labs/11_sut_app/tests", ROOT / "tests"]  # 存量资产 + 本实验套件


def collect_nodes(py: str) -> tuple[list[str], int]:
    """跨两个测试根收集节点；返回 (节点列表, pytest 报告的 collected 数)。"""
    proc = subprocess.run(
        [py, "-m", "pytest", "--collect-only", "-q", *[str(p) for p in TEST_ROOTS]],
        cwd=REPO, capture_output=True, text=True)
    nodes = [ln.strip() for ln in proc.stdout.splitlines()
             if "::" in ln and not ln.startswith("=")]
    reported = 0
    for ln in proc.stdout.splitlines():
        if " tests collected" in ln or " test collected" in ln:
            reported = int(ln.split()[0])
    if proc.returncode != 0 or not nodes:
        sys.exit(f"收集失败（exit {proc.returncode}）：\n{proc.stdout[-800:]}{proc.stderr[-300:]}")
    return nodes, reported


def build_matrix(nodes: list[str], reqs: dict, mapping: dict):
    """三方对账：返回 (节点→需求, 需求→节点, 孤儿, 陈旧键)。"""
    node_reqs: dict[str, list[str]] = {}
    stale: list[str] = []
    for key, rids in mapping.items():
        hits = [n for n in nodes if key in n]
        if not hits:
            stale.append(key)
        for n in hits:
            for r in rids:
                if r not in node_reqs.setdefault(n, []):
                    node_reqs[n].append(r)
    orphans = [n for n in nodes if n not in node_reqs]
    req_cover = {rid: sorted(n for n, rs in node_reqs.items() if rid in rs)
                 for rid in reqs}
    return node_reqs, req_cover, orphans, stale


def w(s, width):  # 中文按 2 列宽对齐
    pad = width - sum(2 if ord(c) > 0x2E7F else 1 for c in str(s))
    return str(s) + " " * max(pad, 1)


def vis_len(s):  # 终端显示宽度（汉字占 2）
    return sum(2 if ord(c) > 0x2E7F else 1 for c in str(s))


def clip(s, width):  # 需求文本太长会顶破表格，按显示宽度截断（md/json 里保留全文）
    s = str(s)
    if vis_len(s) <= width:
        return s
    out, acc = "", 0
    for c in s:
        cw = 2 if ord(c) > 0x2E7F else 1
        if acc + cw > width - 1:
            return out + "…"
        out += c
        acc += cw
    return out


def main():
    ap = argparse.ArgumentParser(description="需求↔测试双向追溯矩阵")
    ap.add_argument("--mapping", default=str(ROOT / "configs/test_mapping.yaml"))
    ap.add_argument("--requirements", default=str(ROOT / "configs/requirements.yaml"))
    ap.add_argument("--py", default=str(REPO / ".venv/bin/python"))
    args = ap.parse_args()

    nodes, reported = collect_nodes(args.py)
    reqs = {r["id"]: " ".join(r["text"].split())
            for r in yaml.safe_load(Path(args.requirements).read_text())["requirements"]}
    mapping = yaml.safe_load(Path(args.mapping).read_text())["mapping"]
    node_reqs, req_cover, orphans, stale = build_matrix(nodes, reqs, mapping)

    # 机械一致：引擎数出来的 = pytest 报告的 = 已映射 + 孤儿（两个等式都成立才打勾）
    consistent = (len(nodes) == reported == len(node_reqs) + len(orphans))
    uncovered = [rid for rid, ns in req_cover.items() if not ns]

    print(f"需求↔测试追溯矩阵（治理对象：labs/11 SUT + 本实验套件）")
    print(f"收集 {len(nodes)} 个测试（pytest 报告 {reported}）= 已映射 {len(node_reqs)} "
          f"+ 孤儿 {len(orphans)}  {'✓ 机械一致' if consistent else '✗ 不一致！'}")
    print(f"\n{w('REQ', 9)}{w('需求', 42)}{w('覆盖', 5)}测试节点")
    for rid, text in reqs.items():
        ns = req_cover[rid]
        mark = f"{len(ns)}" if ns else "0 ⛔"
        print(f"{w(rid, 9)}{w(clip(text, 42), 42)}{w(mark, 5)}{ns[0] if ns else '——'}"
              + (f" 等 {len(ns)} 条" if len(ns) > 1 else ""))
    print(f"\n需求覆盖 {len(reqs) - len(uncovered)}/{len(reqs)}；"
          f"孤儿测试 {len(orphans)}；陈旧映射 {len(stale)}")
    for n in orphans:
        print(f"  ⚠️ 孤儿 {n}（未挂任何需求映射）")
    for k in stale:
        print(f"  ⚠️ 陈旧映射 {k}（匹配不到任何收集节点）")
    if uncovered:
        for rid in uncovered:
            print(f"  ⛔ 未覆盖需求 {rid}：{reqs[rid]}")
        print(f"门禁判定：{len(uncovered)} 条需求漏测，打回（exit 1）")
        code = 1
    else:
        print("门禁判定：需求全覆盖，放行（exit 0）")
        code = 0

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "collected": len(nodes), "mapped": len(node_reqs), "orphans": orphans,
               "stale_keys": stale, "uncovered_reqs": uncovered,
               "consistent": consistent,
               "matrix": {rid: req_cover[rid] for rid in reqs}}
    (out / "trace_matrix.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    with (out / "trace_matrix.md").open("w") as f:
        f.write(f"# 需求↔测试追溯矩阵（{payload['generated_at']}）\n\n"
                f"| REQ | 需求 | 覆盖数 | 测试节点 |\n|:--|:--|--:|:--|\n")
        for rid, text in reqs.items():
            ns = req_cover[rid]
            f.write(f"| {rid} | {text} | {len(ns)} | {'<br>'.join(ns) if ns else '——'} |\n")
        f.write(f"\n覆盖 {len(reqs) - len(uncovered)}/{len(reqs)}，孤儿 {len(orphans)}，"
                f"机械一致：{consistent}\n")
    print(f"产物：reports/trace_matrix.md、reports/trace_matrix.json")
    sys.exit(code)


if __name__ == "__main__":
    main()
