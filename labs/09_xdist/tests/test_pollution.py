"""共享状态污染（预期在并行下失败——教学演示）"""
from pollution import bump_and_report


def test_step_1():
    assert bump_and_report() == 1


def test_step_2():
    assert bump_and_report() == 2  # 依赖 test_step_1 先在同一 worker 跑过


def test_step_3():
    assert bump_and_report() == 3  # 同上，且赌的是文件顺序
