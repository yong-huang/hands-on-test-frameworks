"""项目 9 局部夹具：失败自动留证（截图 + page source），通过用例零附件。"""
import os
import time

import pytest


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def auto_evidence(request, driver):
    yield
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        out = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(out, exist_ok=True)
        stamp = time.strftime("%H%M%S")
        safe = request.node.name.replace("/", "_")[:60]
        driver.save_screenshot(os.path.join(out, f"FAIL_{safe}_{stamp}.png"))
        with open(os.path.join(out, f"FAIL_{safe}_{stamp}.source.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
