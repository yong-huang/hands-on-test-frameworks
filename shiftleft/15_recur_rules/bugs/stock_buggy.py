"""bug02 · 并发超卖（缺陷版）：check-then-act 无锁，检查与扣减之间是竞态窗口。

sleep 模拟真实检查耗时（查库存要走一次读库）——窗口不是构造的，是常态的。
"""
import time


class Stock:
    def __init__(self, n: int):
        self.remaining = n

    def reserve(self, k: int = 1) -> bool:
        if self.remaining >= k:      # check
            time.sleep(0.002)        # 检查耗时 → 竞态窗口
            self.remaining -= k      # act（无锁）
            return True
        return False
