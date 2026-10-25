"""温度换算的 15 条用例——最后 1 条是**故意写错**的，用于演示断言回溯输出。

运行方式（在 lab 目录下）：
    pytest -c configs/pytest.ini -v              # 全量：14 过 1 挂（预期）
    pytest -c configs/pytest.ini -k "not regression_demo" -v   # 圈掉故意失败：全绿
"""
import pytest

from temperature import (
    Thermostat,
    celsius_to_fahrenheit,
    celsius_to_kelvin,
    fahrenheit_to_celsius,
    kelvin_to_celsius,
)


# ---------- celsius_to_fahrenheit：4 条 ----------
def test_c2f_freezing_point():
    """冰点 0°C → 32°F"""
    assert celsius_to_fahrenheit(0) == 32


def test_c2f_boiling_point():
    """沸点 100°C → 212°F"""
    assert celsius_to_fahrenheit(100) == 212


def test_c2f_body_temperature():
    """体温 37°C → 98.6°F（浮点就近比较）"""
    assert celsius_to_fahrenheit(37) == pytest.approx(98.6)


def test_c2f_negative():
    """-40°C → -40°F：两个温标唯一交点"""
    assert celsius_to_fahrenheit(-40) == -40


# ---------- fahrenheit_to_celsius：3 条 ----------
def test_f2c_round_trip():
    """往返转换应还原：C → F → C"""
    assert fahrenheit_to_celsius(celsius_to_fahrenheit(23.5)) == pytest.approx(23.5)


def test_f2c_zero():
    assert fahrenheit_to_celsius(32) == 0


def test_f2c_below_zero():
    assert fahrenheit_to_celsius(-4) == pytest.approx(-20)


# ---------- 开尔文：正常 3 条 + 异常 2 条 ----------
def test_c2k_absolute_zero():
    assert celsius_to_kelvin(-273.15) == pytest.approx(0)


def test_c2k_room():
    assert celsius_to_kelvin(25) == pytest.approx(298.15)


def test_k2c_room():
    assert kelvin_to_celsius(300) == pytest.approx(26.85)


def test_c2k_rejects_below_absolute_zero():
    """低于绝对零度应抛 ValueError，且消息里带数值——pytest.raises 的标准姿势"""
    with pytest.raises(ValueError, match="绝对零度"):
        celsius_to_kelvin(-300)


def test_k2c_rejects_negative():
    with pytest.raises(ValueError):
        kelvin_to_celsius(-1)


# ---------- Thermostat 分支：3 条 ----------
@pytest.mark.parametrize("temp,expected", [(10, "heating"), (22, "comfort"), (30, "cooling")])
def test_thermostat_modes(temp, expected):
    mode = Thermostat().mode(temp)
    # 这行 print 是 observe ④ 的教具：默认被 pytest 捕获（看不到），-s 时直达终端
    print(f"\n  thermostat: {temp}°C -> {mode}（期望 {expected}）")
    assert mode == expected


def test_thermostat_custom_thresholds():
    """阈值可配置：低温阈值提到 25°C 后，22°C 也算 heating"""
    assert Thermostat(low=25).mode(22) == "heating"


# ---------- 故意失败：教学演示 ----------
def test_regression_demo_deliberately_wrong():
    """【故意失败】需求说冰点是 32°F，写错成 0——看断言重写如何展开中间值。

    这是全实验唯一预期失败的用例：pytest 会把 `==` 两侧算出来，
    在报告里显示 `assert 32.0 == 0`，比 unittest 的 AssertionError 直观得多。
    """
    assert celsius_to_fahrenheit(0) == 0, "冰点应该是 0（故意写错，演示失败输出）"
