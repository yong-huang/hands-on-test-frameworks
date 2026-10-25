"""拦截目标：写法全新的同类缺陷——金额照旧用 float 承接（bug01 再世）。"""


def cart_payable(items, coupon) -> float:
    subtotal = 0.0
    for raw in items:
        subtotal = subtotal + float(raw)  # 同类缺陷：金额走 float
    return subtotal - float(coupon)
