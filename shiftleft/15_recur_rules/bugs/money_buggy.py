"""bug01 · 金额精度（缺陷版）：float 做金额运算——项目 1 漏斗里那个缺陷的域复刻。"""


def total(price_a, price_b, discount) -> float:
    return (float(price_a) + float(price_b)) - float(discount)
