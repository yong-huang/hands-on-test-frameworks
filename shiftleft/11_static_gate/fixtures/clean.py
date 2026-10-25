"""干净 fixture：类型正确、无缺陷模式、风格达标——gate 应当全绿放行。"""


def price(qty: int, unit: int = 10) -> int:
    """简单定价：数量 × 单价，qty 非正时返回 0。"""
    if qty <= 0:
        return 0
    return qty * unit


def banner(text: str) -> str:
    return f"== {text} =="
