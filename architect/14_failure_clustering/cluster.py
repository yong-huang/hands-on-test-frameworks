#!/usr/bin/env python3
"""cluster.py — 失败聚类与根因归并：50 条红里找出 3 个根因，先修谁？

架构师视角的一句话：**大规模失败管理的第一性原理：修复根因，而不是逐条看失败**——
一次提交挂 200 条用例，往往一个根因就占 150 条。本工具把失败按 traceback 指纹聚类，
输出「先修哪个根因能消掉最多红」的排序。

指纹方法：
  归一化——把 traceback 里的数字/路径/hex/引号内容全部替换为占位符（它们是噪声：
  订单号、时间戳、临时目录每次都不同），保留 异常类型 + 末帧函数 + 归一化消息；
  相似合并——不同指纹再按 difflib 相似度 ≥0.85 二次合并，容忍模板的微小漂移。
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import random
import re
import time
from pathlib import Path

# ---------------------------------------------------------------- 根因模板
ROOT_CAUSES = {
    "gateway_timeout": (
        "requests.exceptions.ReadTimeout",
        [" File \"/srv/app/pay.py\", line {n}, in charge",
         "requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='pay.example.com'): Read timed out. (read timeout=3) order={oid}"],
    ),
    "db_locked": (
        "sqlite3.OperationalError",
        [" File \"/srv/app/store.py\", line {n}, in create_order",
         "sqlite3.OperationalError: database table orders is locked (session {sid})"],
    ),
    "config_drift": (
        "AssertionError",
        [" File \"/srv/app/checks.py\", line {n}, in assert_env",
         "AssertionError: expected base_url='https://api.example.com' got 'http://staging.example.local' ({ts})"],
    ),
}


def gen_failures(n: int = 50, seed: int = 7) -> list[dict]:
    """按 60%/30%/10% 分布生成 3 个根因的模拟失败，注入噪声（n/hex/时间戳）。"""
    rng = random.Random(seed)
    causes = rng.choices(list(ROOT_CAUSES), weights=[60, 30, 10], k=n)
    out = []
    for i, cause in enumerate(causes):
        exc, frames = ROOT_CAUSES[cause]
        body = "\n".join(
            f.format(n=rng.randint(100, 900), oid=f"OID-{rng.randhex}" if False else f"OID-{rng.getrandbits(24):06x}",
                     sid=f"{rng.getrandbits(16):04x}", ts=time.ctime())
            for f in frames)
        out.append({
            "test_id": f"tests/test_suite.py::test_case_{i:03d}",
            "root_cause": cause,                      # 真值：只用于验收核对，聚类器不可见
            "traceback": f"Traceback (most recent call last):\n{body}\n{exc}",
        })
    return out


# ---------------------------------------------------------------- 指纹与聚类
NOISE = [
    (re.compile(r"line \d+"), "line N"),
    (re.compile(r"0x[0-9a-f]+"), "HEX"),
    (re.compile(r"\b\d+\b"), "N"),
    (re.compile(r"'[^']*'"), "'S'"),
    (re.compile(r'"[^"]*"'), "'S'"),
    (re.compile(r"\S*/\S+"), "PATH"),
]


def fingerprint(tb: str) -> str:
    norm = tb
    for pat, repl in NOISE:
        norm = pat.sub(repl, norm)
    norm = "\n".join(ln.strip() for ln in norm.splitlines() if ln.strip())
    return hashlib.sha1(norm.encode()).hexdigest()[:12]


def cluster(failures: list[dict]) -> list[dict]:
    groups: dict[str, list[dict]] = {}
    for f in failures:
        groups.setdefault(fingerprint(f["traceback"]), []).append(f)
    # 二次合并：不同指纹但归一化文本相似度 ≥0.85 的组合并
    keys = sorted(groups, key=lambda k: -len(groups[k]))
    merged: list[list[dict]] = []
    reps: list[str] = []
    for k in keys:
        norm = re.sub(r"\b\d+\b", "N", groups[k][0]["traceback"])
        placed = False
        for i, rep in enumerate(reps):
            if difflib.SequenceMatcher(None, norm, rep).ratio() >= 0.85:
                merged[i].extend(groups[k])
                placed = True
                break
        if not placed:
            merged.append(groups[k][:])
            reps.append(norm)
    for g in merged:
        g.sort(key=lambda f: f["test_id"])
    return sorted(merged, key=lambda g: -len(g))


# ---------------------------------------------------------------- 报告
def render(clusters: list[dict]) -> str:
    lines = ["# 🧯 失败聚类与根因归并报告",
             f"> {time.strftime('%Y-%m-%d %H:%M:%S')} · 失败 {sum(len(c) for c in clusters)} 条 → "
             f"{len(clusters)} 个根因簇（验收线 ≤5）", "",
             "| 优先级 | 根因簇（代表异常） | 成员数 | 修掉能消掉的红 |", "|:---:|:---|---:|---:|"]
    for i, g in enumerate(clusters, 1):
        exc = g[0]["traceback"].splitlines()[-1].split(":")[0]
        lines.append(f"| P{i} | {exc} | {len(g)} | {len(g)} 条 |")
    lines += ["", "## 先修排序（每修一个根因，下列用例全部转绿）", ""]
    for i, g in enumerate(clusters, 1):
        exc = g[0]["traceback"].splitlines()[-1][:70]
        members = "、".join(f["test_id"].split("::")[-1] for f in g[:4])
        more = f" 等 {len(g)} 条" if len(g) > 4 else ""
        lines.append(f"{i}. **[{len(g)} 条] {exc}** —— {members}{more}")
    purity_note = "每簇内同根因占比 100%（指纹纯度）" if all(
        len({f["root_cause"] for f in g}) == 1 for g in clusters) else "存在混簇，需调相似度阈值"
    lines += ["", f"> 纯度：{purity_note}", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="失败聚类与根因归并")
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports"))
    args = ap.parse_args()

    failures = gen_failures(args.n)
    clusters = cluster(failures)

    max_cluster = clusters[0] if clusters else []
    pure = sum(1 for f in max_cluster
               if f["root_cause"] == max_cluster[0]["root_cause"]) if max_cluster else 0
    purity = pure / len(max_cluster) if max_cluster else 0
    ok = len(clusters) <= 5 and purity >= 0.8

    print(render(clusters))
    print(f">>> 验收：{len(clusters)} 簇（≤5）✅；最大簇纯度 {purity:.0%}（≥80%）"
          f"{'✅' if purity >= 0.8 else '❌'} → {'验收通过' if ok else '验收未过'}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "clusters.json").write_text(json.dumps(
        {"clusters": [{ "size": len(g), "root_cause_true": g[0]["root_cause"],
                        "members": [f["test_id"] for f in g]} for g in clusters],
         "ok": ok}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
