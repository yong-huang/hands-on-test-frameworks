"""温度换算模块——lab 01 的被测对象（SUT）。

刻意写得"小而完整"：4 个纯函数 + 1 个带分支的类方法，
足够演示断言重写、-k 圈选、-x 早停和断言回溯输出。
"""


def celsius_to_fahrenheit(celsius: float) -> float:
    """摄氏 → 华氏：F = C × 9/5 + 32"""
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """华氏 → 摄氏：C = (F − 32) × 5/9"""
    return (fahrenheit - 32) * 5 / 9


def celsius_to_kelvin(celsius: float) -> float:
    """摄氏 → 开尔文；低于绝对零度（-273.15°C）物理上不成立"""
    if celsius < -273.15:
        raise ValueError(f"温度低于绝对零度: {celsius}°C")
    return celsius + 273.15


def kelvin_to_celsius(kelvin: float) -> float:
    """开尔文 → 摄氏；同样不允许低于绝对零度"""
    if kelvin < 0:
        raise ValueError(f"温度低于绝对零度: {kelvin}K")
    return kelvin - 273.15


class Thermostat:
    """简易恒温器：根据设定温度判断冷暖档位（含分支逻辑）"""

    def __init__(self, low: float = 18.0, high: float = 26.0) -> None:
        self.low, self.high = low, high

    def mode(self, celsius: float) -> str:
        """返回 heating / comfort / cooling 三档"""
        if celsius < self.low:
            return "heating"
        if celsius > self.high:
            return "cooling"
        return "comfort"
