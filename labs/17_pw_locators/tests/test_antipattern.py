"""反面教材：用固定 sleep + 不等待的断言——"看起来能跑"的写法为什么必挂。

test_sleep_too_short 预期失败（真实触发）：延迟列表要 2s 才渲染，
sleep(0.5) 后 count()（不等待！）当场返回 0。
对照 test_waits.py：expect 自动等到为止。
"""
import time


def test_sleep_too_short(page):
    page.goto("/slow.html")
    page.get_by_role("button", name="加载延迟列表（2 秒后渲染）").click()
    time.sleep(0.5)                                       # 反模式①：赌固定时长
    assert page.locator("#late-list .box").count() == 3   # 反模式②：count 不等待


def test_sleep_generously_but_still_wasteful(page):
    """反模式的反面：sleep 给足 3s 也绿——但每条用例白等 3s，200 条用例=10 分钟"""
    page.goto("/slow.html")
    page.get_by_role("button", name="加载延迟列表（2 秒后渲染）").click()
    time.sleep(3)
    assert page.locator("#late-list .box").count() == 3
    # 正确写法见 test_waits.py：expect(...).to_have_count(3) 平均只等实际需要的时长
