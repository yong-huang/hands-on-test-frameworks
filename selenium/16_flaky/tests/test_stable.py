"""稳定对照组：零误报是检测器的底线。"""


def test_stable_math():
    assert 1 + 1 == 2


def test_stable_string():
    assert "selenium".upper() == "SELENIUM"
