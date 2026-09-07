"""消费者驱动的契约测试（pact-python FFI 版，无 JVM/Ruby 依赖）。

前端(consumer)定义对 API(provider)的期望 → mock server 上验证交互 → 写出 pact 文件。
PACT_BREAK=1 时故意期望错误字段名（customerName）——演示 provider verify 变红的另一半。
"""
import os
from pathlib import Path

import pytest
from pact import Pact
from pact.match import decimal, each_like, integer, like

from frontend_client import create_order, get_orders

BREAK = os.environ.get("PACT_BREAK") == "1"

PACT_DIR = Path(__file__).resolve().parents[1] / "pacts"


@pytest.fixture()
def pact():
    """每条用例独立的 Pact；write_file 默认 overwrite=False=向已有契约**合并**交互"""
    p = Pact("ministore-frontend", "ministore-api")  # consumer / provider
    yield p
    p.write_file(PACT_DIR)                           # 本地文件交换，代替付费 Broker


def test_get_orders_contract(pact):
    """查询订单：期望 200 + 结构化订单数组（like 只锁类型不锁具体值）"""
    customer_field = "customerName" if BREAK else "customer"
    (
        pact
        .upon_receiving("a request for orders")
        .with_request("GET", "/api/orders")
        .with_query_parameters({"limit": like("10")})
        .will_respond_with(200)
        .with_headers({"Content-Type": "application/json"}, part="Response")
        .with_body(
            {
                "items": each_like(
                    {
                        "id": integer(),
                        customer_field: like("某人"),  # 写错字段 → provider 端 verify 必红
                        "qty": integer(),
                        "price": decimal(),
                        "status": like("created"),
                    },
                    min=1,
                ),
                "total": integer(),
            },
            part="Response",
        )
    )
    with pact.serve() as srv:
        result = get_orders(srv.url)
        assert isinstance(result["total"], int)


def test_create_order_contract(pact):
    """下单：期望 201 + 带回完整订单对象"""
    (
        pact
        .upon_receiving("a request to create an order")
        .with_request("POST", "/api/orders")
        .with_headers({"Content-Type": "application/json"})
        .with_body({"customer": "契约员", "item": "测试商品", "qty": 1, "price": 9.9})
        .will_respond_with(201)
        .with_body(
            {
                "id": integer(),
                "customer": like("契约员"),
                "status": like("created"),
            },
            part="Response",
        )
    )
    with pact.serve() as srv:
        order = create_order(srv.url, "契约员", "测试商品", 1, 9.9)
        assert order["id"] > 0
