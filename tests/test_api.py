from __future__ import annotations

from fastapi.testclient import TestClient

from ai_sql_analyst.config import settings
from ai_sql_analyst.main import app


settings.openai_api_key = ""
client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_endpoint() -> None:
    response = client.post("/ask", json={"question": "Show monthly revenue trend"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["row_count"] >= 1
    assert "SELECT" in payload["sql"]


def test_evals_endpoint() -> None:
    response = client.post("/evals/run")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["pass_rate"] >= 0.8
