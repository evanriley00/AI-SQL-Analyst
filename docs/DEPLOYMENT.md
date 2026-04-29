# Deployment

This project supports three deployment modes: SQLite local development, PostgreSQL with Docker Compose, and Kubernetes.

## Local SQLite

```bash
pip install -r requirements.txt
python manage.py init-db
uvicorn ai_sql_analyst.main:app --reload
```

## Docker Compose

```bash
docker compose up --build
```

This starts:

- `api`: FastAPI application
- `postgres`: PostgreSQL 16

The API is available at:

```text
http://127.0.0.1:8000
```

## Kubernetes

Render the manifests:

```bash
kubectl kustomize k8s/base
```

Apply:

```bash
kubectl apply -k k8s/base
```

The Kubernetes base includes:

- Namespace
- ConfigMap
- Secret example
- PostgreSQL StatefulSet and Service
- API Deployment and Service
- Liveness and readiness probes
- HorizontalPodAutoscaler
- Optional ingress example

For real environments, replace `k8s/base/secret.example.yaml` with a sealed secret, external secret, or managed secret provider.

## Terraform

The Terraform example expects an existing Kubernetes cluster and local kubeconfig.

```bash
cd terraform/kubernetes
terraform init
terraform plan \
  -var="api_keys=replace-me" \
  -var="postgres_password=replace-me"
```

Terraform provisions:

- Namespace
- Secret
- ConfigMap
- PostgreSQL StatefulSet and Service
- API Deployment and Service

## Environment Variables

```bash
AI_SQL_ANALYST_DATABASE_BACKEND=postgres
AI_SQL_ANALYST_POSTGRES_DSN=postgresql://ai_sql:ai_sql_password@postgres:5432/ai_sql_analyst
AI_SQL_ANALYST_API_KEYS=dev-api-key
AI_SQL_ANALYST_BROWSER_API_KEY=dev-api-key
OPENAI_API_KEY=
```

## CI

GitHub Actions runs:

- Python tests
- Text-to-SQL eval suite
- Postgres-backed integration evals

Workflow:

```text
.github/workflows/ai-sql-analyst-ci.yml
```
