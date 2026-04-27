from __future__ import annotations

import re

from ai_sql_analyst.config import settings
from ai_sql_analyst.services.database import discover_tables, list_tables


BLOCKED_TOKENS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "attach",
    "detach",
    "pragma",
    "replace",
    "truncate",
}


def validate_read_only_sql(sql: str) -> str:
    normalized = " ".join(sql.strip().split())
    if not normalized:
        raise ValueError("SQL generation returned an empty statement.")

    lowered = normalized.lower()
    if not lowered.startswith("select"):
        raise ValueError("Only SELECT queries are allowed.")

    tokens = set(re.findall(r"[a-z_]+", lowered))
    blocked = sorted(token for token in tokens if token in BLOCKED_TOKENS)
    if blocked:
        raise ValueError(f"Blocked SQL token(s) detected: {', '.join(blocked)}")

    if ";" in normalized[:-1]:
        raise ValueError("Multiple SQL statements are not allowed.")

    if lowered.count("select") > 3:
        raise ValueError("Generated SQL is too complex for the MVP guardrails.")

    referenced_tables = discover_tables(normalized)
    allowed_tables = set(list_tables())
    unknown_tables = sorted(referenced_tables - allowed_tables)
    if unknown_tables:
        raise ValueError(f"Unknown table(s) referenced: {', '.join(unknown_tables)}")

    safe_sql = normalized.rstrip(";")
    if " limit " not in f" {lowered} ":
        safe_sql = f"{safe_sql} LIMIT {settings.max_query_rows}"
    return safe_sql
