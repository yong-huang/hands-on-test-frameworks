"""Locust 等效封闭场景：与 k6 closed.js 同一套动作（浏览+详情+半概率下单），
用于交叉验证封闭模型的读数，并对比两个工具的统计口径。
运行：locust -f locustfile.py --headless -u 50 -r 25 -t 40s --host ... --csv reports/locust
"""
import random

from locust import HttpUser, between, task


class ShopUser(HttpUser):
    wait_time = between(0.05, 0.15)  # 与 k6 sleep(0.1) 同量级的思考时间

    @task(2)
    def browse(self):
        self.client.get("/api/products?limit=50")

    @task(2)
    def detail(self):
        pid = random.randint(1, 200)
        self.client.get(f"/api/products/{pid}")

    @task(1)
    def order(self):
        pid = random.randint(1, 200)
        self.client.post(
            "/api/orders",
            json={"user_id": id(self) % 1000, "product_id": pid, "qty": 1},
        )
