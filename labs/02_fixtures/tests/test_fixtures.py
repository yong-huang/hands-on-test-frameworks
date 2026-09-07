"""lab 02 用例：作用域证据、yield teardown、工厂 fixture。

跑法（lab 目录下）：
    python -m pytest -c configs/pytest.ini -v -s
"""
import uuid

import pytest

from fake_db import FakeDB


# ---------- session 作用域证据：贵资源只建一次 ----------
def test_db_connection_is_shared(db, clean_db):
    """FakeDB.instances==1：4 条用例用了同一个 session 连接"""
    assert FakeDB.instances == 1


def test_db_dsn_preserved(db):
    assert db.dsn == "sqlite://:memory:"


# ---------- function 作用域：每用例干净的表 ----------
def test_clean_db_starts_empty(clean_db):
    assert clean_db.users == {}


def test_add_user(clean_db):
    u = clean_db.add_user("alice")
    assert clean_db.get_user(u["id"])["name"] == "alice"


def test_add_user_isolated(clean_db):
    """上一条用例加的 alice 不会漏到这里——function 级 teardown 生效"""
    assert all(u["name"] != "alice" for u in clean_db.users.values())


# ---------- 模块级作用域：module fixture 本模块只初始化一次 ----------
@pytest.fixture(scope="module")
def module_tag():
    return uuid.uuid4().hex


def test_module_scope_stable_1(module_tag):
    assert module_tag


def test_module_scope_stable_2(module_tag):
    """两条用例拿到同一个 uuid → module fixture 没有重建"""
    assert isinstance(module_tag, str)


# ---------- yield teardown 顺序 ----------
def test_session_db_open_until_end(db):
    """会话内任何时刻连接都未关闭；真正 close 发生在全部用例之后"""
    assert db.closed is False


# ---------- fixture 工厂：一条用例造 N 份数据 ----------
def test_factory_make_three(user_factory):
    users = user_factory(n=3)
    assert [u["id"] for u in users] == [1, 2, 3]


def test_factory_custom_name(user_factory):
    (u,) = user_factory(name="boss")
    assert u["name"] == "boss"


def test_factory_many_rows(user_factory):
    """造 10 份不同数据——工厂模式的威力：参数随便变"""
    users = user_factory(n=10)
    names = {u["name"] for u in users}
    assert len(names) == 10


# ---------- tmp_path：pytest 自带的"临时目录"fixture ----------
def test_tmp_path_fixture(tmp_path):
    """tmp_path 是 function 级唯一临时目录（Path 对象），用例结束自动清理"""
    f = tmp_path / "demo.txt"
    f.write_text("hello", encoding="utf-8")
    assert f.read_text(encoding="utf-8") == "hello"
    assert list(tmp_path.iterdir()) == [f]
