"""过期语义对照：同一个「token 过期即拒绝」，两个实现的代价天差地别。

legacy 版必须真睡——TTL 是模块常量，只能 monkeypatch 成 1 秒再 real sleep；
refactored 版拨一下 FixedClock 的针，毫秒级完成。耗时差异由 measure_dft.py
外部实测留档（验收①的 <100ms vs ≥1s）。
"""
import time

import pytest

from legacy import sessions as legacy
from refactored.sessions import (
    FixedClock,
    InMemorySessionStore,
    SessionService,
    SystemIdGenerator,
)


def test_expiry_legacy_needs_real_sleep(monkeypatch):
    """重构前：monkeypatch 模块常量 + 真实等待——准备代码 4 行、墙钟 ≥1s。"""
    monkeypatch.setattr(legacy, "TTL", 1.0)          # 准备 1：把模块常量改小
    legacy._TOKENS.clear()                            # 准备 2：清模块级状态
    token = legacy.issue_token("dave", "admin")       # 准备 3：真实签发
    time.sleep(1.05)                                  # 准备 4：真等 TTL 过去（ wall time 大头）
    assert legacy.validate_token(token) is None       # 行为：过期即拒绝


def test_expiry_fake_clock_instant():
    """重构后：拨针代替等待——准备代码 2 行（构造注入对象），墙钟毫秒级。"""
    clock = FixedClock(start=0.0)                      # 准备：注入假钟
    svc = SessionService(clock, SystemIdGenerator(),
                         InMemorySessionStore(), ttl=3600.0)   # 注入随机源与存储
    token = svc.issue("dave", "admin")
    clock.advance(3601.0)                                             # 拨针：一小时后
    assert svc.validate(token) is None
