#!/usr/bin/env python3
"""关卡 1 · 需求评审 —— 验收条件 ↔ 测试用例 映射检查（预防层：缺陷还没进代码）。

输入：configs/requirements.yaml（AC = Acceptance Criteria，验收条件清单）
      configs/test_plan.yaml（编码前评审会要过目的用例计划）
检查：每条 AC 至少被一条用例的 covers 字段引用。
判定：存在缺口 → RESULT: INTERCEPTED（评审会要求先补用例，缺陷进不了编码）
      全部覆盖 → RESULT: CLEAN_PASS

复现：python gates/gate1_requirements.py
"""
import argparse
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=["good", "bad"], default="bad")
    args = ap.parse_args()  # 本关检查的是测试计划完整性，与实现无关

    reqs = yaml.safe_load((ROOT / "configs/requirements.yaml").read_text())
    plan = yaml.safe_load((ROOT / "configs/test_plan.yaml").read_text())
    acs = {ac["id"]: " ".join(ac["text"].split()) for ac in reqs["acceptance_criteria"]}
    covered = {ac for case in plan["cases"] for ac in case["covers"]}
    missing = [aid for aid in acs if aid not in covered]

    print(f"[关卡1 · 需求评审] AC 共 {len(acs)} 条，用例计划覆盖 {len(covered)} 条")
    for aid in missing:
        print(f"  ⛔ {aid} 无任何用例覆盖：{acs[aid]}")
    if missing:
        print("  → 评审结论：先补齐用例再开发（float 金额这类缺陷被堵在编码之前）")
        print("RESULT: INTERCEPTED")
    else:
        print("  → AC 全部有用例，放行进入编码")
        print("RESULT: CLEAN_PASS")


if __name__ == "__main__":
    main()
