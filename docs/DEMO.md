# Demo Walkthrough

Use this flow when showing the project in an interview or portfolio review.

## 1. Open The Console

```bash
uvicorn ai_sql_analyst.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## 2. Ask A Revenue Question

Question:

```text
Show the top customers by revenue
```

Point out:

- Generated SQL is visible.
- Results are shown in a table.
- Chart metadata is generated.
- The response includes query ID, latency, row count, and warnings.

## 3. Show SQL Guardrails

The backend validates that generated SQL is read-only and scoped to the workspace:

```sql
WHERE i.workspace_id = 'demo' AND c.workspace_id = 'demo'
```

This is the key engineering detail: the system does not blindly execute model output.

## 4. Run Evals

```bash
python manage.py evals
```

Expected:

```text
6/6 passed
```

Explain that this catches regressions in generated SQL behavior.

## 5. Show Deployment Assets

Highlight:

- `Dockerfile`
- `docker-compose.yml`
- `k8s/base`
- `terraform/kubernetes`
- GitHub Actions workflow

## 30-Second Pitch

AI SQL Analyst is a production-style text-to-SQL analytics app. It turns natural-language business questions into guarded SQL, scopes queries by workspace, executes against SQLite or PostgreSQL, logs query telemetry, and includes an eval suite plus Docker/Kubernetes/Terraform deployment assets.
