"""mutator.py —— 自研 AST 变异器：把源码里「一个符号的改变会改变行为」的位置
逐一生成变异体（mutant）。

四类变异（各挑一类有业务含义的）：
  比较符翻转   < ↔ <=、> ↔ >=、== ↔ !=   （门槛/边界类缺陷）
  算术符翻转   + ↔ -                      （金额计算类缺陷）
  数值字面量   常量 +1；纯数字字符串 ±0.01（券额/门槛/精度类缺陷）
  布尔翻转     True ↔ False               （默认行为类缺陷）

实现是两遍式：第一遍按确定性遍历顺序给变异点编号（同一棵树顺序恒定），
第二遍深拷贝语法树、把第 i 个变异点替换为孪生操作符，ast.unparse 回源码。
等价变异（行为恰好不变）不在生成期剔除——它是变异测试的理论边界，留给报告。
"""
import ast
import copy
import re

FLIP_COMPARE = {ast.Lt: ast.LtE, ast.LtE: ast.Lt,
                ast.Gt: ast.GtE, ast.GtE: ast.Gt,
                ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
SWAP_RAISE = {"ValueError": "TypeError", "TypeError": "ValueError"}
FLIP_BINOP = {ast.Add: ast.Sub, ast.Sub: ast.Add}
NUMERIC_STR = re.compile(r"^-?\d+(\.\d+)?$")


def _alt_compare(op):
    return FLIP_COMPARE[type(op)]()


def _alt_binop(op):
    return FLIP_BINOP[type(op)]()


def _describe(node) -> str | None:
    """该节点是否可变异；返回人类可读的变异说明。"""
    if isinstance(node, ast.Compare) and len(node.ops) == 1 \
            and type(node.ops[0]) in FLIP_COMPARE:
        return f"比较符 {type(node.ops[0]).__name__} → {type(_alt_compare(node.ops[0])).__name__}（L{node.lineno}）"
    if isinstance(node, ast.BinOp) and type(node.op) in FLIP_BINOP:
        return f"算术符 {type(node.op).__name__} → {type(_alt_binop(node.op)).__name__}（L{node.lineno}）"
    if isinstance(node, ast.Constant):
        v = node.value
        if isinstance(v, bool):
            return f"布尔 {v} → {not v}（L{node.lineno}）"
        if isinstance(v, str) and NUMERIC_STR.match(v):
            frac = f"{v}1" if "." in v else f"{v}.1"
            return f"数值字符串 \"{v}\" → \"{frac}\"（L{node.lineno}）"
        if isinstance(v, (int, float)):
            return f"数值 {v} → {v + 1}（L{node.lineno}）"
    return None


class _Mutator(ast.NodeTransformer):
    """把第 target 号可变异节点替换为孪生形态；target=None 时只按同一遍历
    顺序记录变异点——编号与生成必须同源，错位会让报告张冠李戴。"""

    def __init__(self, target: int | None):
        self.i = -1
        self.target = target
        self.applied = None
        self.records = []

    def _maybe(self, node, make_alt, desc):
        self.i += 1
        if self.target is None:
            self.records.append({"index": self.i, "desc": desc, "lineno": node.lineno})
            return self.generic_visit(node)
        if self.i == self.target:
            alt = make_alt(node)
            alt = ast.copy_location(alt, node)
            self.applied = ast.unparse(alt)
            return self.generic_visit(alt)
        return self.generic_visit(node)

    def visit_Compare(self, node):
        if _describe(node) is not None:
            return self._maybe(node, lambda n: ast.Compare(
                left=n.left, ops=[_alt_compare(n.ops[0])], comparators=n.comparators),
                _describe(node))
        return self.generic_visit(node)

    def visit_BinOp(self, node):
        if _describe(node) is not None:
            return self._maybe(node, lambda n: ast.BinOp(
                left=n.left, op=_alt_binop(n.op), right=n.right), _describe(node))
        return self.generic_visit(node)

    def visit_Raise(self, node):
        # raise ValueError(...) 的 exc 是 Call 节点，被调名挂在 exc.func 上
        if (isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name)
                and node.exc.func.id in SWAP_RAISE):
            desc = f"异常类型 {node.exc.func.id} → {SWAP_RAISE[node.exc.func.id]}（L{node.lineno}）"
            return self._maybe(node, lambda n: ast.Raise(
                exc=ast.Call(func=ast.Name(id=SWAP_RAISE[n.exc.func.id], ctx=ast.Load()),
                             args=n.exc.args, keywords=n.exc.keywords),
                cause=n.cause), desc)
        return self.generic_visit(node)

    def visit_Constant(self, node):
        d = _describe(node)
        if d is None:
            return self.generic_visit(node)
        v = node.value
        if isinstance(v, bool):
            return self._maybe(node, lambda n: ast.Constant(value=not n.value), d)
        if isinstance(v, str):
            frac = f"{v}1" if "." in v else f"{v}.1"
            return self._maybe(node, lambda n: ast.Constant(value=frac), d)
        return self._maybe(node, lambda n: ast.Constant(value=v + 1), d)


def describe_all(src: str) -> list[dict]:
    """第一遍：与生成同一遍历顺序列出全部变异点（编号、说明、行号）。"""
    counter = _Mutator(target=None)
    counter.visit(ast.parse(src))
    return counter.records


def build_mutant(src: str, index: int) -> str:
    """第二遍：生成第 index 号变异体的源码。"""
    m = _Mutator(target=index)
    new_tree = m.visit(copy.deepcopy(ast.parse(src)))
    if m.applied is None:
        raise RuntimeError(f"变异体 {index} 未命中")
    return ast.unparse(new_tree) + "\n"
