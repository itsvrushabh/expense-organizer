import pytest
import storage
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_storage():
    """Reset in-memory storage before and after every test."""
    storage._expenses.clear()
    storage._next_id = 1
    yield
    storage._expenses.clear()
    storage._next_id = 1


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
