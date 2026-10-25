#!/usr/bin/env python3
"""detector.py —— 测试反模式检测器：用 AST 找出「全绿但没在测」的测试。

九类规则（表驱动，全部只读分析）：
  assert_constant   空断言/恒真断言     assert True、assert 1
  tautology         永真比较           assert x == x
  tautology_math    恒真数学比较        assert len(x) >= 0
  raises_base       裸 Exception        with pytest.raises(Exception)（吞一切异常）
  bare_except       裸 except           try/except: pass 吞错不留痕
  no_assert         无断言测试          函数体内没有任何断言/raises
  sleep_in_test     测试内真实等待       time.sleep —— 把不确定性写死在测试里
  print_debug       调试残留            测试里的 print
  commented_assert  注释掉的断言         # assert ... （尸体测试）

用法：
    python detector.py --path samples/bad          # 坏样本：埋点全部检出
    python detector.py --path samples/good --gate  # 好样本：零误报（gate 退出码 0）
    python detector.py --path ../../labs           # 真实报告（只读，不改任何文件）
产出：reports/antipattern_report.md / .json（--no-save 关闭）
"""
import argparse
import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path

RULES = {
    "assert_constant": "空断言/恒真断言（assert True 这类永远绿）",
    "tautology": "永真比较（assert x == x）",
    "tautology_math": "恒真数学比较（len(x) >= 0）",
    "raises_base": "裸 Exception（pytest.raises(Exception) 吞一切异常）",
    "bare_except": "裸 except 吞错",
    "no_assert": "无断言测试（全函数没有 assert/raises）",
    "sleep_in_test": "测试内真实等待（time.sleep）",
    "print_debug": "调试 print 残留",
    "commented_assert": "注释掉的断言（尸体测试）",
}


def _is_pytest_raises(node: ast.AST) -> bool:
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "raises")


def scan_file(path: Path) -> list[dict]:
    """单文件扫描：返回 [{file, line, rule, detail}]；AST 规则 + 注释正则规则。"""
    src = path.read_text()
    findings = []
    tree = ast.parse(src)

    test_funcs = [n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name.startswith("test")]

    for fn in test_funcs:
        has_assert = False
        for node in ast.walk(fn):
            # 断言的三种形态：assert 语句、pytest.raises、playwright 的 expect
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id == "expect":
                has_assert = True
            if _is_pytest_raises(node):
                has_assert = True
                if node.args and isinstance(node.args[0], ast.Name) \
                        and node.args[0].id == "Exception":
                    findings.append({"line": node.lineno, "rule": "raises_base",
                                     "detail": "pytest.raises(Exception)"})
                continue
            if isinstance(node, ast.Assert):
                has_assert = True
                test_node = node.test
                # 空断言：assert 后面是常量（True/1/"x" 都算）
                if isinstance(test_node, ast.Constant):
                    findings.append({"line": node.lineno, "rule": "assert_constant",
                                     "detail": f"assert {ast.unparse(test_node)}"})
                # 永真比较：x == x / len(x) >= 0
                if isinstance(test_node, ast.Compare):
                    left, cmp = test_node.left, test_node.comparators[0]
                    if isinstance(test_node.ops[0], ast.Eq) \
                            and ast.unparse(left) == ast.unparse(cmp):
                        findings.append({"line": node.lineno, "rule": "tautology",
                                         "detail": f"assert {ast.unparse(test_node)}"})
                    if (isinstance(left, ast.Call) and isinstance(left.func, ast.Name)
                            and left.func.id == "len"
                            and isinstance(test_node.ops[0], (ast.GtE, ast.Gt))
                            and isinstance(cmp, ast.Constant) and cmp.value == 0):
                        findings.append({"line": node.lineno, "rule": "tautology_math",
                                         "detail": f"assert {ast.unparse(test_node)}"})
            # 裸 except：handler 无类型（吞掉一切）
            if isinstance(node, ast.Try):
                for h in node.handlers:
                    if h.type is None:
                        findings.append({"line": h.lineno, "rule": "bare_except",
                                         "detail": "except: 不留痕迹地吞掉一切"})
            # 测试内 sleep / print
            if isinstance(node, ast.Call):
                fn_node = node.func
                name = fn_node.attr if isinstance(fn_node, ast.Attribute) else (
                    fn_node.id if isinstance(fn_node, ast.Name) else "")
                if name == "sleep":
                    findings.append({"line": node.lineno, "rule": "sleep_in_test",
                                     "detail": f"sleep 真实等待（{ast.unparse(node)}）"})
                if name == "print":
                    findings.append({"line": node.lineno, "rule": "print_debug",
                                     "detail": "print 调试残留"})
        if not has_assert:
            findings.append({"line": fn.lineno, "rule": "no_assert",
                             "detail": f"{fn.name} 全函数无断言"})

    for i, line in enumerate(src.splitlines(), start=1):
        stripped = line.strip()
        if re.match(r"#\s*assert\b", stripped):
            findings.append({"line": i, "rule": "commented_assert",
                             "detail": stripped[:60]})
    return findings


