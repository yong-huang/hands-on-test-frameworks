"""迁移测试：建表脚本必须幂等（空库可执行、旧库可重复执行）"""
import sys
from pathlib import Path

import pytest

import store

SUT_DIR = Path(__file__).resolve().parents[2] / "11_sut_app" / "app"
sys.path.insert(0, str(SUT_DIR))


def test_init_db_on_empty(tmp_path):
    db = tmp_path / "empty.db"
    store.init_db(db)                       # 空库首跑
    assert store.current_version(db) == 1
    assert store.count(db) == 0


def test_init_db_repeatable(tmp_path):
    db = tmp_path / "old.db"
    store.init_db(db)
    store.create_order(db, "迁移幸存者", "x", 1, 1.0)
    store.init_db(db)                       # 旧库重跑：不能丢数据、不能报错
    assert store.current_version(db) == 1   # 版本不重复累加
    assert store.count(db) == 1             # 数据完好
    with store.connect(db) as conn:         # 迁移记录也只此一条
        n = conn.execute("SELECT COUNT(*) c FROM schema_migrations").fetchone()["c"]
    assert n == 1


def test_migration_version_monotonic(tmp_path):
    """新版本迁移 = INSERT OR IGNORE 新版本号：可重复但只记一次"""
    db = tmp_path / "v.db"
    store.init_db(db)
    with store.connect(db) as conn:
        conn.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES (2)")
    assert store.current_version(db) == 2
    store.init_db(db)
    assert store.current_version(db) == 2
