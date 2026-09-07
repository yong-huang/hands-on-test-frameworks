"""lab 05 被测对象：折扣引擎（分支密集，专门用来玩覆盖率）。"""

SHIPPING_FEE = 15.0
FREE_SHIPPING_THRESHOLD = 200.0
BULK_DISCOUNT_THRESHOLD = 100.0
BULK_DISCOUNT_AMOUNT = 20.0


def item_price(item: dict, *, weekend: bool = False) -> float:
    """单品价格：周末全品加价 5%（分支：weekend / VIP 豁免）"""
    price = item["price"]
    if weekend and not item.get("vip_exempt"):
        price *= 1.05
    return round(price, 2)


def cart_subtotal(items: list[dict], *, weekend: bool = False) -> float:
    """小计：逐件计价求和"""
    return round(sum(item_price(i, weekend=weekend) for i in items), 2)


def apply_discount(subtotal: float, *, tier: str | None = None, coupon: str | None = None) -> float:
    """折扣叠加：满减 → 会员折扣 → 优惠券，顺序不可换（业务规则）"""
    total = subtotal
    if total >= BULK_DISCOUNT_THRESHOLD:            # 满 100 减 20
        total -= BULK_DISCOUNT_AMOUNT
    if tier == "vip":                               # VIP 再打 9 折
        total *= 0.9
    if coupon == "SAVE10" and total > 0:            # 券：再减 10%
        total *= 0.9
    elif coupon not in (None, "SAVE10"):            # 未知券码：报错而不是静默忽略
        raise ValueError(f"未知优惠券: {coupon}")
    return round(total, 2)


def checkout(items: list[dict], *, tier: str | None = None, coupon: str | None = None,
             weekend: bool = False, international: bool = False) -> dict:
    """结账：小计 → 折扣 → 运费（满 200 免运费；国际件不免）"""
    subtotal = cart_subtotal(items, weekend=weekend)
    total = apply_discount(subtotal, tier=tier, coupon=coupon)

    if international:
        shipping = SHIPPING_FEE * 3                 # 国际件一律收三倍运费
    elif total >= FREE_SHIPPING_THRESHOLD:          # 国内满额免运费
        shipping = 0.0
    else:
        shipping = SHIPPING_FEE

    return {"subtotal": subtotal, "total": total, "shipping": shipping,
            "grand": round(total + shipping, 2)}
