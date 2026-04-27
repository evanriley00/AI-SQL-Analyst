from __future__ import annotations

from ai_sql_analyst.services.database import initialize_database
from ai_sql_analyst.services.query_service import answer_question


def test_answers_top_customers_question() -> None:
    initialize_database()

    response = answer_question("Show the top customers by revenue", force_fallback=True)

    assert response.row_count >= 1
    assert "customers" in response.sql.lower()
    assert "invoices" in response.sql.lower()
    assert response.columns
    assert response.chart is not None


def test_answers_ticket_priority_question() -> None:
    initialize_database()

    response = answer_question("How many support tickets were opened by priority?", force_fallback=True)

    assert response.row_count >= 1
    assert "support_tickets" in response.sql.lower()
    assert "priority" in response.sql.lower()
