"""样例的单测：快层 pytest 的口粮。"""
from app import price


def test_price():
    assert price(3) == 30
    assert price(-1) == 0
