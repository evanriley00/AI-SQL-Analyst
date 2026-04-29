# AI SQL Analyst

Production-style text-to-SQL analytics app for asking business questions over structured SaaS data.

![AI SQL Analyst console](docs/assets/ai-sql-analyst-console.png)

## Why This Project Exists

AI SQL Analyst is built to demonstrate practical AI engineering plus real software engineering: FastAPI service design, SQL guardrails, Postgres-backed data access, auth, workspace scoping, Docker, Kubernetes, Terraform, CI, observability, and automated text-to-SQL evals.

It answers questions like:

- `Show the top customers by revenue`
- `Show monthly revenue trend`
- `How many support tickets were opened by priority?`
- `Break down revenue by customer segment`

## Technical Highlights

- **AI application layer:** Natural-language questions are converted into SQL using an LLM when configured, with deterministic fallback for repeatable demos and tests.
- **SQL safety:** Generated SQL is validated as read-only, blocked from unknown tables, limited by row count, and scoped by `workspace_id`.
- **Backend:** FastAPI, Pydantic models, service-layer separation, health checks, API docs, and static app serving.
- **Data layer:** SQLite fallback for quick local work and PostgreSQL support for production-style deployment.
- **Product surface:** Analyst console with query input, generated SQL, result table, chart preview, query history, metrics, and eval runner.
- **Auth and tenancy:** Protected endpoints use `X-API-Key`; requests include `workspace_id` and guardrails inject workspace predicates.
- **Operations:** Dockerfile, Docker Compose, Kubernetes manifests, Terraform example, liveness/readiness probes, HPA, and CI.
- **Quality:** Unit/API tests, SQL guardrail tests, text-to-SQL eval suite, and GitHub Actions with Postgres integration.

## Architecture

```mermaid
flowchart LR
    UI[Analyst Console] --> API[FastAPI API]
    API --> Auth[API Key Auth]
    API --> Generator[LLM or Fallback SQL Generator]
    Generator --> Guardrails[Read-only SQL Guardrails]
    Guardrails --> Scope[Workspace Scope Injection]
    Scope --> DB[(SQLite or PostgreSQL)]
    API --> Logs[Query Log and Metrics]
    API --> Evals[Text-to-SQL Eval Suite]
```

See [Architecture](docs/ARCHITECTURE.md) for the deeper walkthrough.

## Quick Start

### SQLite

```bash
pip install -r requirements.txt
python manage.py init-db
uvicorn ai_sql_analyst.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

### PostgreSQL With Docker Compose

```bash
docker compose up --build
```

The app runs at:

```text
http://127.0.0.1:8000
```

## Configuration

```bash
AI_SQL_ANALYST_DATABASE_BACKEND=sqlite
AI_SQL_ANALYST_POSTGRES_DSN=postgresql://ai_sql:ai_sql_password@localhost:5432/ai_sql_analyst
AI_SQL_ANALYST_API_KEYS=dev-api-key
AI_SQL_ANALYST_BROWSER_API_KEY=dev-api-key
OPENAI_API_KEY=your-key-here
```

If no OpenAI key is set, the app uses deterministic fallback SQL for common analytics questions.

## API

Protected endpoints require:

```text
X-API-Key: dev-api-key
```

Example:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key" \
  -d "{\"question\":\"Show the top customers by revenue\", \"workspace_id\":\"demo\"}"
```

Core endpoints:

- `GET /health`
- `GET /schema`
- `POST /ask`
- `GET /history`
- `GET /metrics`
- `POST /evals/run`

## Verification

```bash
pytest tests -q
python manage.py evals
kubectl kustomize k8s/base
docker compose config
```

Current local verification:

```text
tests: 11 passed
eval suite: 6/6 passed
kubectl kustomize: ok
docker compose config: ok
```

## Deployment

- Docker Compose: [docker-compose.yml](docker-compose.yml)
- Kubernetes: [k8s/base](k8s/base)
- Terraform Kubernetes example: [terraform/kubernetes](terraform/kubernetes)
- CI: [.github/workflows/ai-sql-analyst-ci.yml](.github/workflows/ai-sql-analyst-ci.yml)

See [Deployment](docs/DEPLOYMENT.md) for commands and environment notes.

## Project Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Demo Walkthrough](docs/DEMO.md)
- [Resume Bullets](docs/RESUME.md)
- [Roadmap](docs/ROADMAP.md)

## Tech Stack

Python, FastAPI, Pydantic, PostgreSQL, SQLite, Docker, Docker Compose, Kubernetes, Kustomize, Terraform, GitHub Actions, HTML, CSS, JavaScript, OpenAI-compatible LLM integration.
