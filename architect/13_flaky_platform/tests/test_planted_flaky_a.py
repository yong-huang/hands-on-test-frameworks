"""植入 flaky A：随机失败（演示「时过时不过」的经典形态）。"""
import random


def test_random_flake():
    assert random.random() > 0.4, "植入的随机 flaky"
