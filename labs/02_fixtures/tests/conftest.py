"""conftest.py——pytest 的"共享 fixture 仓库"：同目录及子目录的用例自动可见。

本文件演示三种最常用的 fixture 形态：
1. session 级昂贵资源（整个测试会话只建一次）
2. yield 式 setup/teardown（yield 前是 setup，之后是 teardown）
3. fixture 工厂（一条用例造 N 份数据）
"""
import pytest

from fake_db import FakeDB


@pytest.fixture(scope="session")
def db() -> FakeDB:
    """session 级：连接成本只付一次。yield 前是 setup，yield 后是 teardown。"""
    conn = FakeDB(dsn="sqlite://:memory:")  # setup：0.2s 的"昂贵"连接
    yield conn
    conn.close()  # teardown：会话结束时关闭，验证 closed 标志


@pytest.fixture()
def clean_db(db):
    """function 级：每个用例都拿到"干净表"——但复用同一个连接。

    作用域组合的经典手法：贵的部分 session 级共享，脏的部分 function 级重置。
    """
    db.users.clear()
    yield db
    db.users.clear()  # teardown 再清一次，保证乱序执行也不互相污染


@pytest.fixture()
def user_factory(clean_db):
    """fixture 工厂：返回的不是数据，而是"造数据的函数"。"""
    _seq = {"n": 0}

    def _make(name: str | None = None, n: int = 1) -> list[dict]:
        made = []
        for _ in range(n):
            _seq["n"] += 1
            made.append(clean_db.add_user(name or f"user_{_seq['n']}"))
        return made

    return _make
