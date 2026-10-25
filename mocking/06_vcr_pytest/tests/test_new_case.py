"""后补的新用例：没有 cassette。

none 模式 + --block-network 下它必红——没有录制就没有回放，无录制的请求
要么被 vcrpy 拒绝、要么被 socket 级断网挡下，绝无可能泄漏到真实网络。
"""
import httpx
import pytest

BASE = "http://127.0.0.1:9600"


@pytest.mark.vcr
def test_new_endpoint():
    with httpx.Client(base_url=BASE, trust_env=False) as client:
        r = client.get("/reports/nonexistent")
        assert r.status_code == 200
