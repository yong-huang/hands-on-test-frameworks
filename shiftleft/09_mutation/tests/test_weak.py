"""第一轮被测套件：覆盖率好看的「假测试」——五个测试全绿、四条分支都踩到，
但断言稀薄（is not None / 只查有异常不查类型）。它们能给变异测试送出多少分？"""
import pytest

from pricing import payable


def test_discount_returns_something():
    assert payable(150.0, use_coupon=True) is not None


def test_threshold_raises():
    with pytest.raises(Exception):  # 只查「抛了」，不查类型与信息
        payable(50.0, use_coupon=True)


def test_no_coupon_returns_something():
    assert payable(80.0, use_coupon=False) is not None


def test_boundary_no_crash():
    assert payable(100.0, use_coupon=True) is not None


def test_default_runs():
    assert payable(150.0) is not None
