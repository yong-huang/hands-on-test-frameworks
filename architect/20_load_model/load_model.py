#!/usr/bin/env python3
"""load_model.py — 从业务流量到压测模型：推导目标 TPS → 生成 k6 场景 → 实测容量。

架构师视角的一句话：**压测方案题的标准链路是「流量估算 → 模型设计 → 场景选择 →
容量结论」**，每一步都有推导而不是拍脑袋：
  1. 均值 QPS = DAU × 人均请求 ÷ 86400
  2. 峰值 QPS = 均值 × 峰值系数（二八原则：80% 流量挤在 20% 时间）
  3. 压测目标 = 峰值 × 安全系数（大促/突发余量）
  4. 容量结论 = 实测「P95 ≤ 预算」的最大吞吐，推荐水位 = 容量 × 水位系数
推导过程写进生成的 k6 脚本注释——场景即代码，推导即注释。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
K6 = "k6"
GEN = Path(__file__).parent / "generated"

K6_TEMPLATE = """
// ⚠️ 本文件由 load_model.py 生成——所有数字都带推导，不要手改
// 业务输入：DAU={dau}，人均请求 {rpu}/日
// 均值 QPS = {dau} × {rpu} ÷ 86400 = {avg:.1f}
// 峰值 QPS = 均值 × 峰值系数{pf}（二八原则）= {peak:.1f}
// 压测目标 = 峰值 × 安全系数{sf} = {target:.1f}
// 容量结论：见 reports/capacity.md（由多档速率实测得出）
import http from 'k6/http';

export const options = {{
  scenarios: {{
    steady: {{
      executor: 'constant-arrival-rate',
      rate: __ENV.RATE,              // 目标吞吐（每秒请求数），由调度器注入
      timeUnit: '1s',
      duration: '12s',
      preAllocatedVUs: Number(__ENV.RATE) * 2 + 20,
      maxVUs: Number(__ENV.RATE) * 4 + 50,
    }},
  }},
  thresholds: {{
    http_req_duration: ['p(95)<{budget}'],   // P95 预算：{budget}ms
  }},
}};

export default function () {{
  http.get('{base}/api/orders?limit=20');
}}

// 摘要落盘：调度器经 OUT 环境变量指定路径（--summary-export 在 k6 v2 已废弃）
export function handleSummary(data) {{
  return {{ [__ENV.OUT]: JSON.stringify({{
    p95_ms: data.metrics.http_req_duration.values['p(95)'],
    count: data.metrics.http_reqs.values.count,
    fail_rate: (data.metrics.http_req_failed || {{values:{{rate:0}}}}).values.rate,
  }}) }};
}}
"""


def derive(cfg: dict) -> dict:
    b, t = cfg["business"], cfg["traffic"]
    avg = b["dau"] * b["requests_per_user"] / 86400
    peak = avg * t["peak_factor"]
    target = peak * t["safety_factor"]
    return {"avg": avg, "peak": peak, "target": target,
            "dau": b["dau"], "rpu": b["requests_per_user"],
            "pf": t["peak_factor"], "sf": t["safety_factor"],
            "budget": cfg["latency_budget_ms"]}


def write_k6(d: dict, base: str) -> Path:
    GEN.mkdir(parents=True, exist_ok=True)
    script = GEN / "orders_load.js"
    script.write_text(K6_TEMPLATE.format(base=base, **d), encoding="utf-8")
    return script


def run_k6(script: Path, rate: int, budget: int) -> dict:
    """k6 以恒定到达率跑 12s，从 summary 导出吞吐与 P95。"""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        out = tf.name
    r = subprocess.run(
        [K6, "run", "--quiet", "-e", f"RATE={rate}", "-e", f"OUT={out}", str(script)],
        capture_output=True, text=True, timeout=300, check=False)
    try:
        d = json.loads(Path(out).read_text())       # handleSummary 写出的扁平结构
        p95 = float(d["p95_ms"])
        count = int(d["count"])
        fails = float(d.get("fail_rate", 0))
    except Exception:
        p95, count, fails = 1e9, 0, 1.0
    finally:
        Path(out).unlink(missing_ok=True)
    actual_rate = count / 12.0
    return {"rate_target": rate, "rate_actual": round(actual_rate, 1),
            "p95_ms": round(p95, 1) if p95 < 1e8 else None,
            "error_rate": round(fails, 4),
            "within_budget": p95 is not None and p95 <= budget and fails < 0.01,
            "rc": r.returncode}


def main() -> int:
    ap = argparse.ArgumentParser(description="从业务流量到压测模型")
    base = Path(__file__).parent
    ap.add_argument("--out", default=str(base / "reports"))
    args = ap.parse_args()

    cfg = yaml.safe_load((base / "configs/business.yaml").read_text(encoding="utf-8"))
    d = derive(cfg)
    budget = d["budget"]
    base_url = "http://127.0.0.1:8899"
    print(f"# 📈 流量推导：均值 {d['avg']:.1f} → 峰值 {d['peak']:.1f} → 压测目标 {d['target']:.0f} TPS"
          f"（P95 预算 {budget}ms）")

    script = write_k6(d, base_url)
    print(f"k6 场景已生成（含推导注释）：{script}")

    results = []
    for mult in cfg["capacity"]["probe_rates"]:
        rate = max(int(d["target"] * mult), 5)
        print(f"probe：恒定 {rate} TPS × 12s ...", flush=True)
        res = run_k6(script, rate, budget)
        results.append(res)
        print(f"  实际吞吐 {res['rate_actual']} TPS，P95 {res['p95_ms']}ms，"
              f"错误率 {res['error_rate']:.1%} → {'✅ 预算内' if res['within_budget'] else '❌ 超预算/打挂'}")

    passing = [r for r in results if r["within_budget"]]
    capacity = max((r["rate_actual"] for r in passing), default=0)
    watermark = round(capacity * cfg["capacity"]["watermark"])
    verdict = (f"当前配置最大可承载 **{capacity:.0f} TPS**（P95≤{budget}ms 实测依据），"
               f"推荐水位 **{watermark:.0f} TPS**（容量的 "
               f"{cfg['capacity']['watermark']:.0%}，留波动与退化余量）。"
               f"对照压测目标 {d['target']:.0f} TPS："
               + ("容量达标，可承接目标流量" if capacity >= d["target"]
                  else "容量不足——目标流量下 P95 将超预算，需扩容或优化"))
    print(f"\n# 🏁 容量结论\n{verdict}")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "capacity.json").write_text(json.dumps(
        {"derive": d, "probes": results, "capacity_tps": capacity,
         "watermark_tps": watermark, "verdict": verdict},
        ensure_ascii=False, indent=2), encoding="utf-8")
    ok = capacity > 0
    print(f"\n{'✅ 容量结论有实测依据' if ok else '❌ 未能测得容量'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
