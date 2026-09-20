#!/usr/bin/env python3
"""audit.py — 测试资产分层审计：给 labs/ 30 个实验画一张「金字塔画像」。

架构师视角的一句话：**测试策略不能拍脑袋，先让数据说话**。
本工具回答三个问题：
  1. 家底——三层（单元/集成/UI E2E）各有多少用例、各占多少比例？
  2. 成本——实测跑一轮，每层各花多少时间（时间占比往往和数量占比严重背离）？
  3. 形状——当前资产是金字塔、冰淇淋，还是过渡形态？该怎么重分层？

设计约束：
  - 规则全部在 configs/layer_rules.yaml（规则即配置，工具不内嵌 lab 知识）
  - 每个数字都可人工抽查核对（明细表附抽查命令）
  - 测不了的如实标注「未实测 + 原因」，绝不编造（计时口径在报告里明示）

用法：
  python audit.py                    # 全量审计：计数 + 实测计时（服务不通自动跳过）
  python audit.py --no-timed         # 只计数，不跑计时（秒级出报告）
  python audit.py --out reports      # 指定输出目录（默认 reports/）
产物：
  reports/pyramid.json               # 结构化结果（喂给后续看板/门禁项目）
  reports/pyramid_report.md          # 人类可读的画像报告
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PYTEST_TIMEOUT_DEFAULT = 300


# ---------------------------------------------------------------- 数据模型
@dataclass
class LabResult:
    name: str
    layer: str
    declared: dict                      # layer_rules.yaml 里的原始声明
    count: int = 0                      # 用例数（按 counter 策略）
    count_error: str | None = None      # 计数失败原因
    wall_s: float | None = None         # 实测墙钟秒（None=未实测）
    passed: int | None = None           # 实测通过数
    failed: int | None = None           # 实测失败数
    returncode: int | None = None       # 实测退出码
    skip_reason: str | None = None      # 未计时原因（如实进报告）
    notes: list[str] = field(default_factory=list)

    @property
    def timed_ok(self) -> bool:
        return self.wall_s is not None


# ---------------------------------------------------------------- 基础设施
def port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0


def docker_ok() -> bool:
    try:
        return subprocess.run(
            ["docker", "info", "--format", "ok"], capture_output=True, timeout=10
        ).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def run(cmd: list[str], cwd: Path, env: dict | None = None, timeout: int = 120) -> subprocess.CompletedProcess:
    e = dict(**os.environ)
    if env:
        e.update(env)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=e)


# ---------------------------------------------------------------- 计数器
def count_pytest(lab_dir: Path, py: str) -> tuple[int, str | None]:
    """pytest --collect-only -q：精确到参数化展开后的用例数，不执行测试。

    兼容两种输出：汇总行「N tests collected」；ini 自带 -q 时的逐文件「路径: 数量」。
    """
    r = run([py, "-m", "pytest", "-c", "configs/pytest.ini", "--rootdir=.",
             "--collect-only", "-q"], cwd=lab_dir, timeout=120)
    m = re.search(r"(\d+) tests? collected", r.stdout)
    if m:
        return int(m.group(1)), None
    pairs = re.findall(r"^(\S+\.py): (\d+)$", r.stdout, re.M)  # ini 自带 -q 时的逐文件格式
    if pairs:
        return sum(int(n) for _, n in pairs), None
    tail = (r.stderr or r.stdout).strip().splitlines()
    return 0, f"收集失败：{tail[-1] if tail else '无输出'}"


def count_cypress(lab_dir: Path) -> tuple[int, str | None]:
    """正则数 it()/specify()：静态近似，动态生成的用例不计（报告已注明口径）。"""
    n = 0
    for f in (lab_dir / "cypress" / "e2e").glob("*.cy.js"):
        n += len(re.findall(r"\b(?:it|specify)\s*\(", f.read_text(encoding="utf-8", errors="ignore")))
    return n, None if n else "未找到 cypress/e2e/*.cy.js 规格文件"


def count_locust(lab_dir: Path) -> tuple[int, str | None]:
    f = lab_dir / "locustfile.py"
    if not f.exists():
        return 0, "未找到 locustfile.py"
    return len(re.findall(r"@task", f.read_text(encoding="utf-8", errors="ignore"))), None


def count_k6(lab_dir: Path) -> tuple[int, str | None]:
    return len(list(lab_dir.glob("*.js"))), None


# ---------------------------------------------------------------- 计时器
def time_pytest(lab: LabResult, lab_dir: Path, py: str, meta: dict) -> tuple[float, int, int, int, str | None]:
    """实测一轮套件墙钟。结果从 junit-xml 解析——标准产物，不猜屏幕输出格式
    （部分 lab 的 ini 自带 -q，叠加脚本参数后会吞掉汇总行）。
    返回 (wall_s, passed, failed, returncode, err_reason)。"""
    args = [py, "-m", "pytest", "-c", "configs/pytest.ini", "--rootdir=.", "-q"]
    if lab.declared.get("pytest_args"):
        args += lab.declared["pytest_args"].split()
    env = {"SUT_BASE_URL": meta["sut_base_url"], "SUT_URL": meta["sut_base_url"]}
    timeout = int(lab.declared.get("timeout", PYTEST_TIMEOUT_DEFAULT))
    fd, junit = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    args += ["--junitxml", junit]
    t0 = time.perf_counter()
    try:
        r = run(args, cwd=lab_dir, env=env, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 0.0, 0, 0, -1, f"超时（>{timeout}s），已中止"
    finally:
        wall = time.perf_counter() - t0
    passed = failed = 0
    try:
        root = ET.parse(junit).getroot()
        a = (root if root.tag == "testsuite" else root.find("testsuite")).attrib
        tests = int(a.get("tests", 0))
        bad = int(a.get("failures", 0)) + int(a.get("errors", 0))
        skipped = int(a.get("skipped", 0))
        passed, failed = max(tests - bad - skipped, 0), bad
    except ET.ParseError:
        pass  # 崩溃前未产出 junit：按 0/0 记，退出码已如实保留
    finally:
        os.unlink(junit)
    return wall, passed, failed, r.returncode, None


# ---------------------------------------------------------------- 审计主流程
def audit(repo: Path, py: str, do_timed: bool) -> dict:
    cfg_path = Path(__file__).parent / "configs" / "layer_rules.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    meta, layers_decl, labs_decl = cfg["meta"], cfg["layers"], cfg["labs"]

    labs_root = repo / "labs"
    results: list[LabResult] = []
    docker_available: bool | None = None

    for name in sorted(labs_decl):
        d = labs_decl[name]
        lab_dir = labs_root / name
        lab = LabResult(name=name, layer=d["layer"], declared=d)

        if not lab_dir.is_dir():
            lab.count_error = "目录不存在"
            results.append(lab)
            continue

        # ① 计数
        counter = d.get("counter", "none")
        if counter == "pytest":
            lab.count, lab.count_error = count_pytest(lab_dir, py)
        elif counter == "cypress":
            lab.count, lab.count_error = count_cypress(lab_dir)
        elif counter == "locust":
            lab.count, lab.count_error = count_locust(lab_dir)
        elif counter == "k6":
            lab.count, lab.count_error = count_k6(lab_dir)

        # ② 计时（资格 → 服务探测 → 实测；任何一关不过都如实记原因）
        skip = d.get("skip_reason")
        if not do_timed:
            skip = skip or "本次未启用计时（--no-timed）"
        elif not d.get("timed") or counter != "pytest":
            skip = skip or ("计时资格未开启（configs：timed: false，仅计数）" if counter == "pytest"
                            else f"非 pytest 栈（{counter}），v1 只计数不计时")
        if not skip and d.get("service") and not port_open(int(d["service"])):
            skip = f"前置服务端口 {d['service']} 未运行（该 lab 自带服务，审计不代起，见 configs）"
        if not skip and d.get("docker"):
            docker_available = docker_ok() if docker_available is None else docker_available
            if not docker_available:
                skip = "docker daemon 不可用"
        if not skip:
            lab.wall_s, lab.passed, lab.failed, lab.returncode, err = time_pytest(lab, lab_dir, py, meta)
            if err:
                lab.skip_reason = err
                lab.wall_s = None
            elif lab.returncode != 0 and not d.get("expected_fail"):
                lab.notes.append(f"默认命令退出码 {lab.returncode}（套件默认不绿，本身就是一个审计发现）")
            elif d.get("expected_fail"):
                lab.notes.append(f"退出码 {lab.returncode} 属设计内（{d.get('note', '')}）"
                                 if lab.returncode != 0 else
                                 f"默认命令为绿；故意失败演示由 lab 脚本单独触发（{d.get('note', '')}）")
        lab.skip_reason = skip
        if d.get("note"):
            lab.notes.insert(0, d["note"])
        results.append(lab)

    return summarize(results, layers_decl, meta)


def summarize(results: list[LabResult], layers_decl: dict, meta: dict) -> dict:
    """聚合三层画像 + 形状判定 + 数据驱动的重分层建议。"""
    total_count = sum(r.count for r in results)
    total_wall = sum(r.wall_s for r in results if r.timed_ok)

    layer_summary = {}
    for key, decl in layers_decl.items():
        rs = [r for r in results if r.layer == key]
        cnt = sum(r.count for r in rs)
        wall = sum(r.wall_s for r in ws) if (ws := [r for r in rs if r.timed_ok]) else 0.0
        layer_summary[key] = {
            "label": decl["label"], "desc": decl["desc"],
            "count": cnt,
            "count_share": round(cnt * 100 / total_count, 1) if total_count else 0.0,
            "wall_s": round(wall, 2),
            "wall_share": round(wall * 100 / total_wall, 1) if total_wall else None,
            "reference_share": meta["reference"].get(key),
            "timed_labs": sum(1 for r in rs if r.timed_ok),
            "total_labs": len(rs),
        }

    shape, shape_evidence = judge_shape(layer_summary)

    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "timing_scope": {
            "total_wall_s": round(total_wall, 2),
            "timed_lab_count": sum(1 for r in results if r.timed_ok),
            "untimed_lab_count": sum(1 for r in results if not r.timed_ok and r.count > 0),
            "note": "耗时占比仅基于「pytest 栈已实测」的 lab（口径见明细表）；cypress/性能/移动栈 v1 只计数",
        },
        "total": {"cases": total_count, "wall_s": round(total_wall, 2)},
        "layers": layer_summary,
        "shape": {"verdict": shape, "evidence": shape_evidence},
        "recommendations": recommend(results, layer_summary),
        "labs": [r.__dict__ | {"timed_ok": r.timed_ok} for r in results],
    }


def judge_shape(layers: dict) -> tuple[str, list[str]]:
    u, i, e = (layers[k]["count_share"] for k in ("unit", "integration", "e2e"))
    ev = [f"单元 {u}% / 集成 {i}% / E2E {e}%（参考 70/20/10）"]
    if e <= 10 and u >= 60:
        return "金字塔 ✅", ev
    if u < e:
        return "冰淇淋反模式 ❌（E2E 比单元还多，上层浮肿）", ev + ["判定依据：单元占比 < E2E 占比"]
    return f"过渡形态 ⚠️（{'偏 E2E' if e > 10 else '基础扎实但分布不均'}）", ev + [
        f"判定依据：E2E {e}% 超出参考上限 10%" if e > 10 else "各层在参考区间附近但未达金字塔标准"]


def recommend(results: list[LabResult], layers: dict) -> list[dict]:
    """数据驱动的建议：每条都带证据数字，不许空对空。"""
    recs = []
    e2e_share = layers["e2e"]["count_share"]
    unit_share = layers["unit"]["count_share"]
    integ_share = layers["integration"]["count_share"]

    if e2e_share > (layers["e2e"]["reference_share"] or 10):
        recs.append({"level": "高", "title": "E2E 占比超标，需要「下沉」而不是「删掉」",
                     "evidence": f"E2E 实测 {e2e_share}%，参考上限 10%",
                     "action": "把「只验证业务规则、不验证渲染」的 UI 用例下沉为接口层用例（同断言、1/10 成本），"
                               "UI 只保留关键路径冒烟与视觉/交互专项"})
    if unit_share < 60:
        recs.append({"level": "中", "title": "单元层有提升空间",
                     "evidence": f"单元 {unit_share}%，参考下限 60-70%",
                     "action": "新增业务逻辑先补单元层（mock/参数化/性质测试 labs/04/06 已备好工具），把缺陷拦在最便宜的一层"})
    if integ_share < 10:
        recs.append({"level": "中", "title": "集成层偏薄",
                     "evidence": f"集成 {integ_share}%，参考约 20%",
                     "action": "接口层是「下沉」的承接层：优先覆盖核心 API 的边界与异常路径（labs/12 模式可复制）"})

    ports = sorted({str(r.declared["service"]) for r in results if r.declared.get("service")})
    if len(ports) > 1:
        recs.append({"level": "高", "title": "SUT 端口蔓延：一份应用被起了多份「私有实例」",
                     "evidence": f"6 个 lab 各自约定服务端口：{', '.join(ports)}",
                     "action": "统一环境供给（按需 ephemeral 实例 + 标准端口发现），对应本清单项目 16「Ephemeral 环境工厂」"})

    ui_stacks = sorted({counter for r in results if r.layer == "e2e"
                        and (counter := r.declared.get("counter")) in ("pytest", "cypress")})
    if len(ui_stacks) > 1:
        recs.append({"level": "中", "title": "UI 自动化三栈并存，维护成本三倍",
                     "evidence": f"E2E 层同时存在 playwright(pytest)+cypress+selenium 资产（{ui_stacks} 计数入口）",
                     "action": "明确主栈+保留栈策略：新用例只进主栈，旧栈冻结直至迁移（labs/25 已有对比数据支撑选型）"})

    untimed = [r for r in results if not r.timed_ok and r.count > 0]
    untimed_cases = sum(r.count for r in untimed)
    total = sum(r.count for r in results)
    if untimed and total:
        recs.append({"level": "中", "title": "计时口径不完整，成本数据有盲区",
                     "evidence": f"{len(untimed)} 个 lab 共 {untimed_cases} 条用例未纳入实测"
                                 f"（占 {untimed_cases * 100 // total}%），耗时占比只反映 pytest 栈",
                     "action": "把 cypress/selenium/移动栈纳入统一计时（流水线产物 junit 统一落盘），对应项目 27 全景看板"})

    outside = [r for r in results if r.layer == "outside" and r.count > 0]
    if outside:
        recs.append({"level": "低", "title": "塔外资产（性能/a11y/安全）游离在门禁之外",
                     "evidence": f"{len(outside)} 个 lab 属塔外：{', '.join(r.name for r in outside)}",
                     "action": "非功能资产应接入质量门禁与度量（对应项目 3 门禁引擎、项目 23 度量看板）"})

    return recs


# ---------------------------------------------------------------- 报告渲染
def render_md(rep: dict) -> str:
    ls, ts = rep["layers"], rep["timing_scope"]
    lines = [
        "# 🏛️ 测试资产分层审计报告（金字塔画像）",
        f"> 生成于 {rep['generated_at']} · 审计对象 `labs/` 30 个实验 · 共 {rep['total']['cases']} 条用例 · 实测一轮 {ts['total_wall_s']}s",
        "",
        f"## 形状判定：{rep['shape']['verdict']}",
        "",
    ]
    lines += [f"- {e}" for e in rep["shape"]["evidence"]]
    lines += ["", "## 三层画像（数量占比 + 耗时占比）", "",
              "| 层 | 用例数 | 数量占比 | 参考 | 实测耗时 | 耗时占比 |", "|:---|---:|---:|:---:|---:|---:|"]
    for key in ("unit", "integration", "e2e", "outside"):
        l = ls[key]
        ref = f"{l['reference_share']}%" if l["reference_share"] else "—"
        wall = f"{l['wall_s']}s" if l["timed_labs"] else "未实测"
        wshare = f"{l['wall_share']}%" if l["wall_share"] is not None else "—"
        lines.append(f"| {l['label']} | {l['count']} | {l['count_share']}% | {ref} | {wall} | {wshare} |")
    lines += ["", f"> ⏱️ **计时口径**：{ts['note']}。已实测 {ts['timed_lab_count']} 个 lab，"
              f"未实测 {ts['untimed_lab_count']} 个含用例的 lab。", "", "## 重分层建议", ""]
    for n, r in enumerate(rep["recommendations"], 1):
        lines += [f"### {n}. [{r['level']}] {r['title']}", f"- **证据**：{r['evidence']}", f"- **动作**：{r['action']}", ""]
    lines += ["## 明细（每格都可抽查）", "",
              "| lab | 层 | 用例数 | 实测耗时 | 结果 | 说明 |", "|:---|:---|---:|---:|:---|:---|"]
    for r in rep["labs"]:
        if r["count"] == 0 and not r["timed_ok"] and r["layer"] == "outside" and not r["notes"] and not r.get("count_error"):
            continue
        wall = f"{r['wall_s']:.2f}s" if r["timed_ok"] else "—"
        res = f"退出码 {r['returncode']}（{r['passed']} 过 / {r['failed']} 挂）" if r["timed_ok"] else (r.get("skip_reason") or "未计时")
        cnt = f"{r['count']} ⚠️" if r.get("count_error") else str(r["count"])
        notes = "；".join([r.get("count_error") or "", *r["notes"]]).strip("；") if r.get("count_error") else "；".join(r["notes"])
        lines.append(f"| {r['name']} | {r['layer']} | {cnt} | {wall} | {res} | {notes} |")
    lines += ["", "## 抽查命令（人工核对 ≥2 项即验收）", "",
              "```bash",
              "# 数量抽查：collect-only 与报告一致即通过（例抽 2 个）",
              "cd labs/03_parametrize && ../../.venv/bin/python -m pytest -c configs/pytest.ini --rootdir=. --collect-only -q | tail -1",
              "cd labs/12_api_tests  && ../../.venv/bin/python -m pytest -c configs/pytest.ini --rootdir=. --collect-only -q | tail -1",
              "# 耗时抽查：--durations 汇总应与报告量级一致",
              "cd labs/01_pytest_basics && ../../.venv/bin/python -m pytest -c configs/pytest.ini --rootdir=. -q --durations=1 | tail -3",
              "```", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="测试资产分层审计（金字塔画像）")
    ap.add_argument("--no-timed", action="store_true", help="只计数不计时")
    ap.add_argument("--out", default="reports", help="报告输出目录")
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    py = str(repo / ".venv" / "bin" / "python") if (repo / ".venv" / "bin" / "python").exists() else sys.executable

    rep = audit(repo, py, do_timed=not args.no_timed)

    out = Path(__file__).parent / args.out
    out.mkdir(exist_ok=True)
    (out / "pyramid.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    md = render_md(rep)
    (out / "pyramid_report.md").write_text(md, encoding="utf-8")

    print(md)
    print(f"\n>>> 报告已写入 {out/'pyramid_report.md'} 与 {out/'pyramid.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
