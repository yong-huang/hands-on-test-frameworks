"""200 条"真实工作量"用例：每条 50ms 模拟 I/O——串行 10s、并行 ~2s 的素材。

用例完全独立：无共享状态、无顺序依赖（并行的前提，见 test_pollution 的反面教材）。
smoke/e2e marker 演示分层：smoke 子集免睡秒回，e2e 才付 50ms 成本。
"""
import pytest

SLOW_WORK_MS = 0.05  # 模拟一次真实 I/O（DB 查询 / RPC）


@pytest.mark.parametrize("i", range(150))
def test_case(i):
    """150 条常规用例：干的都是同一类'慢活'"""
    import time
    time.sleep(SLOW_WORK_MS)
    assert i >= 0


@pytest.mark.slow_work
@pytest.mark.parametrize("i", range(50))
def test_heavy_case(i):
    """50 条重型用例：同样 50ms——smoke 子集会把它们排除在外"""
    import time
    time.sleep(SLOW_WORK_MS)
    assert i < 50


@pytest.mark.smoke
def test_smoke_health():
    assert True


@pytest.mark.smoke
@pytest.mark.parametrize("i", range(5))
def test_smoke_core(i):
    """冒烟子集：不睡觉，秒级反馈"""
    assert i in range(5)
