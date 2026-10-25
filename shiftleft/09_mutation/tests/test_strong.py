"""第二轮被测套件：针对性补断言后的「强测试」——每个变异点都有精确断言盯着。"""
import pytest

from pricing import payable


def test_discount_exact():
    assert str(payable(150.0, use_coupon=True)) == "130.00"


def test_threshold_boundary_inclusive():
    assert str(payable(100.0, use_coupon=True)) == "80.00"


def test_below_raises_with_threshold_in_message():
    with pytest.raises(ValueError, match="100"):
        payable(50.0, use_coupon=True)


def test_no_coupon_exact():
    assert str(payable(80.0, use_coupon=False)) == "80.00"


def test_custom_coupon_value():
    assert str(payable(150.0, use_coupon=True, coupon_value=50.0)) == "100.00"


def test_exact_cents_float_inputs():
    assert str(payable(19.99 + 80.10, use_coupon=True)) == "80.09"


def test_default_applies_coupon():
    assert str(payable(150.0)) == "130.00"
