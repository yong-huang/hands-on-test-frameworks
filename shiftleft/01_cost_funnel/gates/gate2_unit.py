#!/usr/bin/env python3
"""关卡 2 · 单元测试 —— pytest 精确到分断言，失败栈直接指向 pricing 函数。

本关跑 defect/test_pricing.py：断言用字符串精确比对（"80.09"），
把「精确到分」这条验收条件直译成断言。被测实现由 PRICING_IMPL 决定：
pytest 红 = 缺陷被单测拦下；pytest 绿 = 无缺陷可拦。

复现：python gates/gate2_unit.py            # 对缺陷实现
      PRICING_IMPL=good python gates/gate2_unit.py  # 对照
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFECT = ROOT / "defect"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=["good", "bad"], default="bad")
    args = ap.parse_args()

    print(f"[关卡2 · 单元测试] pytest test_pricing.py（被测实现 = pricing_{args.impl}）")
    env = dict(os.environ, PRICING_IMPL=args.impl)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "test_pricing.py", "-q", "--tb=line"],
        cwd=DEFECT, env=env, capture_output=True, text=True)
    for line in proc.stdout.strip().splitlines()[-5:]:
        print("  " + line)

    if proc.returncode != 0:
        print("  → 用例红：金额断言失败，缺陷在编码阶段被单测拦下")
        print("RESULT: INTERCEPTED")
    else:
        print("  → 用例全绿：无缺陷可拦")
        print("RESULT: CLEAN_PASS")


if __name__ == "__main__":
    main()
