# AI SQL Analyst

AI SQL Analyst is a recruiter-readable portfolio project for natural-language analytics over structured business data.

It is designed to show:
- Text-to-SQL application engineering
- SQL guardrails and safe query execution
- Schema-aware prompting
- FastAPI backend development
- Observable analytics workflows
- PostgreSQL-backed application architecture
- Dockerized local infrastructure
- Kubernetes manifests with probes, services, secrets, and autoscaling
- Terraform Kubernetes deployment option
- Automated tests and text-to-SQL evals

## What It Does

The app accepts plain-English analytics questions such as:

- `Why did revenue drop last month?`
- `Show the top customers by revenue`
- `How many support tickets were opened by priority this quarter?`

It then:
- Reads the available database schema and metric definitions
- Generates a SQL query from the user question
- Validates the SQL to block unsafe statements
- Executes the query against a demo analytics database
- Returns the SQL, rows, and an analyst-style summary

## Current Application

- FastAPI API
- PostgreSQL warehouse via Docker Compose
- SQLite fallback for quick local development
- Natural-language to SQL pipeline
- SQL guardrails that allow read-only queries
- Schema context endpoint
- Query logging with latency and row counts
- Heuristic fallback when no OpenAI API key is configured
- Analyst console served by the API
- Query history and aggregate system metrics
- API key authentication
- Workspace-scoped SQL guardrails for multi-tenant analytics
- Built-in SQL evaluation suite
- Automated tests for API behavior and guardrails
- CI workflow for tests, evals, and Postgres integration

## Project Structure

```text
ai-sql-analyst/
  ai_sql_analyst/
    config.py
    main.py
    models.py
    db/
      migrations.py
      seeds.py
    services/
      database.py
      evaluation.py
      query_service.py
      sql_guardrails.py
    static/
      app.js
      index.html
      styles.css
  tests/
  k8s/
    base/
  terraform/
    kubernetes/
  evals.py
  manage.py
  docker-compose.yml
  Dockerfile
  data/
    demo_warehouse.db
    query_log.jsonl
  .env.example
  requirements.txt
```

## Quick Start

### Option A: Run With SQLite

```bash
pip install -r ai-sql-analyst/requirements.txt
python ai-sql-analyst/manage.py init-db
uvicorn ai_sql_analyst.main:app --reload --app-dir ai-sql-analyst
```

Then open:

```text
http://127.0.0.1:8000
```

### Option B: Run With PostgreSQL

```bash
cd ai-sql-analyst
docker compose up --build
```

The API will run at:

```text
http://127.0.0.1:8000
```

The Compose stack starts:
- `api`: FastAPI application
- `postgres`: PostgreSQL 16 warehouse

### Configuration

Copy `ai-sql-analyst/.env.example` into `.env` or set environment variables directly.

Key options:

```bash
AI_SQL_ANALYST_DATABASE_BACKEND=sqlite
AI_SQL_ANALYST_POSTGRES_DSN=postgresql://ai_sql:ai_sql_password@localhost:5432/ai_sql_analyst
AI_SQL_ANALYST_API_KEYS=dev-api-key
AI_SQL_ANALYST_BROWSER_API_KEY=dev-api-key
OPENAI_API_KEY=your-key-here
```

If no OpenAI key is set, the app still works with deterministic SQL fallback for common analytics questions.

### Database Management

Apply migrations and seed the configured database:

```bash
python ai-sql-analyst/manage.py init-db
```

Run the eval suite:

```bash
python ai-sql-analyst/manage.py evals
```

## API

### `GET /health`

Returns service status and whether the LLM-backed SQL generator is enabled.

### `GET /schema`

Returns the schema reference used to ground SQL generation.

### `POST /ask`

Request:

```json
{
  "question": "Show the top 5 customers by revenue",
  "workspace_id": "demo"
}
```

Protected API endpoints require:

```text
X-API-Key: dev-api-key
```

### `GET /history`

Returns recent query log entries.

### `GET /metrics`

Returns aggregate usage telemetry, including total queries, fallback rate, average latency, and recent questions.

### `POST /evals/run`

Runs the built-in text-to-SQL evaluation suite.

## Verification

Run the automated tests:

```bash
pytest ai-sql-analyst/tests
```

Run the eval suite directly:

```bash
python ai-sql-analyst/evals.py
```

The GitHub Actions workflow in `.github/workflows/ai-sql-analyst-ci.yml` runs both tests and evals.

## Kubernetes

The Kubernetes base manifests live in `k8s/base`.

Apply with Kustomize:

```bash
kubectl apply -k ai-sql-analyst/k8s/base
```

The base includes:
- Namespace
- ConfigMap
- Secret example
- PostgreSQL StatefulSet and Service
- API Deployment and Service
- Readiness and liveness probes
- HorizontalPodAutoscaler
- Optional ingress example

For a real environment, replace `k8s/base/secret.example.yaml` with a sealed secret, external secret, or cluster-managed secret.

## Terraform

The Terraform Kubernetes example lives in `terraform/kubernetes`.

```bash
cd ai-sql-analyst/terraform/kubernetes
terraform init
terraform plan \
  -var="api_keys=replace-me" \
  -var="postgres_password=replace-me"
```

This provisions the namespace, app config, secret, PostgreSQL StatefulSet, and API Deployment/Service into an existing Kubernetes cluster.

Response shape:

```json
{
  "query_id": "abc123def456",
  "created_at": "2026-04-27T15:11:33.148303+00:00",
  "question": "Show the top 5 customers by revenue",
  "sql": "SELECT ...",
  "summary": "Northstar Health generated the highest revenue in the sample data.",
  "columns": ["customer_name", "total_revenue"],
  "rows": [
    ["Northstar Health", 12400.0]
  ],
  "row_count": 5,
  "latency_ms": 42,
  "used_fallback": false,
  "chart": {
    "chart_type": "bar",
    "x": "customer_name",
    "y": "total_revenue",
    "title": "Revenue analysis"
  },
  "warnings": []
}
```

## Demo Schema

The seeded database models a lightweight B2B SaaS analytics warehouse:

- `customers`
- `invoices`
- `support_tickets`

This keeps the project business-facing and makes the SQL portfolio signal much clearer than another generic chatbot demo.

## Next Up

- Role-based workspace permissions
- Retrieval over metric definitions and BI docs
- Cloud deployment walkthrough
