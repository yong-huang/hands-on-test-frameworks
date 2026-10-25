"""正确实现：金额全程 Decimal（十进制浮点），精确到分。

需求背景（configs/requirements.yaml）：新人立减券 ¥20，满 ¥100 可用，每单限一张。
验收条件 AC-2 要求「金额精确到分，禁止二进制浮点」——
Decimal("19.99") + Decimal("80.10") 永远精确等于 100.09；
同款算式换成 float 是 100.08999999999999（defect/pricing_bad.py 的缺陷根源）。
"""
from decimal import Decimal, ROUND_HALF_UP

# 金额常量一律用字符串构造 Decimal，避免"先 float 后 Decimal"把误差带进来
COUPON_VALUE = Decimal("20.00")   # 券面额
THRESHOLD = Decimal("100.00")     # 用券门槛
_CENT = Decimal("0.01")


def cart_total(prices):
    """小计：商品价逐项累加。Decimal 十进制加法无累积误差。"""
    total = Decimal("0")
    for p in prices:
        total += Decimal(str(p))
    return total


def payable(subtotal, use_coupon):
    """应付金额：用券则减券面额，未满门槛拒绝用券（AC-1）。

    quantize(…, ROUND_HALF_UP) 即"四舍五入到分"，最后一步统一收口。
    """
    if use_coupon:
        if subtotal < THRESHOLD:
            raise ValueError("未满 ¥100，不可用新人立减券")
        return (subtotal - COUPON_VALUE).quantize(_CENT, ROUND_HALF_UP)
    return subtotal.quantize(_CENT, ROUND_HALF_UP)
