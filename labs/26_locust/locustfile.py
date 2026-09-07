"""lab 26：Locust 压测场景——读写混合、任务权重、阶梯加压。

对 SUT API 施压：读为主（列表/详情）、写为辅（下单），权重 3:1。
被压的 SUT 由脚本起在 8926（独立空库，压完即弃）。
"""
import random
import uuid

from locust import HttpUser, between, task


class OrderUser(HttpUser):
    """一个虚拟用户：模拟"逛一逛再下单"的真实节奏"""

    wait_time = between(0.5, 1.5)
    host = "http://127.0.0.1:8926"

    def on_start(self):
        """每个虚拟用户启动时健康检查一次"""
        self.client.get("/api/health")

    @task(3)
    def browse_orders(self):
        """权重 3：浏览订单列表（分页）"""
        page = random.randint(0, 2)
        with self.client.get(f"/api/orders?limit=10&offset={page*10}",
                             name="GET /api/orders 分页", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"状态码 {resp.status_code}")

    @task(1)
    def create_order(self):
        """权重 1：下单（写操作，唯一客户名避免业务冲突）"""
        uniq = uuid.uuid4().hex[:6]
        with self.client.post("/api/orders", json={
            "customer": f"压测用户-{uniq}", "item": "压测商品", "qty": 1, "price": 9.9,
        }, name="POST /api/orders 下单", catch_response=True) as resp:
            if resp.status_code != 201:
                resp.failure(f"状态码 {resp.status_code}")

    @task(1)
    def slow_config(self):
        """权重 1：慢接口——压测下排队效应最明显的端点"""
        self.client.get("/api/slow-config", name="GET /api/slow-config 慢接口")
