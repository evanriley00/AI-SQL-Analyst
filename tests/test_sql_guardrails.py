from __future__ import annotations

import pytest

from ai_sql_analyst.services.sql_guardrails import validate_read_only_sql


def test_allows_read_only_select_and_adds_limit() -> None:
    sql = validate_read_only_sql("SELECT customer_name FROM customers")

    assert sql == "SELECT customer_name FROM customers LIMIT 100"


def test_blocks_write_statement() -> None:
    with pytest.raises(ValueError, match="Only SELECT"):
        validate_read_only_sql("DELETE FROM customers")


def test_blocks_unknown_tables() -> None:
    with pytest.raises(ValueError, match="Unknown table"):
        validate_read_only_sql("SELECT * FROM payroll")


def test_blocks_multiple_statements() -> None:
    with pytest.raises(ValueError, match="Multiple SQL"):
        validate_read_only_sql("SELECT * FROM customers; SELECT * FROM invoices")
