"""隔离区机制：quarantine.txt 里的用例（子串匹配 nodeid）自动 skip。"""
from pathlib import Path

import pytest

QUARANTINE = Path(__file__).parent / "quarantine.txt"


def pytest_collection_modifyitems(config, items):
    if not QUARANTINE.exists():
        return
    patterns = [ln.strip() for ln in QUARANTINE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not patterns:
        return
    for item in items:
        if any(p in item.nodeid for p in patterns):
            item.add_marker(pytest.mark.skip(reason=f"隔离区：{next(p for p in patterns if p in item.nodeid)}"))
