"""坏 fixture · 类型层：注解与实际返回不符——mypy 的 error 级 [return-value]。"""


def price(qty: int) -> int:
    if qty <= 0:
        return "many"  # 类型错误：声明返回 int，实际返回 str
    return qty * 10
