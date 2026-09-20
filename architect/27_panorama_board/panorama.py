#!/usr/bin/env python3
"""panorama.py — 效能全景看板：一条命令聚合 architect/ 各项目产物，缺失明示不编造。

架构师视角的一句话：**「你们测试体系整体什么样」的答案要能一条命令跑出来**——
本工具按指标字典从兄弟项目采集真实产物；产物缺失时自动调用对应项目的轻量模式
再生成（并在看板标注「本轮生成」），连轻量模式都不具备的直接标「数据缺失」。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent
REPO = BASE.parents[1]
PY = str(REPO / ".venv" / "bin" / "python")

# 每个 collector：(来源项目, 产物路径, 生成命令(轻量), 指标提取器)
def _j(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


COLLECTORS = [
    ("01 分层审计", "../../architect/01_pyramid_audit/reports/pyramid.json",
     "audit.py --no-timed",
     lambda d: {"总用例数": d["total"]["cases"],
                "分层比例": f"{d['layers']['unit']['count_share']}/{d['layers']['integration']['count_share']}/{d['layers']['e2e']['count_share']}%",
                "形状判定": d["shape"]["verdict"].split("（")[0]}),
    ("02 风险策略", "../../architect/02_risk_strategy/reports/strategy.json",
     "strategy.py",
     lambda d: {"风险分布": " · ".join(f"{k}×{v}" for k, v in d["distribution"].items() if v)}),
    ("03 质量门禁", "../../architect/03_quality_gate/reports/gate.json",
     "gate.py",
     lambda d: {"门禁裁决": d["verdict"],
                "数据层覆盖率": f"{next(r['measured'] for r in d['rules'] if r['id'] == 'coverage_total')}%"}),
    ("13 flaky 平台", "../../architect/13_flaky_platform/reports/flaky.json",
     "flaky_platform.py detect --rounds 3",
     lambda d: {"flaky 率": f"{d['flaky_rate_pct']}%（3 轮轻量检测）"}),
    ("20 压测容量", "../../architect/20_load_model/reports/capacity.json",
     "load_model.py",
     lambda d: {"实测容量": f"{d['capacity_tps']:.0f} TPS",
                "推荐水位": f"{d['watermark_tps']:.0f} TPS"}),
    ("22 安全门禁", "../../architect/22_security_gate/reports/sec.json",
     "secgate.py",
     lambda d: {"安全裁决": "PASS" if d["passed"] else "FAIL",
                "CVE 拦截": f"{sum(1 for b in d['blocking'] if 'CVE' in b)} 条"}),
]

OPTIONAL_HINT = {"20 压测容量": "需 SUT 在 :8899（./load_model.sh apply）"}


def ensure_source(rel: str, gen_cmd: str, auto: bool, project: str) -> Path | None:
    p = (BASE / rel).resolve()
    if p.exists() or not auto:
        return p if p.exists() else None
    cwd = (BASE / rel).resolve().parents[1]
    print(f"  [生成] {project} → {gen_cmd}", flush=True)
    subprocess.run([PY, *gen_cmd.split()], cwd=cwd, capture_output=True, text=True,
                   timeout=600, check=False)
    return p if p.exists() else None


def collect(auto: bool) -> tuple[list[dict], list[dict]]:
    panels, missing = [], []
    for project, rel, gen_cmd, extract in COLLECTORS:
        src = ensure_source(rel, gen_cmd, auto, project)
        if src is None:
            missing.append({"project": project, "note": OPTIONAL_HINT.get(project, "先运行对应项目生成产物")})
            continue
        try:
            metrics = extract(_j(src))
            panels.append({"project": project, "metrics": metrics, "source": str(src)})
        except Exception as e:
            missing.append({"project": project, "note": f"解析失败 {type(e).__name__}: {e}"})
    return panels, missing


def render(panels: list[dict], missing: list[dict], secs: float, auto: bool) -> str:
    cards = ""
    for p in panels:
        rows = "".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in p["metrics"].items())
        cards += f"""<div class="panel"><h2>{p['project']}</h2>
<table>{rows}</table><p class="src">{p['source']}</p></div>"""
    miss = "".join(f'<div class="panel miss"><h2>{m["project"]}</h2><p>⚠️ 数据缺失：{m["note"]}</p></div>'
                   for m in missing)
    return f"""<!doctype html><html lang="zh"><head><meta charset="utf-8"><title>测试效能全景</title>
<style>body{{font-family:-apple-system,sans-serif;background:#101820;color:#e8eef4;margin:24px}}
h1{{color:#7fd1b9}} .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:16px}}
.panel{{background:#1a2634;border-radius:10px;padding:16px}} .panel h2{{margin:0 0 10px;font-size:18px;color:#9fc5e8}}
.panel.miss{{border:1px dashed #c0392b}} table{{width:100%;border-collapse:collapse;font-size:14px}}
td{{padding:4px 6px;border-bottom:1px solid #2a3a4a}} td:last-child{{text-align:right;color:#7fd1b9}}
.src{{font-size:10px;color:#5a6a7a;font-family:monospace;margin:8px 0 0}}</style></head><body>
<h1>🏛️ 测试效能全景看板</h1>
<p>生成于 {time.strftime('%Y-%m-%d %H:%M:%S')} · {len(panels)} 个面板 {len(missing)} 个缺失 ·
聚合耗时 {secs:.1f}s · {"含本轮自动生成" if auto else "只读现有产物"}</p>
<div class="grid">{cards}{miss}</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser(description="效能全景看板")
    ap.add_argument("--no-auto", action="store_true", help="只读现有产物，不自动生成")
    ap.add_argument("--out", default=str(BASE / "reports"))
    args = ap.parse_args()

    t0 = time.perf_counter()
    panels, missing = collect(auto=not args.no_auto)
    secs = time.perf_counter() - t0
    html = render(panels, missing, secs, auto=not args.no_auto)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "panorama.html").write_text(html, encoding="utf-8")
    (out / "panorama.json").write_text(json.dumps(
        {"panels": panels, "missing": missing}, ensure_ascii=False, indent=2), encoding="utf-8")

    n_metrics = sum(len(p["metrics"]) for p in panels)
    print(f"# 🏛️ 效能全景：{len(panels)} 面板 / {n_metrics} 指标 / 缺失 {len(missing)}（聚合 {secs:.1f}s）")
    for p in panels:
        for k, v in p["metrics"].items():
            print(f"- {p['project']} · {k}: {v}")
    for m in missing:
        print(f"- ⚠️ {m['project']}: 数据缺失（{m['note']}）")
    print(f">>> 看板已写入 {out/'panorama.html'}")
    ok = n_metrics >= 8
    print(f"{'✅ 验收通过' if ok else '❌ 指标不足 8'}（指标 ≥8 且缺失明示）")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
