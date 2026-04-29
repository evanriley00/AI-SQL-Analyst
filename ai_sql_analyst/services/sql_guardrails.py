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


def validate_read_only_sql(sql: str, *, workspace_id: str = "demo") -> str:
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

    safe_sql = " ".join(apply_workspace_scope(normalized.rstrip(";"), workspace_id=workspace_id).split())
    if " limit " not in f" {lowered} ":
        safe_sql = f"{safe_sql} LIMIT {settings.max_query_rows}"
    return safe_sql


def apply_workspace_scope(sql: str, *, workspace_id: str) -> str:
    if not workspace_id.replace("-", "").replace("_", "").isalnum():
        raise ValueError("workspace_id contains unsupported characters.")

    references = table_references(sql)
    if not references:
        return sql

    predicates = [
        f"{alias}.workspace_id = '{workspace_id}'"
        for table_name, alias in references
        if table_name in set(list_tables())
    ]
    if not predicates:
        return sql

    scope_predicate = " AND ".join(dict.fromkeys(predicates))
    boundary = first_clause_boundary(sql)
    prefix = sql[:boundary].rstrip()
    suffix = sql[boundary:]
    if re.search(r"\bwhere\b", prefix, flags=re.IGNORECASE):
        return f"{prefix} AND {scope_predicate} {suffix.lstrip()}"
    return f"{prefix} WHERE {scope_predicate} {suffix.lstrip()}"


def table_references(sql: str) -> list[tuple[str, str]]:
    pattern = re.compile(
        r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)(?:\s+(?:as\s+)?([a-z_][a-z0-9_]*))?",
        flags=re.IGNORECASE,
    )
    references: list[tuple[str, str]] = []
    stop_words = {"where", "join", "on", "group", "order", "limit"}
    for table_name, alias in pattern.findall(sql):
        clean_alias = alias if alias and alias.lower() not in stop_words else table_name
        references.append((table_name.lower(), clean_alias))
    return references


def first_clause_boundary(sql: str) -> int:
    matches = [
        match.start()
        for match in re.finditer(r"\b(group\s+by|order\s+by|limit)\b", sql, flags=re.IGNORECASE)
    ]
    return min(matches) if matches else len(sql)
