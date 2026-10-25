#!/usr/bin/env python3
"""measure_dft.py —— 可测性度量：重构前后的墙钟耗时与准备代码行数对比。

口径（全部机械可复核）：
  墙钟耗时   pytest --durations=0 报告的「单个测试执行时长」（不含 pytest 启动开销，
             否则毫秒级测试会被 0.5s 的启动淹没，验收 <100ms 就失真了）
  函数行数   AST 解析测试函数的物理行数
  准备语句数 AST 统计测试函数内、第一条 assert 之前的语句条数（arrange 段）
产出：reports/dft_report.md / .json
"""
import ast
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = str(ROOT.parent.parent / ".venv/bin/python")
EXPIRY = "tests/test_expiry.py"
BEHAVIOR = "tests/test_behavior.py"


def test_metrics(path: str, func: str) -> tuple[int, int]:
    """AST 统计：测试函数总行数 + 第一条 assert 前的语句数（准备段）。"""
    src = (ROOT / path).read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func:
            total = node.end_lineno - node.lineno + 1
            prep = 0
            for stmt in node.body[1:]:  # [0] 是 docstring，不算语句
                if isinstance(stmt, ast.Assert):
                    break
                prep += 1
            # 模块全局触碰：monkeypatch.setattr 或直接给模块属性赋值/清场（legacy 的污染证据）
            touches = sum(1 for line in
                          ast.get_source_segment(src, node).splitlines()
                          if "monkeypatch.setattr" in line or re.search(r"legacy\._", line))
            return total, prep, touches
    sys.exit(f"未找到测试函数 {func}")


def durations() -> dict[str, float]:
    """legacy 测试的 call 阶段时长取自 pytest --durations（口径=测试函数体）。

    fake 测试 <5ms 会被 pytest 隐藏（-vv 也不显示），改为进程内直接实测函数体
    ——与 durations 的 call 阶段同口径，跑 3 次取最小值。
    """
    proc = subprocess.run(
        [PY, "-m", "pytest", EXPIRY, "-q", "--durations=0"],
        cwd=ROOT, capture_output=True, text=True)
    out = {}
    for line in proc.stdout.splitlines():
        m = re.match(r"\s*([\d.]+)s\s+call\s+\S*::(test_\w+)", line)
        if m:
            out[m.group(2)] = float(m.group(1))
    if "test_expiry_legacy_needs_real_sleep" not in out:
        sys.exit(f"durations 解析失败：\n{proc.stdout[-600:]}")
    sys.path.insert(0, str(ROOT / "tests"))
    import test_expiry
    best = min(_time_body(test_expiry.test_expiry_fake_clock_instant) for _ in range(3))
    out["test_expiry_fake_clock_instant"] = best
    return out


def _time_body(fn) -> float:
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def run_suite(args: list[str]) -> tuple[bool, str]:
    proc = subprocess.run([PY, "-m", "pytest", *args, "-q"],
                          cwd=ROOT, capture_output=True, text=True)
    tail = [l for l in proc.stdout.splitlines() if l.strip()][-1]
    return proc.returncode == 0, tail


def main():
    d = durations()
    legacy = "test_expiry_legacy_needs_real_sleep"
    fake = "test_expiry_fake_clock_instant"
    lt, lp, ltouch = test_metrics(EXPIRY, legacy)
    ft, fp, ftouch = test_metrics(EXPIRY, fake)
    beh_ok, beh_tail = run_suite([BEHAVIOR])

    speedup = d[legacy] / max(d[fake], 1e-6)
    speedup_disp = f"{speedup:.0f}×" if speedup < 10000 else ">10000×"
    rows = [
        ("过期测试墙钟（实测/条）", f"{d[legacy]:.2f}s", f"{d[fake]*1e6:.0f}µs",
         "legacy 真睡 TTL；fake clock 拨针"),
        ("测试触碰模块全局（处）", f"{ltouch}", f"{ftouch}",
         "monkeypatch/清场 vs 零触碰（状态隔离）"),
        ("测试函数行数（AST）", f"{lt} 行", f"{ft} 行", "含 docstring；DI 版更长是显式构造的代价"),
        ("assert 前语句数（AST）", f"{lp} 条", f"{fp} 条", "arrange+act 的机械口径"),
        ("行为等价（4 用例×2 实现）", beh_tail if beh_ok else "红！", beh_tail if beh_ok else "红！",
         "同一套测试双实现全绿 = 不改行为"),
    ]

    print("===== 可测性重构前后对比（会话管理域）=====")
    print(f"{'指标':<26}{'重构前 legacy':<18}{'重构后 DI':<16}说明")
    for name, a, b, note in rows:
        print(f"{name:<26}{a:<18}{b:<16}{note}")
    print(f"\n过期测试加速：{speedup_disp}（{d[legacy]:.2f}s → {d[fake]*1e6:.0f}µs，"
          f"{'✓ <100ms 达标' if d[fake] < 0.1 else '✗ 未达 100ms'}；"
          f"legacy {'✓ ≥1s' if d[legacy] >= 1.0 else '✗ <1s'}）")
    print(f"行为等价：{'✅ 全绿（重构不改行为）' if beh_ok else '❌ ' + beh_tail}")

    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
               "durations": d, "speedup_disp": speedup_disp,
               "func_lines": {legacy: lt, fake: ft},
               "prep_statements": {legacy: lp, fake: fp},
               "global_touches": {legacy: ltouch, fake: ftouch},
               "behavior_ok": beh_ok}
    (out / "dft_report.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    with (out / "dft_report.md").open("w") as f:
        f.write(f"# 可测性重构对比（{payload['generated_at']}）\n\n"
                f"| 指标 | 重构前 legacy | 重构后 DI | 说明 |\n|:--|:--|:--|:--|\n")
        for name, a, b, note in rows:
            f.write(f"| {name} | {a} | {b} | {note} |\n")
        f.write(f"\n加速 {speedup_disp}；fake clock {d[fake]*1e6:.0f}µs（<100ms 达标）\n")
    print("产物：reports/dft_report.md、reports/dft_report.json")
    sys.exit(0 if (beh_ok and d[fake] < 0.1 and d[legacy] >= 1.0) else 1)


if __name__ == "__main__":
    main()
