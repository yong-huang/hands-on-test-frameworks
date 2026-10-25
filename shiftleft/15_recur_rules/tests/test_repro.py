"""复现测试：3 个 bug 的域语义各一条核心用例，按实现参数化。

「buggy 红、fixed 绿」由脚本分两次运行并核验退出码（-k buggy / -k fixed）——
这就是「先写复现测试」的留档形态：测试在缺陷存在时红、在修复后绿。
"""
import importlib
from datetime import datetime, timezone

import pytest

IMPLS = ["buggy", "fixed"]


def _load(domain: str, impl: str):
    return importlib.import_module(f"{domain}_{impl}")


@pytest.mark.parametrize("impl", IMPLS)
def test_bug01_money_exact_cents(impl):
    """复现：19.99 + 80.10 − 20 必须精确等于 80.09（float 版差之毫厘）。"""
    mod = _load("money", impl)
    assert str(mod.total("19.99", "80.10", "20")) == "80.09"


@pytest.mark.parametrize("impl", IMPLS)
def test_bug02_no_oversell(impl):
    """复现：库存 10 面对 60 并发扣减，成功数必须恰好 10（超卖即红）。"""
    from concurrent.futures import ThreadPoolExecutor

    mod = _load("stock", impl)
    stock = mod.Stock(10)
    barrier = __import__("threading").Barrier(60)

    def hit(_):
        barrier.wait()
        return stock.reserve(1)

    with ThreadPoolExecutor(max_workers=60) as pool:
        results = list(pool.map(hit, range(60)))
    assert sum(results) == 10
    assert stock.remaining == 0


@pytest.mark.parametrize("impl", IMPLS)
def test_bug03_timezone_boundary(impl):
    """复现：UTC 15:30 = 北京 23:30，已过截单线，before_cutoff 必须为 False。"""
    mod = _load("cutoff", impl)
    utc = datetime(2026, 3, 7, 15, 30, tzinfo=timezone.utc)
    assert mod.before_cutoff(utc) is False
