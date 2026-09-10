#!/usr/bin/env python3
"""汇总封闭/开放/尖峰/locust 各轮 summary-export JSON → docs/modeling.md。

输出：两套模型的 RPS/P95 对照表、自动配对最近吞吐档位的 P95 差异、
尖峰场景平稳期 vs 尖峰期对比，以及 Coordinated Omission 解释章节。
"""
import csv
import json
import sys
from pathlib import Path


def load(path):
    with open(path) as f:
        return json.load(f)


def m(data):
    mm = data["metrics"]
    dur = mm["http_req_duration"]
    return {
        "rps": round(mm["http_reqs"].get("rate", 0), 1),
        "p50": round(dur["med"], 1),
        "p95": round(dur["p(95)"], 1),
        "p99": round(dur["p(99)"], 1),
        "err": round(mm["http_req_failed"].get("rate", mm["http_req_failed"].get("value", 0)) * 100, 2),
    }


def m_locust(csv_prefix):
    """解析 locust --csv 的 _stats.csv，取 Aggregated 行。"""
    path = Path("reports") / f"{csv_prefix}_stats.csv"
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["Name"] == "Aggregated":
                # locust 的分位数列本来就是 ms，直接取
                ms = lambda h: round(float(row.get(h, 0)), 1)
                return {
                    "rps": round(float(row["Requests/s"]), 1),
                    "p50": ms("50%"),
                    "p95": ms("95%"),
                    "p99": ms("99%"),
                    "err": round(float(row["Failure Count"]) / max(float(row["Request Count"]), 1) * 100, 2),
                }
    raise SystemExit(f"{path} 里没有 Aggregated 行")


def main():
    r = Path("reports")
    rows = []
    # 参数按文件名约定：closed_VU{N}.json / open_RATE{N}.json / spike.json / locust_VU{N}.json
    for p in sorted(r.glob("closed_VU*.json")):
        d = m(load(p))
        rows.append(("封闭", p.stem.split("_")[1], d))
    for p in sorted(r.glob("open_RATE*.json")):
        d = m(load(p))
        rows.append(("开放", f"{p.stem.split('_')[1][4:]} it/s", d))
    for p in sorted(Path("reports").glob("locust_VU50_stats.csv")):
        d = m_locust(p.stem.replace("_stats", ""))
        rows.append(("封闭(Locust)", "50 VU", d))

    lines = [
        "# 02 · 负载建模：开放 vs 封闭模型对比报告",
        "",
        "- 每轮 40s，场景动作完全一致（浏览+详情+半概率下单），只有执行模型不同",
        "",
        "| 模型 | 档位 | 实测 RPS | P50(ms) | P95(ms) | P99(ms) | 错误率% |",
        "|:---|:---|---:|---:|---:|---:|---:|",
    ]
    for model, gear, d in rows:
        lines.append(f"| {model} | {gear} | {d['rps']} | {d['p50']} | {d['p95']} | {d['p99']} | {d['err']} |")

    # 自动配对：取每档封闭模型，找实测 RPS 最接近的开放档，对比 P95
    closed = [x for x in rows if x[0].startswith("封闭") and not x[0].endswith("(Locust)")]
    opened = [x for x in rows if x[0] == "开放"]
    if closed and opened:
        lines += ["", "## 最近吞吐配对：P95 差异（本实验验收点）", "",
                  "| 配对（吞吐≈） | 封闭 P95 | 开放 P95 | 差异 |", "|:---|---:|---:|---:|"]
        for cm, gear, cd in closed:
            best = min(opened, key=lambda o: abs(o[2]["rps"] - cd["rps"]))
            diff = round(best[2]["p95"] - cd["p95"], 1)
            lines.append(
                f"| {gear} vs {best[1]}（{cd['rps']}≈{best[2]['rps']} req/s） "
                f"| {cd['p95']} | {best[2]['p95']} | +{diff}ms |")

    spike = m(load(r / "spike.json")) if (r / "spike.json").exists() else None
    if spike:
        lines += [
            "",
            "## 尖峰场景（ramping-arrival-rate 30→400→30 it/s）",
            "",
            f"- 全程聚合 P95：{spike['p95']}ms，P99：{spike['p99']}ms，错误率：{spike['err']}%",
            "- 平稳期基线 P95≈130ms（项目 1 实测），尖峰把延迟与错误顶起即是验收证据；",
            "  k6 文本输出的逐段进度行可见吞吐/延迟随阶段跳变。",
        ]

    lines += [
        "",
        "## 为什么两套模型的 P95 对不上（Coordinated Omission）",
        "",
        "- 封闭模型：VU 收到响应才发下一单。SUT 一变慢，VU 自动放慢发送节奏，",
        "  **排队被藏进'思考'里**——压测机成了 SUT 的节流阀，P95 被系统性低估。",
        "- 开放模型：到达率恒定，SUT 变慢只会让请求在队列里排队，延迟如实入账。",
        "- 这就是 Coordinated Omission：压测端与 SUT '合谋'跳过了本该发出的请求，",
        "  生产环境（用户不会因为你慢就停止刷新）不会给你这个体面。结论：",
        "  **容量结论以开放模型为准，封闭模型用于定位并发下的行为特征。**",
        "",
    ]
    out = Path("docs/modeling.md")
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("\n".join(lines))
    print(f"\n报告已写入 {out}")


if __name__ == "__main__":
    sys.exit(main())
