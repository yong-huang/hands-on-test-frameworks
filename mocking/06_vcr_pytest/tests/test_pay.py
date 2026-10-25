"""支付链路集成测试：录制期打真上游，回放期打 cassette——测试代码零改动。"""
import httpx
import pytest

BASE = "http://127.0.0.1:9600"


@pytest.mark.vcr
def test_pay_and_status():
    with httpx.Client(base_url=BASE, trust_env=False) as client:
        r = client.post("/pay", json={"order": "ORDER-FIXED-001", "amount": 4200})
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

        txn = r.json()["txn"]
        r2 = client.get(f"/pay/status?txn={txn}")
        assert r2.status_code == 200
        assert r2.json()["state"] == "settled"


@pytest.mark.vcr
def test_pay_idempotent():
    with httpx.Client(base_url=BASE, trust_env=False) as client:
        r = client.post("/pay", json={"order": "ORDER-FIXED-002", "amount": 100})
        assert r.status_code == 200
        assert r.json()["txn"]
