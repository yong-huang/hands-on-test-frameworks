"""非法 tier：--ministore 下收集期直接 UsageError（演示用，正常套件不含此文件）"""
import pytest


@pytest.mark.ministore_tier(tier="prod")  # prod 不在 smoke|core|slow 里
def test_bad_tier():
    assert True
