"""插件演示用例：快/慢/挂/分层标记 四种形态"""
import time

import pytest


def test_fast_case():
    assert 1 + 1 == 2


def test_slow_case():
    """0.3s > 默认阈值 0.1s：会被插件自动打上 slow 标并记账"""
    time.sleep(0.3)
    assert True


@pytest.mark.ministore_tier(tier="smoke")
def test_tiered_smoke():
    assert True


@pytest.mark.ministore_tier(tier="core")
def test_tiered_core():
    assert True


def test_failing_case():
    """故意失败：插件会给它落一份 contexts/*.json 上下文"""
    assert 1 == 2, "预期失败：演示失败上下文自动落盘"
