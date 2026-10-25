#!/usr/bin/env python3
"""关卡 3 · 静态分析 —— AST 规则 MONEY-FLOAT：金额代码里不许出现 float。

规则（教学版）：解析目标文件的 AST，凡 float 字面量常量或 float() 调用
逐行列出。教学版不做金额上下文收窄——本实验两个 pricing 文件里所有
float 都与金额有关；真实项目应按变量命名/类型注解收窄以控误报。

对照：pricing_bad.py 命中 4 处（20.00 / 100.00 / 0.0 / float(p)）；
      pricing_good.py 命中 0 处（金额全是字符串构造的 Decimal）——零误报。

复现：python gates/gate3_static.py            # 扫缺陷实现
      python gates/gate3_static.py --file pricing_good.py  # 零误报对照
"""
import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFECT = ROOT / "defect"


def scan(path: Path):
    """返回 [(行号, 违规说明)]：float 字面量与 float() 调用都算命中。"""
    tree = ast.parse(path.read_text())
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            hits.append((node.lineno, f"float 字面量 {node.value!r}"))
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == "float"):
            hits.append((node.lineno, "float() 转换调用"))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=["good", "bad"], default="bad")
    ap.add_argument("--file", default=None, help="显式指定被扫文件名")
    args = ap.parse_args()

    target = DEFECT / (args.file or f"pricing_{args.impl}.py")
    hits = scan(target)
    print(f"[关卡3 · 静态分析] 规则 MONEY-FLOAT 扫描 {target.name}")
    for lineno, why in hits:
        src = target.read_text().splitlines()[lineno - 1].strip()
        print(f"  ⛔ L{lineno} {why}：{src}")
    if hits:
        print("  → 建议改用 Decimal（字符串构造），违规在编码提交前即被标出")
        print("RESULT: INTERCEPTED")
    else:
        print("  → 未命中 float 金额：零误报，放行")
        print("RESULT: CLEAN_PASS")


if __name__ == "__main__":
    main()
