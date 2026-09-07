"""SUT 数据层切换到真 Postgres：CRUD 回归 + 与 SQLite 的行为差异实测。"""
import sys
import threading
from pathlib import Path

import pytest

import pg_store

SUT_DIR = Path(__file__).resolve().parents[2] / "11_sut_app" / "app"
sys.path.insert(0, str(SUT_DIR))
import store as sqlite_store  # noqa: E402  SUT 同款 SQLite 数据层，用于对照


def test_crud_roundtrip_on_postgres(clean_pg):
    dsn = clean_pg
    o = pg_store.create_order(dsn, "PG测试员", "容器商品", 2, 19.9)
    assert o["id"] >= 1 and o["status"] == "created"
    assert pg_store.get_order(dsn, o["id"])["customer"] == "PG测试员"
    assert pg_store.update_status(dsn, o["id"], "paid")["status"] == "paid"
    assert pg_store.delete_order(dsn, o["id"]) is True
    assert pg_store.get_order(dsn, o["id"]) is None


def test_pg_rejects_wrong_type(clean_pg, tmp_path):
    """差异 ① 类型强约束：SQLite 会把字符串塞进 INTEGER 列（类型亲和），PG 拒绝"""
    sqlite_db = tmp_path / "s.db"
    sqlite_store.init_db(sqlite_db)
    sqlite_store.create_order(sqlite_db, "亲和试验", "x", "3(字符串也能进!)", 1.0)  # SQLite 竟然不报错
    with pytest.raises(Exception):
        pg_store.create_order(clean_pg, "强约束", "x", "3(字符串)", 1.0)  # PG 直接拒绝


def test_pg_concurrent_writers_no_lock_error(clean_pg, tmp_path):
    """差异 ② 并发写：SQLite 单写者（未串行化时报 database is locked）；
    Postgres MVCC 多写者并发无锁冲突——20 线程裸写全部成功"""
    results: list[str] = []

    def writer(i):
        conn = pg_store.connect(clean_pg)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO orders (customer, item, qty, price) VALUES (%s,%s,%s,%s)",
                    (f"并发{i}", "x", 1, 1.0),
                )
            results.append("ok")
        except Exception as e:  # noqa: BLE001
            results.append(str(e))
        finally:
            conn.close()

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(20)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert all(r == "ok" for r in results), [r for r in results if r != "ok"]


def test_pg_numeric_rounding(clean_pg, tmp_path):
    """差异 ③ NUMERIC(10,2) 定点 vs SQLite REAL 浮点：金额存储行为不同"""
    o = pg_store.create_order(clean_pg, "精度测试", "x", 1, 0.1 + 0.2)
    assert str(o["price"]) in {"0.30", "0.3"}  # PG 存的是十进制 0.30
    # 对照组：SQLite 里同款计算是浮点 0.30000000000000004
    sqlite_db = tmp_path / "s2.db"
    sqlite_store.init_db(sqlite_db)
    s = sqlite_store.create_order(sqlite_db, "精度测试", "x", 1, 0.1 + 0.2)
    assert s["price"] == pytest.approx(0.30000000000000004)
