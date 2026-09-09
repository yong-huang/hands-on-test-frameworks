"""perf-shop：本性能系列的被测系统之一（FastAPI）。

所有端点都是同步函数——FastAPI 会把它们丢进线程池跑，这是后续
剖析与调参实验的基线形态。代码里埋了 3 处刻意性能缺陷，
答案在 ../SECRET_DEFS.md（做完对应实验前不要看）。
"""
import hashlib
import os
import time
from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "host=postgres port=5432 dbname=shop user=shop password=shop",
)

# 连接池参数是项目 6/8 的调参对象：先给一个"看起来合理"的默认
pool = ConnectionPool(
    DATABASE_URL, min_size=2, max_size=10, open=True, name="shop-pool"
)

app = FastAPI(title="perf-shop")
Instrumentator().instrument(app).expose(app)  # GET /metrics


@contextmanager
def get_conn():
    with pool.connection() as conn:
        yield conn


@app.get("/health")
def health():
    with get_conn() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.get("/api/products")
def list_products(limit: int = 50, offset: int = 0):
    """商品分页列表。附带每行库存数。"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, price FROM products ORDER BY id LIMIT %s OFFSET %s",
            (min(limit, 200), offset),
        ).fetchall()
        # 【缺陷位之一】下面这行循环是刻意为之的，先别优化它
        items = []
        for pid, name, price in rows:
            qty = conn.execute(
                "SELECT qty FROM stock WHERE product_id = %s", (pid,)
            ).fetchone()
            items.append(
                {"id": pid, "name": name, "price": price, "stock": qty[0] if qty else 0}
            )
    return {"items": items, "total": len(items)}


@app.get("/api/products/{pid}")
def product_detail(pid: int):
    """商品详情 + "推荐打分"。打分逻辑是刻意的，先别动它。"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, name, price FROM products WHERE id = %s", (pid,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="product not found")
    score = recommend_score(pid)
    return {
        "id": row[0],
        "name": row[1],
        "price": row[2],
        "recommend_score": score,
    }


def recommend_score(pid: int) -> int:
    # 【缺陷位之一】"推荐打分"：纯 CPU 计算，剖析实验里它会自己站出来
    score = 0
    for i in range(20000):
        digest = hashlib.md5(f"{pid}:{i}".encode()).hexdigest()
        score ^= int(digest[:8], 16)
    return score


class OrderIn(BaseModel):
    user_id: int
    product_id: int
    qty: int = 1


@app.post("/api/orders", status_code=201)
def create_order(order: OrderIn):
    """下单：扣库存 + 落订单，中间串了一次"风控调用"。"""
    # 【缺陷位之一】同步阻塞模拟串行调用下游风控，先别异步化它
    time.sleep(0.12)
    with get_conn() as conn:
        row = conn.execute(
            "UPDATE stock SET qty = qty - %s WHERE product_id = %s AND qty >= %s RETURNING qty",
            (order.qty, order.product_id, order.qty),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=409, detail="insufficient stock")
        order_id = conn.execute(
            "INSERT INTO orders (user_id, product_id, qty) VALUES (%s, %s, %s) RETURNING id",
            (order.user_id, order.product_id, order.qty),
        ).fetchone()
    return {"order_id": order_id[0]}
