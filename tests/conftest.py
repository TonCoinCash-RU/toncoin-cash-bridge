import pytest

from app.config import settings


@pytest.fixture(autouse=True)
def _bridge_test_api_key(monkeypatch):
    monkeypatch.setattr(settings, "bridge_api_key", "test-bridge-key")
