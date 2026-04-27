from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class ChartSpec(BaseModel):
    chart_type: str
    x: str
    y: str
    title: str


class AskResponse(BaseModel):
    query_id: str
    created_at: str
    question: str
    sql: str
    summary: str
    columns: list[str]
    rows: list[list[object]]
    row_count: int
    latency_ms: int
    used_fallback: bool
    chart: ChartSpec | None = None
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    app_name: str
    llm_enabled: bool
    database_backend: str
    database_path: str


class SchemaResponse(BaseModel):
    schema_markdown: str
    tables: list[str]


class QueryLogEntry(BaseModel):
    query_id: str
    timestamp: str
    question: str
    sql: str
    row_count: int
    latency_ms: int
    used_fallback: bool


class MetricsResponse(BaseModel):
    total_queries: int
    fallback_rate: float
    average_latency_ms: float
    average_row_count: float
    recent_queries: list[QueryLogEntry]


class EvalCaseResult(BaseModel):
    name: str
    question: str
    passed: bool
    sql: str
    row_count: int
    latency_ms: int
    checks: list[str]
    failures: list[str]


class EvalSuiteResponse(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    results: list[EvalCaseResult]
