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


def test_smoke_aimodel_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "model_path" in data


def test_smoke_aimodel_root(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert "Expense AI Model Server" in data["name"]
