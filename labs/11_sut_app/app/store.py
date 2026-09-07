"""SUT 数据层：SQLite 订单存储（lab 13/14 的集成测试对象，接口保持稳定）。"""
import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT NOT NULL,
    item TEXT NOT NULL,
    qty INTEGER NOT NULL CHECK (qty > 0),
    price REAL NOT NULL CHECK (price >= 0),
    status TEXT NOT NULL DEFAULT 'created',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_write_lock = threading.Lock()  # SQLite 单写者：应用层串行化写请求


def connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path) -> None:
    """建表（幂等）；版本号记入 schema_migrations——lab 13 迁移测试的对象"""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.execute("INSERT OR IGNORE INTO schema_migrations (version) VALUES (1)")


def current_version(db_path) -> int:
    row = connect(db_path).execute("SELECT MAX(version) v FROM schema_migrations").fetchone()
    return row["v"] or 0


def create_order(db_path, customer: str, item: str, qty: int, price: float) -> dict:
    with _write_lock:
        conn = connect(db_path)
        try:
            with conn:  # 事务边界：INSERT 成功即提交
                cur = conn.execute(
                    "INSERT INTO orders (customer, item, qty, price) VALUES (?,?,?,?)",
                    (customer, item, qty, price),
                )
                oid = cur.lastrowid
            return dict(conn.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone())
        finally:
            conn.close()


def get_order(db_path, order_id: int) -> dict | None:
    row = connect(db_path).execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    return dict(row) if row else None


def list_orders(db_path, status: str | None = None, limit: int = 20, offset: int = 0) -> tuple[list[dict], int]:
    """返回 (订单列表, 总数)——分页信息由调用方拼进响应头"""
    where, args = ("WHERE status=?", [status]) if status else ("", [])
    with connect(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM orders {where} ORDER BY id DESC LIMIT ? OFFSET ?",
            [*args, limit, offset],
        ).fetchall()
        total = conn.execute(f"SELECT COUNT(*) c FROM orders {where}", args).fetchone()["c"]
    return [dict(r) for r in rows], total


def update_status(db_path, order_id: int, status: str) -> dict | None:
    with _write_lock, connect(db_path) as conn:
        cur = conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
        if cur.rowcount == 0:
            return None
    return get_order(db_path, order_id)


def delete_order(db_path, order_id: int) -> bool:
    with _write_lock, connect(db_path) as conn:
        return conn.execute("DELETE FROM orders WHERE id=?", (order_id,)).rowcount > 0


def count(db_path) -> int:
    return connect(db_path).execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
