from unittest.mock import patch

import app.main as main_module
import pytest
from app.main import create_app
from app.model import ModelServer
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Provide a mock or standby model server for fast unit tests
    server = ModelServer(model_path="/nonexistent/model.gguf", n_gpu_layers=0)
    main_module.model_server = server

    with patch("app.main.get_model_server", return_value=server):
        with patch("app.model.get_model_server", return_value=server):
            app = create_app()
            with TestClient(app) as test_client:
                yield test_client


def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "Expense AI Model Server" in data["name"]
    assert "endpoints" in data


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "model_file_exists" in data
    assert "device" in data


def test_chat_completions_endpoint(client):
    payload = {
        "messages": [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": "Hello!"},
        ],
        "temperature": 0.1,
        "max_tokens": 128,
    }
    res = client.post("/v1/chat/completions", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["object"] == "chat.completion"
    assert len(data["choices"]) > 0
    assert "message" in data["choices"][0]
    assert data["choices"][0]["message"]["role"] == "assistant"


def test_generate_endpoint(client):
    payload = {
        "prompt": "Say hello:",
        "temperature": 0.1,
        "max_tokens": 32,
    }
    res = client.post("/generate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
