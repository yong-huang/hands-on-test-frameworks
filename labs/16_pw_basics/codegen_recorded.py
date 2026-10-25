"""observe ③ codegen 录制器产出的原始骨架（保留作参考，不是 pytest 用例）。

用法（SUT 必须在 8916 端口运行）：
    ./pw_basics.sh apply                        # 起 SUT
    ../../.venv/bin/python codegen_recorded.py  # 弹出真浏览器自动下单，停留 10s 供观察
    ./pw_basics.sh clean                        # 停 SUT

为什么不能放进 tests/：
  - 模块级的 `with sync_playwright()` 会在 pytest 收集（import）阶段直接执行；
    headless=False 需要图形界面，CI 无 X server 时会让整个收集阶段报错（exit 2）
  - codegen 只录操作、不录断言——接口失败它也"跑完不报错"，不是测试
同一流程的正式 pytest 版见 tests/test_orders_e2e.py::test_create_order
（page fixture 管浏览器生命周期 + expect 断言 + uuid 隔离客户名）。
"""
import re, time
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://127.0.0.1:8916/")
    page.get_by_role("textbox", name="客户名").click()
    page.get_by_role("textbox", name="客户名").fill("李四")
    page.get_by_role("textbox", name="商品").click()
    page.get_by_role("textbox", name="商品").fill("电脑")
    page.get_by_role("spinbutton", name="数量").click()
    page.get_by_role("spinbutton", name="数量").fill("3")
    page.get_by_role("spinbutton", name="单价").click()
    page.get_by_role("spinbutton", name="单价").fill("5000")
    page.get_by_role("button", name="创建订单").click()

    time.sleep(10)
    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
