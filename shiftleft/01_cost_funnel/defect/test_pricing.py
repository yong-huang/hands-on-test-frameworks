"""关卡 2（单元测试）的用例文件：按 PRICING_IMPL 环境变量加载被测实现。

断言方式用 str(result) 对期望字符串精确比对，而不是 == 数值比较——
float 版的 80.08999999999999 和 Decimal 版的 80.09 直接 == 会得到 False，
但写 assert total == 80.09 这种用例本身就可能被 float 的"看起来对"骗过；
字符串比对把"精确到分"这个需求直译成了断言。
"""
import importlib
import os

import pytest

_IMPL = os.environ.get("PRICING_IMPL", "bad")  # 默认对准缺陷实现
pricing = importlib.import_module(f"pricing_{_IMPL}")

ITEMS = ["19.99", "80.10"]  # 两件商品：¥19.99 + ¥80.10


def test_subtotal_exact_cents():
    """AC-2 精确到分：小计必须是 100.09，不能是 100.08999999999999。"""
    assert str(pricing.cart_total(ITEMS)) == "100.09"


def test_payable_with_coupon_exact_cents():
    """AC-2 精确到分：满 100 用券后应付 80.09。"""
    subtotal = pricing.cart_total(ITEMS)
    assert str(pricing.payable(subtotal, use_coupon=True)) == "80.09"


def test_below_threshold_rejected():
    """AC-1 门槛：未满 100 用券必须被拒绝，而不是照常减钱。"""
    subtotal = pricing.cart_total(["19.99"])
    with pytest.raises(ValueError):
        pricing.payable(subtotal, use_coupon=True)
