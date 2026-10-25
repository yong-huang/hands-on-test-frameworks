"""缺陷实现（实验注入，勿模仿）：金额全程 float（二进制浮点）。

与 pricing_good.py 的唯一差异是数值类型——这正是本实验的命题：
一个"只是顺手用了 float"的实现决定，会把这个缺陷送到漏斗的每一层，
越靠右的关卡拦下它，排查代价越大（见 configs/costs.yaml 的成本模型）。

float 是 IEEE-754 二进制浮点：19.99 和 80.10 都无法精确表示，
累加后 19.99 + 80.10 == 100.08999999999999，减券后 80.08999999999999。
"""

COUPON_VALUE = 20.00
THRESHOLD = 100.00


def cart_total(prices):
    """小计：缺陷点 1 —— float 累加商品价，误差从这里开始累积。"""
    total = 0.0
    for p in prices:
        total += float(p)
    return total


def payable(subtotal, use_coupon):
    """应付金额：缺陷点 2 —— float 减法不做精度收口，直接返回脏值。

    门槛判断本身写对了——本实验的缺陷不在业务逻辑，而在数值类型，
    这是"代码逻辑全对、账还是错的"的典型样本。
    """
    if use_coupon:
        if subtotal < THRESHOLD:
            raise ValueError("未满 ¥100，不可用新人立减券")
        return subtotal - COUPON_VALUE
    return subtotal
