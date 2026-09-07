"""Postgres 版数据层：与 SUT 的 store.py（SQLite）语义对齐，便于行为对比。

SQL 方言差异点（这些差异正是本实验要实测记录的）：
- 占位符 %s vs SQLite 的 ?
- 主键自增用 GENERATED + RETURNING 拿回 id（SQLite 靠 cursor.lastrowid）
- 类型强约束（SQLite 是类型亲和，插错类型也能塞进去）
"""
import psycopg2
import psycopg2.extras

DDL = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer TEXT NOT NULL,
    item TEXT NOT NULL,
    qty INTEGER NOT NULL CHECK (qty > 0),
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    status TEXT NOT NULL DEFAULT 'created',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def connect(dsn: str):
    conn = psycopg2.connect(dsn, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = False
    return conn


def init_db(dsn: str) -> None:
    conn = connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(DDL)
    finally:
        conn.close()


def create_order(dsn, customer: str, item: str, qty: int, price: float) -> dict:
    conn = connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO orders (customer, item, qty, price) "
                "VALUES (%s,%s,%s,%s) RETURNING *",
                (customer, item, qty, price),
            )
            return dict(cur.fetchone())
    finally:
        conn.close()


def get_order(dsn, order_id: int) -> dict | None:
    conn = connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
            row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_orders(dsn, limit: int = 20, offset: int = 0) -> list[dict]:
    conn = connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM orders ORDER BY id DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def update_status(dsn, order_id: int, status: str) -> dict | None:
    conn = connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE orders SET status=%s WHERE id=%s RETURNING *", (status, order_id)
            )
            row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_order(dsn, order_id: int) -> bool:
    conn = connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM orders WHERE id=%s", (order_id,))
            return cur.rowcount > 0
    finally:
        conn.close()
