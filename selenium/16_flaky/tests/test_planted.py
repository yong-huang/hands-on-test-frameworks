"""植入的 2 个 flaky（注释即声明，对照 architect/13 的做法）。

- random_flake：50% 概率失败（随机型）
- order_dependent_victim：首轮通过并泄漏 .shared_state，之后每轮必挂（顺序依赖型）
"""
import random
from pathlib import Path

MARK = Path(__file__).parent / ".shared_state"


def test_random_flake():
    assert random.random() > 0.4, "植入的随机失败（40% 失败率）"


def test_order_dependent_victim():
    if MARK.exists():
        assert False, "植入的顺序依赖 flaky：检测到上一轮残留的共享状态"
    MARK.write_text("leftover", encoding="utf-8")
