"""并发复现模板（bug02 防复发资产）：任何「扣减库存/名额」的类都必须通过
本模板——60 并发抢 10 个名额，成功数恰好 10。喂给它带同类缺陷的新代码，
模板当场拦下（红 = 拦截成功）。

替换目标：改 TARGET 变量指向新类（类需提供 reserve()/grab() 语义接口）。
"""
import importlib
import threading
from concurrent.futures import ThreadPoolExecutor

TARGET = "stock_new_bad:CouponStock"  # 演示：指向拦截目标；接入真实代码时改这里


def _load_target():
    mod_name, cls_name = TARGET.split(":")
    return getattr(importlib.import_module(mod_name), cls_name)


def test_template_no_oversell():
    cls = _load_target()
    stock = cls(10)
    barrier = threading.Barrier(60)

    def hit(_):
        barrier.wait()
        grab = getattr(stock, "reserve", None) or getattr(stock, "grab")
        return grab(1) if "reserve" in dir(stock) else grab()

    with ThreadPoolExecutor(max_workers=60) as pool:
        results = list(pool.map(hit, range(60)))
    assert sum(results) == 10, f"超卖：{sum(results)} 个成功 > 10 个名额"
    assert stock.left == 0 or stock.remaining == 0
