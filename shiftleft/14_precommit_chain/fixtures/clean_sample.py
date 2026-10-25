"""干净样本：类型正确、无缺陷模式——快层与重层都应放行。"""


def price(qty: int, unit: int = 10) -> int:
    if qty <= 0:
        return 0
    return qty * unit


def banner(text: str) -> str:
    return f"== {text} =="
