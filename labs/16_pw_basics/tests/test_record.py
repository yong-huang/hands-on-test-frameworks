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
