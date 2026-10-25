"""项目 17 局部夹具：失败自动留证（复用项目 09 的钩子模式）。"""
import os
import sys
import time

import pytest

# 复用项目 10 的 POM 与项目 11 的数据文件——终极套件是组装，不是重写
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "10_pom")))


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def auto_evidence(request, driver):
    yield
    rep = getattr(request.node, "rep_call", None)
    inject = os.environ.get("INJECT_FAILURE") == "1"
    if rep is not None and rep.failed and inject:
        out = os.path.join(os.path.dirname(__file__), "reports")
        os.makedirs(out, exist_ok=True)
        stamp = time.strftime("%H%M%S")
        safe = request.node.name.replace("/", "_")[:50]
        driver.save_screenshot(os.path.join(out, f"FAIL_{safe}_{stamp}.png"))
        with open(os.path.join(out, f"FAIL_{safe}_{stamp}.source.html"), "w", encoding="utf-8") as f:
            f.write(driver.page_source)
