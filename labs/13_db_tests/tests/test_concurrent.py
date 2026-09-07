"""并发写冲突：SQLite 的锁行为 vs store 的应用层串行化"""
import threading

import pytest

import store

import sqlite3


def _raw_writer(db, results, i, busy_timeout_ms=0):
    conn = sqlite3.connect(db, timeout=busy_timeout_ms / 1000)
    try:
        conn.execute("BEGIN IMMEDIATE")  # 抢写锁
        conn.execute(
            "INSERT INTO orders (customer, item, qty, price) VALUES (?,?,?,?)",
            (f"并发{i}", "x", 1, 1.0),
        )
        conn.commit()
        results.append("ok")
    except sqlite3.OperationalError as e:
        results.append(str(e))
    finally:
        conn.close()


def test_unserialized_writers_conflict(tmp_path):
    """裸 SQLite：写者 A 持锁期间，写者 B（timeout=0）当场 'database is locked'

    这就是 lab 26 压测时 RPS 拐点的根源——SQLite 单写者。
    """
    db = tmp_path / "c.db"
    store.init_db(db)
    results: list[str] = []
    t1 = threading.Thread(target=_raw_writer, args=(db, results, 1))
    t1.start()
    # 确保写者 A 先拿到锁（ begun immediate 已在子线程里）
    _raw_writer(db, results, 2)  # 主线程当写者 B：timeout=0，撞锁必错
    t1.join()
    assert any("locked" in r for r in results), results


def test_store_serializes_writes(tmp_path):
    """store 的应用层写锁：20 线程并发下单，全部成功且条数正确"""
    db = tmp_path / "s.db"
    store.init_db(db)
    errs: list[Exception] = []

    def writer(i):
        try:
            store.create_order(db, f"线程{i}", "x", 1, 1.0)
        except Exception as e:  # noqa: BLE001
            errs.append(e)

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(20)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert errs == []
    assert store.count(db) == 20
