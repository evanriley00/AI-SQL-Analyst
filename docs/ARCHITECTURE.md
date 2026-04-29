# Architecture

AI SQL Analyst is structured as a small production-style analytics application rather than a single chatbot script.

## Request Flow

1. The browser console sends a question, `workspace_id`, and `X-API-Key`.
2. FastAPI validates the request with Pydantic models.
3. The auth layer checks the API key.
4. The query service generates SQL using an LLM when configured, otherwise deterministic fallback.
5. SQL guardrails enforce read-only access, known-table access, statement limits, and row limits.
6. Workspace scoping injects `workspace_id` predicates into the generated SQL.
7. The database adapter executes against SQLite or PostgreSQL.
8. The API returns SQL, summary, rows, chart metadata, warnings, latency, and query ID.
9. Query telemetry is written to JSONL for history and metrics.

## Backend Modules

- `ai_sql_analyst/main.py`: FastAPI routes and app lifecycle.
- `ai_sql_analyst/auth.py`: API key auth dependency.
- `ai_sql_analyst/models.py`: Request and response contracts.
- `ai_sql_analyst/services/query_service.py`: SQL generation, summaries, chart hints, logging, and metrics.
- `ai_sql_analyst/services/sql_guardrails.py`: SQL validation and workspace scope injection.
- `ai_sql_analyst/services/database.py`: SQLite/PostgreSQL adapter, migrations, seeding, and query execution.
- `ai_sql_analyst/services/evaluation.py`: Text-to-SQL evaluation suite.
- `ai_sql_analyst/db/migrations.py`: SQLite and PostgreSQL schema definitions.
- `ai_sql_analyst/db/seeds.py`: Demo SaaS warehouse data.

## Data Model

The demo warehouse models a lightweight B2B SaaS business:

- `customers`
- `invoices`
- `support_tickets`

Each table includes `workspace_id` so generated SQL can be scoped for multi-tenant analytics.

## Safety Controls

- Only `SELECT` statements are allowed.
- Write statements such as `INSERT`, `UPDATE`, `DELETE`, `DROP`, and `ALTER` are blocked.
- Unknown tables are blocked.
- Multiple SQL statements are blocked.
- Complex nested SELECTs are limited.
- Missing `LIMIT` clauses are added automatically.
- Workspace predicates are injected before `GROUP BY`, `ORDER BY`, and `LIMIT`.

## Operational Design

The project includes the pieces expected in a deployable service:

- `/health` endpoint for probes.
- Docker image definition.
- Docker Compose stack with Postgres.
- Kubernetes Deployment, Service, StatefulSet, ConfigMap, Secret, HPA, probes, and ingress example.
- Terraform example for Kubernetes resources.
- GitHub Actions for unit/API tests, evals, and Postgres integration.
