from __future__ import annotations

from fastapi.testclient import TestClient

from ai_sql_analyst.config import settings
from ai_sql_analyst.main import app
from ai_sql_analyst.services.database import initialize_database


settings.openai_api_key = ""
initialize_database()
client = TestClient(app)
HEADERS = {"X-API-Key": "dev-api-key"}


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_endpoint() -> None:
    response = client.post(
        "/ask",
        json={"question": "Show monthly revenue trend"},
        headers=HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["row_count"] >= 1
    assert "SELECT" in payload["sql"]
    assert "workspace_id" in payload["sql"]


def test_evals_endpoint() -> None:
    response = client.post("/evals/run", headers=HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["pass_rate"] >= 0.8


def test_protected_endpoint_requires_api_key() -> None:
    response = client.post("/ask", json={"question": "Show monthly revenue trend"})

    assert response.status_code == 401
