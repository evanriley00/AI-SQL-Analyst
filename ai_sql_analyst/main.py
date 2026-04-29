from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ai_sql_analyst.config import settings
from ai_sql_analyst.auth import Principal, require_api_key
from ai_sql_analyst.models import (
    AskRequest,
    AskResponse,
    ClientConfigResponse,
    EvalSuiteResponse,
    HealthResponse,
    MetricsResponse,
    QueryLogEntry,
    SchemaResponse,
)
from ai_sql_analyst.services.database import SCHEMA_REFERENCE, active_backend, initialize_database, list_tables
from ai_sql_analyst.services.evaluation import run_eval_suite
from ai_sql_analyst.services.query_service import answer_question, build_metrics, load_query_log


STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        llm_enabled=bool(settings.openai_api_key),
        database_backend=active_backend(),
        database_path=settings.postgres_dsn if active_backend() == "postgres" else str(settings.db_path),
        auth_enabled=bool(settings.allowed_api_keys()),
    )


@app.get("/client-config", response_model=ClientConfigResponse, include_in_schema=False)
def client_config() -> ClientConfigResponse:
    return ClientConfigResponse(
        browser_api_key=settings.browser_api_key,
        default_workspace_id="demo",
    )


@app.get("/schema", response_model=SchemaResponse)
def schema(_principal: Principal = Depends(require_api_key)) -> SchemaResponse:
    return SchemaResponse(
        schema_markdown=SCHEMA_REFERENCE,
        tables=list_tables(),
    )


@app.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, principal: Principal = Depends(require_api_key)) -> AskResponse:
    workspace_id = payload.workspace_id or principal.workspace_id
    return answer_question(payload.question, workspace_id=workspace_id)


@app.get("/history", response_model=list[QueryLogEntry])
def history(
    limit: int = 25,
    principal: Principal = Depends(require_api_key),
) -> list[QueryLogEntry]:
    return load_query_log(limit=max(1, min(limit, 100)), workspace_id=principal.workspace_id)


@app.get("/metrics", response_model=MetricsResponse)
def metrics(principal: Principal = Depends(require_api_key)) -> MetricsResponse:
    return build_metrics(workspace_id=principal.workspace_id)


@app.post("/evals/run", response_model=EvalSuiteResponse)
def evals_run(principal: Principal = Depends(require_api_key)) -> EvalSuiteResponse:
    return run_eval_suite(workspace_id=principal.workspace_id)
