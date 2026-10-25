"""会话管理·重构版——依赖注入 + 端口适配器（六边形边界）。

与 legacy 的行为契约完全一致（issue/validate 语义不变），变化只有一条：
时间、随机源、存储这三个「说不准的东西」全部变成构造参数——
测试注入 FixedClock/FixedIdGenerator/内存仓，生产注入 SystemXxx，
两边跑的是同一份业务代码。
"""
import secrets
import time
from typing import Protocol


class Clock(Protocol):
    """时间端口：业务只问 now()，不关心时间从哪来。"""

    def now(self) -> float: ...


class SystemClock:
    """生产实现：单调时钟。"""

    def now(self) -> float:
        return time.monotonic()


class FixedClock:
    """测试替身：手动拨针——「过了 3601 秒」不再需要真等 3601 秒。"""

    def __init__(self, start: float = 0.0):
        self._now = start

    def now(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class IdGenerator(Protocol):
    """随机源端口。"""

    def generate(self) -> str: ...


class SystemIdGenerator:
    def generate(self) -> str:
        return secrets.token_hex(16)


class SessionStore(Protocol):
    """存储端口：内存实现换 Redis 实现不动业务。"""

    def put(self, token: str, role: str, issued_at: float) -> None: ...

    def get(self, token: str) -> tuple[str, float] | None: ...

    def pop(self, token: str) -> None: ...


class InMemorySessionStore:
    def __init__(self):
        self._data: dict[str, tuple[str, float]] = {}

    def put(self, token: str, role: str, issued_at: float) -> None:
        self._data[token] = (role, issued_at)

    def get(self, token: str) -> tuple[str, float] | None:
        return self._data.get(token)

    def pop(self, token: str) -> None:
        self._data.pop(token, None)


class SessionService:
    """业务本体：与 legacy 的 issue_token/validate_token 语义一一对应。"""

    def __init__(self, clock: Clock, ids: IdGenerator, store: SessionStore,
                 ttl: float = 3600.0):
        self.clock = clock
        self.ids = ids
        self.store = store
        self.ttl = ttl  # ttl 变普通参数，不再需要 monkeypatch 模块常量

    def issue(self, username: str, role: str) -> str:
        token = self.ids.generate()
        self.store.put(token, role, self.clock.now())
        return token

    def validate(self, token: str, required_role: str | None = None) -> str | None:
        entry = self.store.get(token)
        if entry is None:
            return None
        role, issued_at = entry
        if self.clock.now() - issued_at > self.ttl:
            self.store.pop(token)
            return None
        if required_role is not None and role != required_role:
            return None
        return role
