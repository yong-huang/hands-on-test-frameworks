"""坏 fixture · 缺陷层：ruff 的 error 级规则（B006 可变默认值 / F821 未定义名字）。"""


def add_item(x: int, items: list = []) -> list:  # B006：可变对象做默认值（跨调用共享）
    if x == None:  # E711：与 None 比较应用 is（warning 级）
        return items
    items.append(x)
    return items


def total(cart) -> int:
    return sum(i["price"] for i in cart) + undefined_discount  # F821：名字未定义
