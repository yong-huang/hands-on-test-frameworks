"""bug01 · 金额精度（修复版）：金额一律 Decimal，精确到分。"""
from decimal import Decimal, ROUND_HALF_UP


def total(price_a, price_b, discount) -> Decimal:
    cents = Decimal("0.01")
    return (Decimal(str(price_a)) + Decimal(str(price_b))
            - Decimal(str(discount))).quantize(cents, ROUND_HALF_UP)
