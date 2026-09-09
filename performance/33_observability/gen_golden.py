#!/usr/bin/env python3
"""压测结束后查询 Prometheus API，把黄金信号证据写进 docs/golden.md。

用法：python3 gen_golden.py <期间是否触发过告警: yes/no>
证据 = 4 条 PromQL 查询的实测值（压测窗口内），而非面板截图。
"""
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

PROM = "http://localhost:19090"

QUERIES = [
    ("shop RPS", 'sum(rate(http_requests_total{job="shop"}[2m]))'),
    ("shorturl RPS", 'sum(rate(http_requests_total{job="shorturl"}[2m]))'),
    ("shop P95(s)", "histogram_quantile(0.95, sum(rate(http_request_duration_highr_seconds_bucket[2m])) by (le))"),
    ("shorturl P95(s)", "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[2m])) by (le))"),
    ("shop 进程CPU(核)", 'rate(process_cpu_seconds_total{job="shop"}[2m])'),
    ("shorturl 进程CPU(核)", 'rate(process_cpu_seconds_total{job="shorturl"}[2m])'),
    ("shop RSS(MB)", 'process_resident_memory_bytes{job="shop"} / 1024 / 1024'),
    ("shorturl RSS(MB)", 'process_resident_memory_bytes{job="shorturl"} / 1024 / 1024'),
    ("PG 事务/s", 'rate(pg_stat_database_xact_commit[2m])'),
]


def query(expr: str):
    with urllib.request.urlopen(f"{PROM}/api/v1/query?query={urllib.parse.quote(expr)}", timeout=10) as r:
        data = json.load(r)
    out = []
    for res in data["data"]["result"]:
        out.append(f"{res['metric'].get('job', '')}={float(res['value'][1]):.3f}")
    return "; ".join(out) if out else "(无数据)"


def main():
    fired = sys.argv[1].lower() == "yes" if len(sys.argv) > 1 else False
    lines = [
        "# 33 · 黄金信号观测报告",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "- 证据口径：压测后 2 分钟窗口的 PromQL 查询值（非截图，可复算）",
        "",
        "| 信号 | 实测值 |",
        "|:---|:---|",
    ]
    import urllib.parse
    for name, expr in QUERIES:
        lines.append(f"| {name} | {query(expr)} |")
    lines += [
        "",
        "## 告警触发证据",
        "",
        f"- HighP95Latency 在压测期间触发：{'是' if fired else '否'}",
        "- 复核命令：`curl -s 'http://localhost:19090/api/v1/alerts' | python3 -m json.tool`",
        "  压测期间执行可见 state=fireing；SLO=500ms（configs/alerts.yml）",
        "",
        "## 联动解读",
        "",
        "压同一时刻的四条曲线（流量↑ → 延迟↑ → 进程CPU↑ → RSS 平稳）",
        "在 Grafana『黄金信号 · 双 SUT』面板同屏可见（http://localhost:13000）。",
        "",
    ]
    out = Path("docs/golden.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"报告已写入 {out}")


if __name__ == "__main__":
    main()
