"""pytest-recording 公共配置：cassette 落在 tests/cassettes/，随测试文件进 git。"""
import pytest


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "record_mode": "once",   # 缺省值；实际由 --record-mode CLI 参数覆盖
        "filter_headers": ["content-length"],
    }
