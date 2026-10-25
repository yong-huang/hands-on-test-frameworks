"""干净样例：被三层流水线检查的迷你项目（类型正确、无缺陷模式）。"""


def price(qty: int, unit: int = 10) -> int:
    if qty <= 0:
        return 0
    return qty * unit
