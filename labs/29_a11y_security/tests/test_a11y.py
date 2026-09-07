"""lab 29 用例：axe-core 对 SUT 全页扫 WCAG 违例（门禁：无 critical/serious）。"""
import json
import os

import pytest
from axe_playwright_python.sync_playwright import Axe

PAGES = ["/", "/login.html", "/slow.html"]


@pytest.mark.parametrize("path", PAGES)
def test_no_high_impact_violations(page, path):
    base = os.environ.get("SUT_URL", "http://127.0.0.1:8929")
    page.goto(base + path)
    axe = Axe()
    report = axe.run(page)
    violations = [v for v in report.response["violations"]
                  if v["impact"] in ("critical", "serious")]
    assert violations == [], json.dumps(
        [{"id": v["id"], "impact": v["impact"],
          "nodes": len(v["nodes"]), "help": v["help"]} for v in violations],
        ensure_ascii=False, indent=2)
