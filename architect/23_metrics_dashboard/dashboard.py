#!/usr/bin/env python3
"""dashboard.py — 质量度量看板：指标字典驱动的静态 HTML 生成器。

架构师视角的一句话：**看板不是图表堆，是指标字典的渲染**——每个指标必须能回答
三件事：公式是什么（防口径之争）、数据从哪来（可抽查核对）、怎么防造假
（anti-gaming）。数据缺失就明示「数据缺失」，绝不编数。

采集原则：只读兄弟项目的产物 JSON（01 审计 / 03 门禁 / 13 flaky），来源路径写在
字典里——「数值与原始产物一致」是抽查验收的标准动作。
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import yaml

BASE = Path(__file__).parent


def resolve(source: str) -> Path:
    return (BASE / source).resolve()


def dig(data, path: str):
    """支持 layers / total.cases / rules[0].measured 三种路径。"""
    cur = data
    for seg in path.replace("]", "").replace("[", ".").split("."):
        if seg == "":
            continue
        cur = cur[int(seg)] if seg.isdigit() else cur[seg]
    return cur


def collect() -> list[dict]:
    cfg = yaml.safe_load((BASE / "configs/metrics.yaml").read_text(encoding="utf-8"))
    out = []
    for m in cfg["metrics"]:
        src = resolve(m["source"])
        if src.exists():
            try:
                value = dig(json.loads(src.read_text(encoding="utf-8")), m["field"])
                if isinstance(value, dict) and m["id"] == "layered_ratio":
                    value = {k: f"{v['count_share']}%" for k, v in value.items()
                             if k in ("unit", "integration", "e2e")}
            except Exception as e:
                value = f"解析失败：{type(e).__name__}"
        else:
            value = "数据缺失（来源产物不存在——先跑 apply 生成）"
        out.append({**m, "value": value})
    return out


def render_html(metrics: list[dict]) -> str:
    cards = ""
    for m in metrics:
        v = m["value"]
        if isinstance(v, dict):
            v = " / ".join(f"{k}:{x}" for k, x in v.items())
        missing = isinstance(v, str) and "缺失" in v
        cards += f"""
    <div class="card">
      <h3>{m['name']}</h3>
      <div class="value">{"⚠️ " + v if missing else v}</div>
      <p class="meta"><b>公式</b>：{m['formula']}</p>
      <p class="meta"><b>防造假</b>：{m['anti_gaming']}</p>
      <p class="src">来源：{m['source']}</p>
    </div>"""
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>质量度量看板</title><style>
body {{ font-family: -apple-system, sans-serif; background: #f4f6f8; margin: 24px; }}
h1 {{ color: #1a2b3c }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
.card {{ background: #fff; border-radius: 10px; padding: 18px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
.card h3 {{ margin: 0 0 8px; color: #444 }}
.value {{ font-size: 26px; font-weight: 700; color: #0a7d38; margin: 6px 0; }}
.meta {{ font-size: 12px; color: #666; margin: 4px 0 }}
.src {{ font-size: 11px; color: #999; font-family: monospace }}
footer {{ color: #999; font-size: 12px; margin-top: 20px }}
</style></head><body>
<h1>🏛️ 质量度量看板</h1>
<p>生成于 {time.strftime('%Y-%m-%d %H:%M:%S')} · 指标 {len(metrics)} 个 ·
每个指标：公式 + 实测值 + 数据来源（可抽查核对）</p>
<div class="grid">{cards}</div>
<footer>architect/23_metrics_dashboard · 数据缺失时明示缺失，绝不编数</footer>
</body></html>"""


def main() -> int:
    metrics = collect()
    missing = [m["name"] for m in metrics if isinstance(m["value"], str) and "缺失" in m["value"]]
    html = render_html(metrics)
    out = BASE / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "dashboard.html").write_text(html, encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, default=str),
                                      encoding="utf-8")

    print(f"# 🏛️ 质量度量看板：{len(metrics)} 个指标")
    for m in metrics:
        v = m["value"]
        v = " / ".join(f"{k}:{x}" for k, x in v.items()) if isinstance(v, dict) else v
        print(f"- {m['name']}: {v}")
    if missing:
        print(f"⚠️ 数据缺失：{', '.join(missing)}（已如实标注，未编数）")
        return 2
    print(f">>> 看板已写入 {out/'dashboard.html'}（浏览器直接打开）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
