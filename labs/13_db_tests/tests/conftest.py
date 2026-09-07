"""lab 13 conftest：两种隔离策略的 fixture（indirect 参数切换）+ 速度计量。

策略 A fresh_db：每条用例一个全新 DB 文件——最干净，代价是每例付建表成本。
策略 B truncate_db：session 级共享 DB，用例前后 DELETE FROM——快，但依赖清理纪律。
（第三种"事务回滚隔离"为何缺席？因为 SUT 数据层是"一操作一连接"设计，
用例拿不到外部事务的控制权——README 4.3 专门讨论这个真实取舍。）
"""
import sys
import time
from pathlib import Path

import pytest

SUT_DIR = Path(__file__).resolve().parents[2] / "11_sut_app" / "app"
sys.path.insert(0, str(SUT_DIR))  # 直接复用 SUT 的数据层

import store  # noqa: E402


@pytest.fixture(scope="session")
def session_db(tmp_path_factory):
    db = tmp_path_factory.mktemp("db") / "session.db"
    store.init_db(db)
    return db


@pytest.fixture()
def fresh_db(tmp_path, request):
    """策略 A：全新库文件。记录建库耗时用于对比报告。"""
    db = tmp_path / "fresh.db"
    t0 = time.perf_counter()
    store.init_db(db)
    request.node._iso_ms = (time.perf_counter() - t0) * 1000
    yield db
    db.unlink(missing_ok=True)


@pytest.fixture()
def truncate_db(session_db, request):
    """策略 B：共享库 + 截表。setup 与 teardown 都清，双保险。"""
    t0 = time.perf_counter()
    store.init_db(session_db)
    with store.connect(session_db) as conn:
        conn.execute("DELETE FROM orders")
    request.node._iso_ms = (time.perf_counter() - t0) * 1000
    yield session_db
    with store.connect(session_db) as conn:
        conn.execute("DELETE FROM orders")


@pytest.fixture()
def db(request):
    """按 mark 切换：@pytest.mark.isolation("fresh"|"truncate") 决定策略"""
    strategy = request.node.get_closest_marker("isolation").args[0]
    return request.getfixturevalue({"fresh": "fresh_db", "truncate": "truncate_db"}[strategy])
