from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from urllib import error, request
from uuid import uuid4

from ai_sql_analyst.config import settings
from ai_sql_analyst.models import AskResponse, ChartSpec, MetricsResponse, QueryLogEntry
from ai_sql_analyst.services.database import SCHEMA_REFERENCE, active_backend, execute_query
from ai_sql_analyst.services.sql_guardrails import validate_read_only_sql


def generate_sql(
    question: str,
    *,
    workspace_id: str = "demo",
    force_fallback: bool = False,
) -> tuple[str, bool]:
    if settings.openai_api_key and not force_fallback:
        sql = _generate_sql_with_openai(question, workspace_id=workspace_id)
        if sql:
            return sql, False
    return _generate_sql_with_fallback(question), True


def _generate_sql_with_openai(question: str, *, workspace_id: str) -> str:
    payload = {
        "model": settings.model_name,
        "input": [
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"You translate business analytics questions into one safe {active_backend()} SELECT query. "
                            "Return only SQL with no markdown. Use only the schema provided. "
                            "Do not use write statements, temp tables, stored procedures, or vendor-specific extensions. "
                            f"Only answer for workspace_id '{workspace_id}'."
                        ),
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"{SCHEMA_REFERENCE}\n\n"
                            f"Workspace scope: {workspace_id}\n"
                            f"Question: {question}"
                        ),
                    },
                ],
            },
        ],
    }

    req = request.Request(
        url="https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError, json.JSONDecodeError):
        return ""

    output = body.get("output", [])
    for item in output:
        content = item.get("content", [])
        for block in content:
            text = _strip_sql_fences(block.get("text", "").strip())
            if text:
                return text
    return ""


def _generate_sql_with_fallback(question: str) -> str:
    lowered = question.lower()

    if "top" in lowered and "customer" in lowered and "revenue" in lowered:
        return """
        SELECT
            c.customer_name,
            ROUND(SUM(i.amount_usd), 2) AS total_revenue
        FROM invoices i
        JOIN customers c ON c.customer_id = i.customer_id
        GROUP BY c.customer_name
        ORDER BY total_revenue DESC
        LIMIT 5
        """

    if "revenue" in lowered and ("month" in lowered or "monthly" in lowered or "trend" in lowered):
        return """
        SELECT
            invoice_month,
            ROUND(SUM(amount_usd), 2) AS total_revenue
        FROM invoices
        GROUP BY invoice_month
        ORDER BY invoice_month
        """

    if "ticket" in lowered and ("priority" in lowered or "priorities" in lowered):
        return """
        SELECT
            priority,
            COUNT(*) AS ticket_count
        FROM support_tickets
        GROUP BY priority
        ORDER BY ticket_count DESC, priority ASC
        """

    if "resolution" in lowered or "resolve" in lowered:
        return """
        SELECT
            c.customer_name,
            ROUND(AVG(t.resolution_hours), 2) AS avg_resolution_hours
        FROM support_tickets t
        JOIN customers c ON c.customer_id = t.customer_id
        GROUP BY c.customer_name
        ORDER BY avg_resolution_hours DESC
        """

    if "region" in lowered and "customer" in lowered:
        return """
        SELECT
            region,
            COUNT(*) AS customer_count
        FROM customers
        GROUP BY region
        ORDER BY customer_count DESC, region ASC
        """

    if "segment" in lowered and "revenue" in lowered:
        return """
        SELECT
            c.segment,
            ROUND(SUM(i.amount_usd), 2) AS total_revenue
        FROM invoices i
        JOIN customers c ON c.customer_id = i.customer_id
        GROUP BY c.segment
        ORDER BY total_revenue DESC
        """

    return """
    SELECT
        c.customer_name,
        i.invoice_month,
        i.amount_usd
    FROM invoices i
    JOIN customers c ON c.customer_id = i.customer_id
    ORDER BY i.invoice_month DESC, i.amount_usd DESC
    LIMIT 10
    """


def _strip_sql_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def summarize_result(question: str, columns: list[str], rows: list[list[object]]) -> str:
    if not rows:
        return "No rows matched the question in the demo warehouse."

    lowered = question.lower()
    first_row = rows[0]
    normalized_columns = [column.lower() for column in columns]

    if (
        "top" in lowered
        and "revenue" in lowered
        and "customer_name" in normalized_columns
        and any("revenue" in column for column in normalized_columns)
    ):
        customer_index = normalized_columns.index("customer_name")
        revenue_index = next(
            index for index, column in enumerate(normalized_columns) if "revenue" in column
        )
        return (
            f"{first_row[customer_index]} is the top revenue customer in the current result set "
            f"at ${first_row[revenue_index]:,.2f}."
        )

    if (
        "month" in lowered
        and "revenue" in lowered
        and "invoice_month" in normalized_columns
        and any("revenue" in column for column in normalized_columns)
    ):
        return f"The result shows monthly revenue across the seeded warehouse, with {rows[-1][0]} as the latest month in the series."

    if "ticket" in lowered and "priority" in normalized_columns and any(
        "count" in column for column in normalized_columns
    ):
        priority_index = normalized_columns.index("priority")
        return f"{first_row[priority_index]} priority has the highest ticket volume in the current sample."

    return f"Returned {len(rows)} row(s) for the question using the demo analytics warehouse."


def infer_chart(columns: list[str], rows: list[list[object]], question: str) -> ChartSpec | None:
    if len(columns) < 2 or not rows:
        return None

    normalized_columns = [column.lower() for column in columns]
    numeric_column_index = next(
        (
            index
            for index, row_value in enumerate(rows[0])
            if isinstance(row_value, int | float) and not normalized_columns[index].endswith("_id")
        ),
        None,
    )
    label_column_index = next(
        (
            index
            for index, row_value in enumerate(rows[0])
            if isinstance(row_value, str) and index != numeric_column_index
        ),
        None,
    )
    if numeric_column_index is None or label_column_index is None:
        return None

    chart_type = "line" if "month" in normalized_columns[label_column_index] else "bar"
    title = "Result trend" if chart_type == "line" else "Result comparison"
    if "revenue" in question.lower():
        title = "Revenue analysis"
    elif "ticket" in question.lower():
        title = "Ticket analysis"

    return ChartSpec(
        chart_type=chart_type,
        x=columns[label_column_index],
        y=columns[numeric_column_index],
        title=title,
    )


def build_warnings(*, used_fallback: bool, row_count: int) -> list[str]:
    warnings: list[str] = []
    if used_fallback:
        warnings.append("Used deterministic SQL fallback because LLM generation is unavailable or failed.")
    if row_count >= settings.max_query_rows:
        warnings.append("Result set reached the configured row limit.")
    return warnings


def log_query(
    *,
    query_id: str,
    timestamp: str,
    workspace_id: str,
    question: str,
    sql: str,
    row_count: int,
    latency_ms: int,
    used_fallback: bool,
) -> None:
    settings.query_log_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "query_id": query_id,
        "timestamp": timestamp,
        "workspace_id": workspace_id,
        "question": question,
        "sql": sql,
        "row_count": row_count,
        "latency_ms": latency_ms,
        "used_fallback": used_fallback,
    }
    with settings.query_log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")


