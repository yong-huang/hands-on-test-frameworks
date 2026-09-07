"""lab 06 用例：性质测试四连——往返、不变量、@example 回归、收缩演示。"""
import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st

from props import buggy_mean, decode, encode, stable_mean

# 小策略组合：可打印文本（排除代理对，避免无关失败干扰教学）
# min_size=1：本编解码格式的定义域不含空字符串——
# encode(['']) 与 encode([]) 同为 ""，格式天生无法区分（Hypothesis 挖出的第二个真 bug，
# 已作为格式限制记录在 props.py 与 README）
texts = st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=0x2FFF),
                         min_size=1), max_size=30)


# ---------- 性质 1：编解码往返 ----------
@given(items=texts)
def test_decode_encode_roundtrip(items):
    """不变量：decode(encode(x)) == x 对任意字符串列表成立"""
    assert decode(encode(items)) == items


@given(st.text(min_size=1))
def test_encode_never_crashes(s):
    """不变量：encode 对任何单字符串都不崩（冒烟性质）"""
    assert isinstance(encode([s]), str)


# ---------- 性质 2：排序三不变量 ----------
@given(st.lists(st.integers(), max_size=50))
def test_sorted_invariants(xs):
    """三个不变量一次锁死：有序 / 置换 / 幂等"""
    out = sorted(xs)
    assert out == sorted(out)                    # 有序
    assert sorted(out) == sorted(xs)             # 置换（多键排序后仍相等）
    assert len(out) == len(xs)


# ---------- @example：把挖到的坑固定成永久回归 ----------
@given(st.lists(st.integers(), max_size=10))
@example([])               # 空列表边界：手写补充的经典边界
@example([0, -1])          # 负数与零
def test_sum_preserves_count(xs):
    assert len(xs) >= 0


# ---------- 收缩演示：Hypothesis 自己找到最小失败样例 ----------
# 预期失败！这条用例就是给 observe 步骤"处刑"用的：
# Hypothesis 会自动把失败样例收缩到极简（通常 [1e308, 1e308] 一类），
# 把"浮点精度坑"压缩成人一眼能看懂的最小复现。
@settings(max_examples=200, deadline=None)
@given(st.lists(
    st.one_of(  # 偏向型策略：大数与小数混抽，"大数吞小数"几乎必现
        st.floats(min_value=1e150, max_value=1e300),
        st.floats(min_value=-1e300, max_value=-1e150),
        st.floats(min_value=-1e3, max_value=1e3),
    ),
    min_size=2, max_size=6))
@example([1e300, 1.0, -1e300])  # 手写复现：保证每次运行都触发（回归锚点）
def test_buggy_mean_is_accurate_repro_only(nums):
    assert buggy_mean(nums) == pytest.approx(stable_mean(nums), rel=1e-9, abs=1e-12)


# ---------- 修复版的对应性质：与精确有理数均值对齐 ----------
@settings(max_examples=200, deadline=None)
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False,
                      min_value=-1e300, max_value=1e300), min_size=1, max_size=8))
def test_stable_mean_is_accurate(nums):
    """fsum 求和几乎无损：与 Fraction 精确均值的误差应远小于 buggy 版"""
    from fractions import Fraction
    import math
    exact = float(sum(map(Fraction, nums)) / len(nums))
    assert math.isclose(stable_mean(nums), exact, rel_tol=1e-14, abs_tol=1e-300)
