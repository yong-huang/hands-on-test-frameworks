"""稳定用例：3 条永远绿的——检测器的对照组（不该被误报）。"""


def test_stable_1():
    assert 1 + 1 == 2


def test_stable_2():
    assert "flaky" != "stable"


def test_stable_3():
    assert [1, 2, 3].pop() == 3
