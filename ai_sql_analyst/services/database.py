from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Iterator, Protocol

import psycopg
from psycopg.rows import dict_row

from ai_sql_analyst.config import settings
from ai_sql_analyst.db.migrations import POSTGRES_SCHEMA, SQLITE_SCHEMA
from ai_sql_analyst.db.seeds import CUSTOMERS, INVOICES, SUPPORT_TICKETS


SCHEMA_REFERENCE = """# Warehouse Schema

## customers
- customer_id: integer primary key
- workspace_id: text tenant/workspace identifier
- customer_name: text
- segment: text
- region: text in US sales regions
- signup_date: date

## invoices
- invoice_id: integer primary key
- workspace_id: text tenant/workspace identifier
- customer_id: integer foreign key to customers.customer_id
- invoice_month: date, first day of month
- amount_usd: numeric revenue amount
- plan_name: text

## support_tickets
- ticket_id: integer primary key
- workspace_id: text tenant/workspace identifier
- customer_id: integer foreign key to customers.customer_id
- created_at: date
- priority: text
- status: text
- resolution_hours: numeric

## Metric definitions
- revenue means SUM(invoices.amount_usd)
- customer count means COUNT(DISTINCT customers.customer_id)
- average resolution time means AVG(support_tickets.resolution_hours)
- top customers by revenue means grouping invoices by customer and ordering by total revenue descending
"""


class CursorLike(Protocol):
    description: Any

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        ...

    def fetchone(self) -> Any:
        ...

    def fetchall(self) -> list[Any]:
        ...


class ConnectionLike(Protocol):
    def cursor(self) -> CursorLike:
        ...

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> Any:
        ...

    def executemany(self, sql: str, params_seq: list[tuple[Any, ...]]) -> Any:
        ...

    def commit(self) -> None:
        ...

    def close(self) -> None:
        ...


def active_backend() -> str:
    backend = settings.database_backend.lower().strip()
    if backend not in {"sqlite", "postgres"}:
        raise ValueError("AI_SQL_ANALYST_DATABASE_BACKEND must be either 'sqlite' or 'postgres'.")
    return backend


def ensure_data_dir() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)


def get_sqlite_connection() -> sqlite3.Connection:
    ensure_data_dir()
    connection = sqlite3.connect(settings.db_path)
    connection.row_factory = sqlite3.Row
    return connection


def get_postgres_connection() -> psycopg.Connection[Any]:
    return psycopg.connect(settings.postgres_dsn, row_factory=dict_row)


@contextmanager
def get_connection() -> Iterator[ConnectionLike]:
    backend = active_backend()
    connection: ConnectionLike
    if backend == "postgres":
        connection = get_postgres_connection()
    else:
        connection = get_sqlite_connection()

    try:
        yield connection
    finally:
        connection.close()


def initialize_database() -> None:
    backend = active_backend()
    ensure_data_dir()

    with get_connection() as connection:
        apply_migrations(connection, backend=backend)
        ensure_workspace_columns(connection, backend=backend)
        seed_database(connection, backend=backend)
        connection.commit()


def apply_migrations(connection: ConnectionLike, *, backend: str) -> None:
    schema = POSTGRES_SCHEMA if backend == "postgres" else SQLITE_SCHEMA
    if backend == "postgres":
        with connection.cursor() as cursor:
            cursor.execute(schema)
        return
    connection.executescript(schema)  # type: ignore[attr-defined]


def seed_database(connection: ConnectionLike, *, backend: str) -> None:
    placeholder = "%s" if backend == "postgres" else "?"
    if table_has_rows(connection, table_name="customers"):
        return

    connection.executemany(
        f"""
        INSERT INTO customers (customer_id, workspace_id, customer_name, segment, region, signup_date)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        CUSTOMERS,
    )
    connection.executemany(
        f"""
        INSERT INTO invoices (invoice_id, workspace_id, customer_id, invoice_month, amount_usd, plan_name)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        INVOICES,
    )
    connection.executemany(
        f"""
        INSERT INTO support_tickets (ticket_id, workspace_id, customer_id, created_at, priority, status, resolution_hours)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        SUPPORT_TICKETS,
    )


def ensure_workspace_columns(connection: ConnectionLike, *, backend: str) -> None:
    for table_name in list_tables():
        if column_exists(connection, backend=backend, table_name=table_name, column_name="workspace_id"):
            continue
        if backend == "postgres":
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'demo'"
            )
        else:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'demo'"
            )


def column_exists(
    connection: ConnectionLike,
    *,
    backend: str,
    table_name: str,
    column_name: str,
) -> bool:
    if backend == "postgres":
        cursor = connection.execute(
            """
            SELECT COUNT(*) AS row_count
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (table_name, column_name),
        )
        row = cursor.fetchone()
        return int(row["row_count"] if isinstance(row, dict) else row[0]) > 0

    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    rows = cursor.fetchall()
    return any(row["name"] == column_name for row in rows)


def table_has_rows(connection: ConnectionLike, *, table_name: str) -> bool:
    cursor = connection.execute(f"SELECT COUNT(*) AS row_count FROM {table_name}")
    row = cursor.fetchone()
    if isinstance(row, dict):
        return int(row["row_count"]) > 0
    return int(row[0]) > 0


def execute_query(sql: str) -> tuple[list[str], list[list[object]]]:
    with get_connection() as connection:
        cursor = connection.execute(sql)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description or []]
        return columns, [normalize_row(row, columns) for row in rows]


def normalize_row(row: Any, columns: list[str]) -> list[object]:
    if isinstance(row, dict):
        values = [row[column] for column in columns]
    else:
        values = list(row)
    return [normalize_value(value) for value in values]


def normalize_value(value: object) -> object:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()  # type: ignore[no-any-return]
    return value


def list_tables() -> list[str]:
    return ["customers", "invoices", "support_tickets"]


def discover_tables(sql: str) -> set[str]:
    lowered = sql.lower()
    matches = re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)", lowered)
    return set(matches)
