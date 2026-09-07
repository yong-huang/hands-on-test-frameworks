"""修复版：fixture 每条用例发一个独立计数器——天然可并行"""
import pytest


@pytest.fixture()
def counter():
    return {"n": 0}


def test_step_1_fixed(counter):
    counter["n"] += 1
    assert counter["n"] == 1


def test_step_2_fixed(counter):
    counter["n"] += 1
    assert counter["n"] == 1  # 只关心"自己这条用例"里的行为


def test_step_3_fixed(counter):
    counter["n"] += 2
    assert counter["n"] == 2
