from __future__ import annotations

import argparse
import json

from ai_sql_analyst.config import settings
from ai_sql_analyst.services.database import active_backend, execute_query, initialize_database
from ai_sql_analyst.services.evaluation import run_eval_suite


def init_db() -> None:
    initialize_database()
    columns, rows = execute_query("SELECT COUNT(*) AS customer_count FROM customers")
    print(
        json.dumps(
            {
                "backend": active_backend(),
                "database": settings.postgres_dsn if active_backend() == "postgres" else str(settings.db_path),
                "columns": columns,
                "rows": rows,
            },
            indent=2,
        )
    )


def run_evals() -> None:
    initialize_database()
    result = run_eval_suite(workspace_id="demo")
    print(json.dumps(result.model_dump(), indent=2))
    if result.failed:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="AI SQL Analyst management commands")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init-db", help="Apply migrations and seed the configured database")
    subcommands.add_parser("evals", help="Run the text-to-SQL evaluation suite")
    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "evals":
        run_evals()


if __name__ == "__main__":
    main()
