"""植入 flaky B：共享状态残留（上一轮通过时留下的标记，让下一轮必挂）。

这是「单独跑绿、连跑红」的经典形态：首轮 pass 且写共享文件，之后每轮都因残留失败。
"""
from pathlib import Path

MARK = Path(__file__).parent / ".shared_state"


def test_order_dependent_victim():
    if MARK.exists():
        assert False, "植入的顺序依赖 flaky：检测到上一轮残留的共享状态"
    # 模拟通过但泄漏共享状态（真实世界：缓存文件/临时表/环境变量没清）
    MARK.write_text("leftover", encoding="utf-8")
