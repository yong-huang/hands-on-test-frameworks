"""订单 API 壳：把 good/bad 定价实现暴露成 HTTP 服务，供关卡 4/5 黑盒检测。

真实团队里这就是你们的订单服务；本实验自带 30 行壳是为了能一键切换
被注入的实现（PRICING_IMPL=good|bad），不动 labs/11 的共有资产。
"""
import importlib
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

pricing = importlib.import_module(f"pricing_{os.environ.get('PRICING_IMPL', 'bad')}")
app = FastAPI(title="cost-funnel order api")
_ORDERS: dict[int, dict] = {}  # 内存订单表：id -> 回执数据
_SEQ = {"n": 0}


class OrderIn(BaseModel):
    prices: list[float]
    coupon: bool = False


@app.get("/api/health")
def health():
    return {"ok": True, "impl": pricing.__name__}


@app.post("/api/orders")
def create_order(body: OrderIn):
    subtotal = pricing.cart_total(body.prices)
    total = pricing.payable(subtotal, use_coupon=body.coupon)
    _SEQ["n"] += 1
    oid = _SEQ["n"]
    _ORDERS[oid] = {"subtotal": str(subtotal), "total": str(total),
                    "coupon": body.coupon}
    # total 以字符串进 JSON，原样暴露实现层的脏值——接口层断言才拦得住
    return {"id": oid, "subtotal": str(subtotal), "total": str(total)}


@app.get("/api/orders/{oid}/receipt")
def receipt(oid: int):
    if oid not in _ORDERS:
        raise HTTPException(404, "order not found")
    o = _ORDERS[oid]
    # 用户可见层：回执文本。float 脏值在这里变成用户肉眼可见的 ¥80.08999999999999
    return {"id": oid, "text": f"应付 ¥{o['total']}"}
