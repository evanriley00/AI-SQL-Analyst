# Resume Bullets

## Project Title

**AI SQL Analyst | Production-Style Text-to-SQL Analytics Platform**

## Short Resume Version

- Built a production-style text-to-SQL analytics app using FastAPI, PostgreSQL, Docker, Kubernetes, and Terraform, enabling natural-language questions over structured SaaS warehouse data.
- Implemented SQL guardrails that enforce read-only queries, block unsafe statements and unknown tables, add row limits, and inject `workspace_id` filters for multi-tenant query isolation.
- Added API key authentication, query telemetry, history, latency metrics, chart metadata, and an analyst console for inspecting generated SQL and results.
- Created automated text-to-SQL eval suite and CI pipeline with unit/API tests plus PostgreSQL integration testing through GitHub Actions.

## Interview Expansion

- Designed the system so LLM output is treated as untrusted code: generated SQL must pass validation before execution.
- Supported both SQLite fallback for local development and PostgreSQL for production-style deployment.
- Added Kubernetes manifests with Deployment, StatefulSet, Services, ConfigMap, Secret, readiness/liveness probes, and HPA.
- Added Terraform example for provisioning the Kubernetes app resources into an existing cluster.

## One-Line Portfolio Description

Production-style AI analytics platform that converts business questions into guarded, workspace-scoped SQL with FastAPI, PostgreSQL, Docker, Kubernetes, Terraform, CI, and automated evals.
