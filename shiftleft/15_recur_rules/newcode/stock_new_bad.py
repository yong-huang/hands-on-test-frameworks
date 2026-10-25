"""拦截目标：写法全新的同类缺陷——check-then-act 无锁（bug02 再世）。"""
import time


class CouponStock:
    def __init__(self, n: int):
        self.left = n

    def grab(self) -> bool:
        if self.left >= 1:        # check
            time.sleep(0.001)     # 竞态窗口
            self.left -= 1        # act（无锁）
            return True
        return False
