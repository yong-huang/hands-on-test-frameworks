"""反面教材：三条用例共享一个模块级计数器。

串行按文件顺序跑恰好全绿；一旦并行（xdist 按 worker 分发），
每个 worker 的计数器独立从 0 开始——序号断言立刻现形。
这就是"用例独立性"的反面演示，修复版见 tests/test_pollution_fixed.py。
"""
_counter = {"n": 0}


def bump_and_report() -> int:
    _counter["n"] += 1
    return _counter["n"]
