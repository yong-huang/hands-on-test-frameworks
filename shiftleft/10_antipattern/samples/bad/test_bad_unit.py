"""坏样本 1：5 个反模式点，故意写成一团——检测器的靶场。"""
import pytest


def test_empty_assert():
    assert True  # 埋点：空断言（assert_constant）


def test_tautology():
    name = "订单"
    assert name == name  # 埋点：永真比较（tautology）


def test_swallows_everything():
    with pytest.raises(Exception):  # 埋点：裸 Exception（raises_base）
        raise RuntimeError("任何异常都会被放过")


def test_bare_except():
    try:
        assert 1 + 1 == 2
    except:  # 埋点：裸 except 吞错（bare_except）
        pass


def test_no_assertions():
    # 埋点：无断言测试（no_assert）——跑了等于没跑
    total = 1 + 1
    result = total * 2
