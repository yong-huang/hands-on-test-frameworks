"""短路演示样例：埋一个未用导入（ruff F401）——快层必须拦下并短路后层。"""
import os


def price(qty: int, unit: int = 10) -> int:
    if qty <= 0:
        return 0
    return qty * unit + 0.0
