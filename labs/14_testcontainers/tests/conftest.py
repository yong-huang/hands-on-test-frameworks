"""lab 14 conftest：session 级 Postgres 容器——整套测试共享一个容器实例。

testcontainers 在首个用例前拉起容器、会话结束后自动销毁（含 with 块退出）。
"""
import sys
from pathlib import Path

import pytest

try:
    from testcontainers.community.postgres import PostgresContainer
except ImportError:  # 旧版本命名空间
    from testcontainers.postgres import PostgresContainer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pg_store  # noqa: E402


@pytest.fixture(scope="session")
def pg_dsn():
    """session 级容器：起一次，全类共享；测试结束自动销毁"""
    with PostgresContainer("postgres:16-alpine") as pg:
        dsn = pg.get_connection_url().replace("postgresql+psycopg2://", "postgresql://")
        pg_store.init_db(dsn)
        yield dsn


@pytest.fixture()
def clean_pg(pg_dsn):
    """每条用例截表隔离（等价 lab 13 的 truncate 策略）"""
    conn = pg_store.connect(pg_dsn)
    with conn, conn.cursor() as cur:
        cur.execute("TRUNCATE orders RESTART IDENTITY")
    conn.close()
    yield pg_dsn
    conn = pg_store.connect(pg_dsn)
    with conn, conn.cursor() as cur:
        cur.execute("TRUNCATE orders RESTART IDENTITY")
    conn.close()
