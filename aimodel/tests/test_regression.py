from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch

from app.main import create_app
from app.model import ModelServer
import app.main as main_module


@pytest.fixture
def client():
    server = ModelServer(model_path="/nonexistent/model.gguf", n_gpu_layers=0)
    main_module.model_server = server

    with patch("app.main.get_model_server", return_value=server):
        with patch("app.model.get_model_server", return_value=server):
            app = create_app()
            with TestClient(app) as test_client:
                yield test_client


def test_regression_standby_completions_fallback(client):
    """When model file is in standby mode, returns fallback chat response without crashing."""
    payload = {
        "messages": [{"role": "user", "content": "Spent 25 on Uber"}],
        "temperature": 0.2,
    }
    res = client.post("/v1/chat/completions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["choices"][0]["message"]["role"] == "assistant"
    assert "standby" in data["choices"][0]["message"]["content"].lower() or len(data["choices"][0]["message"]["content"]) > 0


def test_regression_standby_generate_fallback(client):
    """When model file is in standby mode, generate endpoint responds safely."""
    payload = {"prompt": "Analyze expenses:"}
    res = client.post("/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
