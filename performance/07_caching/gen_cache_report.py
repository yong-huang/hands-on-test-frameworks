#!/usr/bin/env python3
"""解析 reports/caching_results.txt 的 key=value 行 → docs/caching.md。"""
from pathlib import Path


def main():
    rows = []
    for line in Path("reports/caching_results.txt").read_text().splitlines():
        if not line.strip():
            continue
        row = dict(kv.split("=", 1) for kv in line.split() if "=" in kv)
        rows.append(row)

    lines = [
        "# 07 · 缓存三大问题实验报告",
        "",
        "| 实验 | 模式 | 关键指标 | 判定 |",
        "|:---|:---|:---|:---|",
    ]
    for r in rows:
        key = {"hits": "hit_rate", "penetrate": "db_calls", "breakdown": "db_selects",
               "avalanche": "db_peak_per_sec"}.get(r.get("exp", ""), "-")
        lines.append(f"| {r.get('exp')} | {r.get('mode')} | {key}={r.get(key, '-')} | {r.get('verdict')} |")

    lines += [
        "",
        "## 三大问题与防护对照",
        "",
        "| 问题 | 复现方式 | 防护 | 实测效果（on → hardened） |",
        "|:---|:---|:---|:---|",
        "| 穿透 | 打不存在的 id，缓存永不命中 | 空值缓存（短 TTL） | 11968 → 305 次 DB 调用 |",
        "| 击穿 | 热 key 被删瞬间高并发 | per-key singleflight（回填在锁内！） | 554 → 109 次回源 |",
        "| 雪崩 | 大批 key 同时到期 | TTL ±20% 抖动 | DB 回源峰值 402 → 20/s（20x 削峰） |",
        "",
        "> 判定说明：penetrate 的 db_calls 为 20s 窗口内详情查询次数；breakdown 的",
        "> db_selects 为 5 次 DEL 后 40s 内的回源总数；avalanche 的 db_peak_per_sec",
        "> 为 20s 突发窗口内逐秒采样的 DB 回源峰值（雪崩的本质是瞬时尖峰）。",
        "",
    ]
    out = Path("docs/caching.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
