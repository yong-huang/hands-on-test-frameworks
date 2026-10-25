"""坏样本 2：5 个反模式点。"""
import time


def test_with_sleep():
    time.sleep(0.01)  # 埋点：测试内真实等待（sleep_in_test）
    assert True  # 埋点 2：又一个空断言（assert_constant）


def test_print_debug():
    result = {"total": 42}
    print(result)  # 埋点：调试残留（print_debug）
    assert result["total"] == 42


# def test_never_written():
#     assert 1 == 2  # 埋点：注释掉的断言（commented_assert，尸体测试）


def test_len_never_negative():
    assert len([1, 2]) >= 0  # 埋点：恒真数学比较（tautology_math）
