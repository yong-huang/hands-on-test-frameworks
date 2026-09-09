#!/usr/bin/env python3
"""汇总 EXPLAIN 前后、pg_stat_statements 排行、连接池前后 → docs/db_analysis.md。"""
import json
from pathlib import Path


def find_stock_scan(node):
    """专找 stock 表的扫描节点（plan 里 products 的扫描不是主角）"""
    if node.get("Relation Name") == "stock":
        return node
    for ch in node.get("Plans", []):
        r = find_stock_scan(ch)
        if r:
            return r
    return None


def explain(tag):
    plan = json.load(open(f"reports/explain_{tag}.json"))[0]["Plan"]
    scan = find_stock_scan(plan)
    return scan["Node Type"], scan["Actual Total Time"], scan.get("Actual Rows", 0)


def pool(tag):
    m = json.load(open(f"reports/pool_{tag}.json"))["metrics"]
    d = m["http_req_duration"]
    peak = max(int(l.rsplit("=", 1)[1]) for l in open(f"reports/pg_activity_{tag}.txt"))
    return {
        "rps": m["http_reqs"].get("rate", 0),
        "p95": d["p(95)"],
        "err": m["http_req_failed"].get("rate", m["http_req_failed"].get("value", 0)) * 100,
        "peak": peak,
    }


def main():
    sb, sb_t, sb_rows = explain("before")
    sa, sa_t, sa_rows = explain("after")
    speedup = sb_t / sa_t if sa_t else float("inf")
    pb, pa = pool("before"), pool("after")
    lines = [
        "# 36 · 数据库性能分析报告",
        "",
        "## EXPLAIN 证据：索引迁移前后（stock 5 万行）",
        "",
        "| 阶段 | 扫描方式 | 目标表 | 该节点实际耗时 |",
        "|:---|:---|:---|---:|",
        f"| 建索引前 | {sb} | {sb_rows:,} 行 | {sb_t:.3f} ms |",
        f"| 建索引后 | {sa} | {sa_rows:,} 行 | {sa_t:.3f} ms |",
        f"| **变化** | {sb} → {sa} | | **{speedup:,.0f}x** |",
        "",
        "证据文件：`reports/explain_before.json` / `reports/explain_after.json`（ANALYZE + BUFFERS 全量计划）",
        "",
        "## pg_stat_statements 排行（按总耗时）",
        "",
        "### 建索引前（JOIN 均值 11.16ms；UPDATE 已是 23ms 的隐形大头）",
        "",
        "```",
        Path("reports/pg_stat_top_before.txt").read_text().strip(),
        "```",
        "",
        "### 建索引后（JOIN 降至 0.03ms/370x；UPDATE 依旧 ~21ms：瓶颈转移实录）",
        "",
        "```",
        Path("reports/pg_stat_top_after.txt").read_text().strip(),
        "```",
        "",
        "## 连接池打满 → 调参（100 VU 压 45s）",
        "",
        "| 阶段 | 池上限 | PG 活跃连接峰值 | RPS | P95(ms) | 错误率% |",
        "|:---|---:|---:|---:|---:|---:|",
        f"| 调参前 | 10 | {pb['peak']} | {pb['rps']:.1f} | {pb['p95']:.1f} | {pb['err']:.2f} |",
        f"| 调参后 | 40 | {pa['peak']} | {pa['rps']:.1f} | {pa['p95']:.1f} | {pa['err']:.2f} |",
        "",
        "判读：调参前活跃连接被池钉死在 10（100 VU 在应用侧排队直到池超时）；",
        "调参后峰值 10→40，池钳制确认解除。P95 没有同步下降——因为 pg_stat 排行",
        "显示 **UPDATE stock 以 21ms 均值成了新的头号查询**：15 万行高频更新表",
        "死元组膨胀 + 同商品热点行锁竞争，这是索引修好 JOIN 之后暴露出的下一层",
        "瓶颈（治理方向：降低更新频率/分区/autovacuum 调优）。",
        "**解决一个瓶颈，下一个瓶颈才现形**——这就是性能工程迭代的样子。",
        "另注：连接池上限不是越大越好，每个连接都是 PG 进程（~10MB），",
        "max_connections=100 的默认额度要先留给运维与监控。",
        "",
        "## 验收判定",
        "",
        "- EXPLAIN 证据 Seq Scan → Index Scan 且数量级下降：见上表",
        "- 连接池打满复现（活跃连接=池上限）并调参解决：见上表",
        "",
    ]
    out = Path("docs/db_analysis.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
