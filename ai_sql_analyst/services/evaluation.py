from __future__ import annotations

from dataclasses import dataclass

from ai_sql_analyst.models import EvalCaseResult, EvalSuiteResponse
from ai_sql_analyst.services.query_service import answer_question


@dataclass(frozen=True, slots=True)
class EvalCase:
    name: str
    question: str
    required_sql_terms: tuple[str, ...]
    min_rows: int = 1


EVAL_CASES = (
    EvalCase(
        name="top_customers_by_revenue",
        question="Show the top customers by revenue",
        required_sql_terms=("customers", "invoices", "sum", "group by", "order by"),
    ),
    EvalCase(
        name="monthly_revenue_trend",
        question="Show monthly revenue trend",
        required_sql_terms=("invoices", "invoice_month", "sum", "group by"),
    ),
    EvalCase(
        name="tickets_by_priority",
        question="How many support tickets were opened by priority?",
        required_sql_terms=("support_tickets", "priority", "count", "group by"),
    ),
    EvalCase(
        name="resolution_time_by_customer",
        question="Which customers have the longest average resolution time?",
        required_sql_terms=("support_tickets", "customers", "avg", "resolution_hours"),
    ),
    EvalCase(
        name="customers_by_region",
        question="Count customers by region",
        required_sql_terms=("customers", "region", "count", "group by"),
    ),
    EvalCase(
        name="revenue_by_segment",
        question="Break down revenue by customer segment",
        required_sql_terms=("customers", "invoices", "segment", "sum", "group by"),
    ),
)


def run_eval_suite() -> EvalSuiteResponse:
    results: list[EvalCaseResult] = []
    for case in EVAL_CASES:
        response = answer_question(case.question, force_fallback=True)
        lowered_sql = response.sql.lower()
        failures: list[str] = []
        checks: list[str] = []

        for term in case.required_sql_terms:
            check = f"SQL contains '{term}'"
            checks.append(check)
            if term not in lowered_sql:
                failures.append(check)

        row_check = f"Returns at least {case.min_rows} row(s)"
        checks.append(row_check)
        if response.row_count < case.min_rows:
            failures.append(row_check)

        results.append(
            EvalCaseResult(
                name=case.name,
                question=case.question,
                passed=not failures,
                sql=response.sql,
                row_count=response.row_count,
                latency_ms=response.latency_ms,
                checks=checks,
                failures=failures,
            )
        )

    passed = sum(1 for result in results if result.passed)
    total = len(results)
    return EvalSuiteResponse(
        total=total,
        passed=passed,
        failed=total - passed,
        pass_rate=round(passed / total, 3) if total else 0.0,
        results=results,
    )
