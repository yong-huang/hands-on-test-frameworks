"""测试环境：两套实现的同接口工厂——同一套行为测试跑两个实现，等价性由此证明。"""
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from legacy import sessions as legacy  # noqa: E402
from refactored.sessions import (  # noqa: E402
    FixedClock,
    InMemorySessionStore,
    SessionService,
    SystemClock,
    SystemIdGenerator,
)


class LegacyAdapter:
    """把 legacy 模块函数包装成与 SessionService 相同的接口——行为测试的通用插头。"""

    def issue(self, username: str, role: str) -> str:
        return legacy.issue_token(username, role)

    def validate(self, token: str, required_role: str | None = None) -> str | None:
        return legacy.validate_token(token, required_role)


@pytest.fixture(params=["legacy", "refactored"])
def make_service(request):
    """工厂 fixture：行为测试不写死实现，等价性 = 同一测试双实现全绿。"""
    if request.param == "legacy":
        def make_legacy():
            legacy._TOKENS.clear()      # 模块级状态：每个测试手动清场（痛点本体之一）
            legacy.TTL = 3600.0         # 防止其他测试 monkeypatch 残留
            return LegacyAdapter()
        return make_legacy

    def make_refactored():
        return SessionService(SystemClock(), SystemIdGenerator(),
                              InMemorySessionStore(), ttl=3600.0)
    return make_refactored


@pytest.fixture
def real_sleep():
    """legacy 过期测试的计时起点（wall time 由 measure_dft.py 外部实测，这里只提供语义）。"""
    return time.perf_counter
