"""ShopLibrary — 项目 11 的自定义关键字库（PythonLibCore 惯用法）。

关键字 = public 方法；docstring = Robot 文档；断言失败抛 AssertionError 即用例红。
"""
import hashlib
import json
import time
import uuid

from robot.api import logger
from robot.api.deco import keyword, library


@library(scope="GLOBAL", version="1.0.0")
class ShopLibrary:

    @keyword("生成订单号前缀")
    def make_order_prefix(self, env: str = "test") -> str:
        """生成唯一订单号前缀（环境前缀-SHORTUUID）。

        示例：`${prefix}=    生成订单号前缀    test`
        """
        return f"{env}-{uuid.uuid4().hex[:8]}"

    @keyword("校验金额")
    def validate_amount(self, amount_str: str) -> float:
        """校验金额字符串必须为两位小数的正数，返回 float；非法直接抛 AssertionError。"""
        try:
            value = float(amount_str)
        except (TypeError, ValueError):
            raise AssertionError(f"金额不是数字：{amount_str!r}")
        if value <= 0:
            raise AssertionError(f"金额必须为正数：{value}")
        rounded = round(value, 2)
        if abs(rounded - value) > 1e-9:
            raise AssertionError(f"金额超过两位小数：{amount_str!r}")
        return rounded

    @keyword("生成测试数据")
    def make_test_data(self, name: str, address: str) -> dict:
        """生成带唯一毫秒后缀的下单测试数据（防止多轮数据串味）。

        同毫秒连调时由进程内计数器递增保证唯一（机器太快实测会撞毫秒）。
        """
        suffix = int(time.time() * 1000)
        self._seq = getattr(self, "_seq", 0) + 1
        if getattr(self, "_last_ms", None) == suffix:
            suffix = suffix * 1000 + self._seq
        self._last_ms = suffix
        return {"customer": f"{name}-{suffix}", "address": address, "created_ms": suffix}

    @keyword("计算签名")
    def sign_payload(self, payload: dict, secret: str) -> str:
        """对 payload 做 sha256 签名（排序后 JSON 序列化 + secret 盐）。"""
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256((canonical + secret).encode()).hexdigest()

    @keyword("断言签名一致")
    def assert_signature(self, payload: dict, secret: str, expected: str) -> None:
        actual = self.sign_payload(payload, secret)
        if actual != expected:
            raise AssertionError(f"签名不一致：期望 {expected}，实际 {actual}")
        logger.info("签名校验通过")
