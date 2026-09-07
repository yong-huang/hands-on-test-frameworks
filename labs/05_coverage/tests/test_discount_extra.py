"""补漏用例——把分支覆盖率从 ~70% 提到 ≥90%。

每条用例对应 .coveragerc 报告里的一条"未覆盖分支"，注释写明补的是哪个分支。
"""
import pytest

from discount import apply_discount, checkout, item_price


def test_item_price_weekend_surcharge():
    """补：item_price 的 weekend=True 且非豁免分支"""
    assert item_price({"price": 100.0}, weekend=True) == 105.0


def test_item_price_weekend_vip_exempt():
    """补：weekend=True 但 vip_exempt 不加价"""
    assert item_price({"price": 100.0, "vip_exempt": True}, weekend=True) == 100.0


def test_discount_bulk_threshold():
    """补：满 100 减 20 分支"""
    assert apply_discount(150.0) == 130.0


def test_discount_vip():
    """补：VIP 九折分支"""
    assert apply_discount(50.0, tier="vip") == 45.0


def test_discount_coupon_stacks():
    """补：优惠券分支（叠加在满减与 VIP 之后）"""
    assert apply_discount(150.0, tier="vip", coupon="SAVE10") == round((150 - 20) * 0.9 * 0.9, 2)


def test_discount_unknown_coupon_raises():
    """补：未知券码的 ValueError 分支"""
    with pytest.raises(ValueError, match="未知优惠券"):
        apply_discount(50.0, coupon="FAKE")


def test_checkout_international_no_free_shipping():
    """补：国际件运费分支（即使满额也不免）"""
    r = checkout([{"price": 300.0}], international=True)
    assert r["shipping"] == 45.0


def test_checkout_weekend_pipeline():
    """补：weekend 贯穿小计→折扣→运费的整条管线"""
    r = checkout([{"price": 100.0}], weekend=True)
    assert r["subtotal"] == 105.0
