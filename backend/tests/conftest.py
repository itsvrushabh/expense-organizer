import pytest
import storage
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_storage():
    """Reset storage before and after every test."""
    storage._pool = None
    storage.reset_in_memory()
    yield
    storage._pool = None
    storage.reset_in_memory()


@pytest.fixture
def client():
    from main import app

    return TestClient(app)


@pytest.fixture
def sample_payload():
    def _make(**overrides):
        payload = {
            "description": "Lunch",
            "amount": 12.5,
            "category": "Food",
            "date": "2026-03-15",
        }
        payload.update(overrides)
        return payload

    return _make
