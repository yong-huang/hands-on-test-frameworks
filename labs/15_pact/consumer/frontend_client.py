"""消费者侧的"前端客户端"——模拟 JS 前端调用订单 API 的两个方法。

契约测试只测这两个方法的"交互形状"：路径、参数、响应结构。
"""
import httpx


def get_orders(base_url: str) -> dict:
    r = httpx.get(f"{base_url}/api/orders", params={"limit": 10}, timeout=10, trust_env=False)  # trust_env=False：绕过系统代理，直连 mock server
    r.raise_for_status()
    return r.json()


def create_order(base_url: str, customer: str, item: str, qty: int, price: float) -> dict:
    r = httpx.post(f"{base_url}/api/orders", timeout=10, trust_env=False, json={
        "customer": customer, "item": item, "qty": qty, "price": price,
    })
    r.raise_for_status()
    return r.json()
