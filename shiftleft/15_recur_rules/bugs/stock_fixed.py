"""bug02 · 并发超卖（修复版）：check 与 act 收进同一把锁——窗口被关掉。"""
import threading


class Stock:
    def __init__(self, n: int):
        self.remaining = n
        self._lock = threading.Lock()

    def reserve(self, k: int = 1) -> bool:
        with self._lock:
            if self.remaining >= k:
                self.remaining -= k
                return True
        return False