def _is_third_party(p: Path) -> bool:
    """跳过虚拟环境/依赖目录——验收对象是本系列实验，不是第三方库的测试套件。"""
    return any(part in (".venv", "node_modules", "__pycache__")
               or (part.startswith(".") and part not in ("..", "."))
               for part in p.parts)


def scan_path(path: Path) -> tuple[list[dict], int]:
    files = [f for f in sorted(path.rglob("test_*.py")) if not _is_third_party(f)]
    all_findings = []
    for f in files:
        for x in scan_file(f):
            all_findings.append({"file": str(f), **x})
    return all_findings, len(files)


def main():
    ap = argparse.ArgumentParser(description="测试反模式检测器（只读）")
    ap.add_argument("--path", default="samples/bad", help="扫描目标目录")
    ap.add_argument("--gate", action="store_true", help="发现任何反模式 → 退出码 1（CI 卡点）")
    ap.add_argument("--no-save", action="store_true")
    args = ap.parse_args()

    target = Path(args.path)
    findings, n_files = scan_path(target)
    by_rule = {}
    for x in findings:
        by_rule[x["rule"]] = by_rule.get(x["rule"], 0) + 1

    print(f"扫描 {target}：{n_files} 个测试文件，{len(findings)} 个反模式点\n")
    for x in sorted(findings, key=lambda x: (x["file"], x["line"])):
        print(f"  ⛔ {x['file']}:{x['line']} [{x['rule']}] {x['detail']}")
    print("\n规则命中统计：")
    for rule, n in sorted(by_rule.items(), key=lambda kv: -kv[1]):
        print(f"  {rule:<18} {n}   # {RULES[rule]}")
    if not findings:
        print("  （零命中——要么代码干净，要么规则没埋对）")

    if not args.no_save:
        out = Path(__file__).resolve().parent / "reports"
        out.mkdir(exist_ok=True)
        tag = target.name or "scan"
        payload = {"generated_at": datetime.now().isoformat(timespec="seconds"),
                   "target": str(target), "files": n_files, "findings": len(findings),
                   "by_rule": by_rule, "detail": findings}
        (out / "antipattern_report.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2))
        (out / "antipattern_report.md").write_text(
            f"# 测试反模式报告 · {target}（{payload['generated_at']}）\n\n"
            f"{n_files} 个文件，{len(findings)} 个反模式点\n\n"
            + "\n".join(f"- `{x['file']}:{x['line']}` [{x['rule']}] {x['detail']}"
                        for x in sorted(findings, key=lambda x: (x["file"], x["line"])))
            + "\n")
        print(f"产物：reports/antipattern_report.md、reports/antipattern_report.json")

    if args.gate and findings:
        print("门禁判定：存在反模式，打回（exit 1）")
        sys.exit(1)


if __name__ == "__main__":
    main()