def answer_question(
    question: str,
    *,
    workspace_id: str = "demo",
    force_fallback: bool = False,
) -> AskResponse:
    started = time.perf_counter()
    query_id = uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()
    sql, used_fallback = generate_sql(
        question,
        workspace_id=workspace_id,
        force_fallback=force_fallback,
    )
    safe_sql = validate_read_only_sql(sql, workspace_id=workspace_id)
    columns, rows = execute_query(safe_sql)
    latency_ms = int((time.perf_counter() - started) * 1000)
    summary = summarize_result(question, columns, rows)
    log_query(
        query_id=query_id,
        timestamp=created_at,
        workspace_id=workspace_id,
        question=question,
        sql=safe_sql,
        row_count=len(rows),
        latency_ms=latency_ms,
        used_fallback=used_fallback,
    )
    return AskResponse(
        query_id=query_id,
        created_at=created_at,
        question=question,
        sql=safe_sql,
        summary=summary,
        columns=columns,
        rows=rows,
        row_count=len(rows),
        latency_ms=latency_ms,
        used_fallback=used_fallback,
        chart=infer_chart(columns, rows, question),
        warnings=build_warnings(used_fallback=used_fallback, row_count=len(rows)),
    )


def load_query_log(limit: int = 25, *, workspace_id: str | None = None) -> list[QueryLogEntry]:
    if not settings.query_log_path.exists():
        return []

    entries: list[QueryLogEntry] = []
    with settings.query_log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            entries.append(
                QueryLogEntry(
                    query_id=str(payload.get("query_id", "")),
                    timestamp=str(payload.get("timestamp", "")),
                    workspace_id=str(payload.get("workspace_id", "demo")),
                    question=str(payload.get("question", "")),
                    sql=str(payload.get("sql", "")),
                    row_count=int(payload.get("row_count", 0)),
                    latency_ms=int(payload.get("latency_ms", 0)),
                    used_fallback=bool(payload.get("used_fallback", False)),
                )
            )
    if workspace_id is not None:
        entries = [entry for entry in entries if entry.workspace_id == workspace_id]
    return list(reversed(entries[-limit:]))


def build_metrics(*, workspace_id: str | None = None) -> MetricsResponse:
    recent = load_query_log(limit=1000, workspace_id=workspace_id)
    total = len(recent)
    if total == 0:
        return MetricsResponse(
            total_queries=0,
            fallback_rate=0.0,
            average_latency_ms=0.0,
            average_row_count=0.0,
            recent_queries=[],
        )

    fallback_count = sum(1 for entry in recent if entry.used_fallback)
    average_latency = sum(entry.latency_ms for entry in recent) / total
    average_row_count = sum(entry.row_count for entry in recent) / total
    return MetricsResponse(
        total_queries=total,
        fallback_rate=round(fallback_count / total, 3),
        average_latency_ms=round(average_latency, 2),
        average_row_count=round(average_row_count, 2),
        recent_queries=recent[:10],
    )
