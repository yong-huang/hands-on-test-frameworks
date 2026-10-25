"""满减优惠券定价——本实验的「被变异目标」。

与项目 8 重构终版同语义：满 100 减 20（券额可配置）、未满门槛拒绝、
金额精确到分。它行覆盖很容易好看，但「测试写得好不好」要交给变异测试审判。
"""
from decimal import Decimal, ROUND_HALF_UP

COUPON_DEFAULT = Decimal("20.00")
THRESHOLD = Decimal("100.00")
_CENT = Decimal("0.01")


def _ensure_threshold(subtotal: Decimal) -> None:
    if subtotal < THRESHOLD:
        raise ValueError(f"未满 {THRESHOLD}，不可用券")


def _to_cents(value) -> Decimal:
    return Decimal(str(value)).quantize(_CENT, ROUND_HALF_UP)


def payable(subtotal, use_coupon=True, coupon_value=COUPON_DEFAULT):
    subtotal = Decimal(str(subtotal))
    if use_coupon:
        _ensure_threshold(subtotal)
        return _to_cents(subtotal - Decimal(str(coupon_value)))
    return _to_cents(subtotal)
