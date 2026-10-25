"""消费方 SDK：消费方团队按「契约」写的调用代码——写它的时候 provider 还不存在。

这就是 mock-first 的开发方式：client 只认识契约定义的端点与结构，
测试先打挡板跑起来；等 provider 实现好，把 BASE_URL 一换即接真实服务。
"""
import os

import httpx

BASE = os.environ.get("MOCK_BASE_URL", "http://127.0.0.1:8934")


class ItemsClient:
    def __init__(self, base: str = BASE):
        self.base = base.rstrip("/")

    def health(self) -> httpx.Response:
        return httpx.get(f"{self.base}/api/health", timeout=10)

    def create_item(self, name: str, price: float) -> httpx.Response:
        return httpx.post(f"{self.base}/api/items",
                          json={"name": name, "price": price}, timeout=10)

    def get_item(self, item_id: int) -> httpx.Response:
        return httpx.get(f"{self.base}/api/items/{item_id}", timeout=10)

    def list_items(self) -> httpx.Response:
        return httpx.get(f"{self.base}/api/items", timeout=10)

    def delete_item(self, item_id: int) -> httpx.Response:
        return httpx.delete(f"{self.base}/api/items/{item_id}", timeout=10)
