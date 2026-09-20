#!/usr/bin/env python3
"""cov_gate.py — 新代码覆盖率卡点与豁免流：增量覆盖率 + CI bot 评论 + 豁免状态机。

架构师视角的一句话：**推动研发写单测，靠的是机制不是口号**——新代码覆盖率卡点
（diff coverage）就是机制：PR 新增行必须有测试覆盖，未达标 CI bot 自动拦截并给出
未覆盖行清单；例外走豁免审批（状态机留痕），既不堵死紧急通道，也不让豁免变后门。
存量问题不追（新账新办法），老代码靠按风险排序补测（项目 2 策略驱动）。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STORE = REPO / "labs/11_sut_app/app/store.py"
COV_JSON = Path(__file__).parent / "reports" / "pr_cov.json"
EXEMPTIONS = Path(__file__).parent / "reports" / "exemptions.json"
BOT_COMMENT = Path(__file__).parent / "reports" / "bot_comment.md"
THRESHOLD = 0.80


# ---------------------------------------------------------------- 数据采集
def refresh_coverage() -> None:
    """跑门禁套件产出 store 的行级覆盖 JSON（含本次 PR 新增行，若已写入工作区）。"""
    import tempfile
    tf = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    out = tf.name
    tf.close()
    subprocess.run(
        [sys.executable, "-m", "pytest", "-c", "configs/pytest.ini", "--rootdir=.", "-q",
         "-o", "addopts=", "-p", "no:cacheprovider",
         "--cov=store", f"--cov-report=json:{out}"],
        cwd=REPO / "labs/13_db_tests", check=True, capture_output=True, text=True, timeout=300)
    data = json.loads(Path(out).read_text())
    Path(out).unlink(missing_ok=True)
    COV_JSON.parent.mkdir(parents=True, exist_ok=True)
    COV_JSON.write_text(json.dumps(data, indent=1), encoding="utf-8")


def added_lines() -> list[int]:
    """git diff -U0 解析 store.py 的新增行号（新文件侧）。"""
    r = subprocess.run(["git", "diff", "-U0", "--", "labs/11_sut_app/app/store.py"],
                       cwd=REPO, capture_output=True, text=True)
    lines = []
    for m in re.finditer(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", r.stdout):
        start, count = int(m.group(1)), int(m.group(2) or 1)
        lines.extend(range(start, start + count))
    return lines


def executed_lines() -> set[int]:
    data = json.loads(COV_JSON.read_text())
    for f, info in data["files"].items():
        if f.endswith("store.py"):
            return set(info["executed_lines"])
    return set()


# ---------------------------------------------------------------- 裁决
def check() -> tuple[str, float, list[int], list[str]]:
    added = added_lines()
    if not added:
        return "NO_DIFF", 1.0, [], []
    executed = executed_lines()
    covered = [ln for ln in added if ln in executed]
    missed = [ln for ln in added if ln not in executed]
    ratio = len(covered) / len(added)
    if ratio >= THRESHOLD:
        return "PASS", ratio, missed, []
    # 豁免检查（状态机：requested/approved 才豁免）
    ex = load_exemptions()
    if any(e["status"] == "approved" and e["file"].endswith("store.py") for e in ex):
        return "PASS_EXEMPT", ratio, missed, ["存在已批准的豁免记录（见 exemptions.json）"]
    return "BLOCK", ratio, missed, []


# ---------------------------------------------------------------- 豁免状态机
def load_exemptions() -> list[dict]:
    if EXEMPTIONS.exists():
        return json.loads(EXEMPTIONS.read_text(encoding="utf-8"))
    EXEMPTIONS.parent.mkdir(parents=True, exist_ok=True)
    return []


def save_exemptions(exs: list[dict]) -> None:
    EXEMPTIONS.write_text(json.dumps(exs, ensure_ascii=False, indent=2), encoding="utf-8")


def request_exemption(reason: str) -> None:
    exs = load_exemptions()
    exs.append({"id": f"EX-{int(time.time())}", "file": "labs/11_sut_app/app/store.py",
                "reason": reason, "status": "requested",
                "requested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "audit": [f"{time.strftime('%H:%M:%S')} requested（理由：{reason}）"]})
    save_exemptions(exs)
    print(f"豁免申请已提交（状态 requested）")


def approve_exemption() -> bool:
    exs = load_exemptions()
    for e in reversed(exs):
        if e["status"] == "requested":
            e["status"] = "approved"
            e["approved_by"] = "qa-lead（审批人来自 CODEOWNERS，演示用）"
            e["audit"].append(f"{time.strftime('%H:%M:%S')} approved by qa-lead")
            save_exemptions(exs)
            print(f"豁免 {e['id']} 已批准（状态 approved）")
            return True
    print("没有待审批的豁免申请")
    return False


# ---------------------------------------------------------------- bot 评论
def bot_comment(verdict: str, ratio: float, missed: list[int], notes: list[str]) -> None:
    pct = f"{ratio:.0%}"
    if verdict == "PASS":
        body = f"## ✅ 增量覆盖率达标\n\n新增行覆盖 {pct}（阈值 {THRESHOLD:.0%}），可以合并。"
    elif verdict == "PASS_EXEMPT":
        body = (f"## ⚠️ 增量覆盖率未达标，但存在已批准豁免\n\n新增行覆盖 {pct}（阈值 {THRESHOLD:.0%}）。"
                f"\n本次放行携带豁免徽章，豁免记录永久留痕可审计。")
    else:
        lines = "\n".join(f"- 第 {ln} 行（`store.py`）" for ln in missed) or "-（无）"
        body = (f"## ❌ 增量覆盖率未达标：{pct} < {THRESHOLD:.0%}\n\n"
                f"以下新增行没有任何测试覆盖：\n{lines}\n\n"
                f"**整改建议**：为新逻辑补单元测试（mock 外部依赖，参考 labs/04 模式）；"
                f"确属紧急修复可走豁免申请（附理由与补偿计划）。")
    BOT_COMMENT.write_text(body, encoding="utf-8")
    print(body)


def main() -> int:
    ap = argparse.ArgumentParser(description="新代码覆盖率卡点")
    ap.add_argument("cmd", choices=["refresh", "check", "request", "approve"])
    ap.add_argument("--reason", default="")
    args = ap.parse_args()

    if args.cmd == "refresh":
        refresh_coverage()
        print("覆盖数据已刷新（labs/13 套件 × store）")
        return 0
    if args.cmd == "request":
        request_exemption(args.reason)
        return 0
    if args.cmd == "approve":
        return 0 if approve_exemption() else 1

    verdict, ratio, missed, notes = check()
    bot_comment(verdict, ratio, missed, notes)
    if verdict == "BLOCK":
        print(f"裁决：BLOCK（{ratio:.0%} < {THRESHOLD:.0%}），退出码 1")
        return 1
    print(f"裁决：{verdict}（{ratio:.0%} ≥ {THRESHOLD:.0%}），退出码 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

