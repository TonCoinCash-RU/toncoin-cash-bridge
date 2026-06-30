import pytest
from fastapi.testclient import TestClient

from app.main import app

_API_HEADERS = {"x-api-key": "test-bridge-key"}


@pytest.fixture
def client():
    return TestClient(app)


def test_healthz_without_api_key(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["service"] == "Bridge Service"


def test_bridge_assets_requires_api_key(client):
    assert client.get("/bridge/assets").status_code == 401
    res = client.get("/bridge/assets", headers=_API_HEADERS)
    assert res.status_code == 200
    ids = {a["id"] for a in res.json()["assets"]}
    assert ids == {"tcc", "btc", "sol"}


def test_bridge_route_tcc_btc(client):
    res = client.post(
        "/bridge/route",
        json={"from_asset": "tcc", "to_asset": "btc"},
        headers=_API_HEADERS,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["available"] is True
    assert body["step_count"] == 3


def test_bridge_route_btc_sol_unavailable(client):
    res = client.post(
        "/bridge/route",
        json={"from_asset": "btc", "to_asset": "sol"},
        headers=_API_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["available"] is False
