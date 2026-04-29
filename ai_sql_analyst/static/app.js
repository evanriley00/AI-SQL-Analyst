const form = document.querySelector("#query-form");
const input = document.querySelector("#question-input");
const sqlOutput = document.querySelector("#sql-output");
const summaryTitle = document.querySelector("#summary-title");
const summaryText = document.querySelector("#summary-text");
const queryId = document.querySelector("#query-id");
const table = document.querySelector("#result-table");
const warnings = document.querySelector("#warnings");
const chart = document.querySelector("#chart");
const chartTitle = document.querySelector("#chart-title");
const chartKind = document.querySelector("#chart-kind");
const modeValue = document.querySelector("#mode-value");
const rowCount = document.querySelector("#row-count");
const latencyValue = document.querySelector("#latency-value");
const metricTotal = document.querySelector("#metric-total");
const metricLatency = document.querySelector("#metric-latency");
const metricFallback = document.querySelector("#metric-fallback");
const historyList = document.querySelector("#history-list");
const runEvals = document.querySelector("#run-evals");
const evalRate = document.querySelector("#eval-rate");
const evalResults = document.querySelector("#eval-results");
let clientConfig = {
  browser_api_key: "dev-api-key",
  default_workspace_id: "demo",
};

async function fetchJson(url, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };
  if (!url.includes("/client-config") && clientConfig.browser_api_key) {
    headers["X-API-Key"] = clientConfig.browser_api_key;
  }
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || payload.error || `Request failed: ${response.status}`);
  }
  return response.json();
}

function renderTable(columns, rows) {
  const thead = table.querySelector("thead");
  const tbody = table.querySelector("tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  const headerRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = column;
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

function renderWarnings(items) {
  warnings.innerHTML = "";
  items.forEach((item) => {
    const div = document.createElement("div");
    div.className = "warning";
    div.textContent = item;
    warnings.appendChild(div);
  });
}

function renderChart(response) {
  chart.innerHTML = "";
  if (!response.chart) {
    chartTitle.textContent = "Chart";
    chartKind.textContent = "none";
    return;
  }

  chartTitle.textContent = response.chart.title;
  chartKind.textContent = response.chart.chart_type;
  const xIndex = response.columns.indexOf(response.chart.x);
  const yIndex = response.columns.indexOf(response.chart.y);
  const maxValue = Math.max(...response.rows.map((row) => Number(row[yIndex]) || 0), 1);

  response.rows.slice(0, 8).forEach((row) => {
    const value = Number(row[yIndex]) || 0;
    const line = document.createElement("div");
    line.className = "bar-row";
    line.innerHTML = `
      <span>${row[xIndex]}</span>
      <div class="bar" style="width: ${(value / maxValue) * 100}%"></div>
      <strong>${value.toLocaleString()}</strong>
    `;
    chart.appendChild(line);
  });
}

function renderAnswer(response) {
  summaryTitle.textContent = "Result";
  summaryText.textContent = response.summary;
  queryId.textContent = response.query_id;
  sqlOutput.textContent = response.sql;
  modeValue.textContent = response.used_fallback ? "fallback" : "LLM";
  rowCount.textContent = response.row_count;
  latencyValue.textContent = `${response.latency_ms} ms`;
  renderWarnings(response.warnings || []);
  renderTable(response.columns, response.rows);
  renderChart(response);
}

async function runQuestion(question) {
  summaryTitle.textContent = "Running";
  summaryText.textContent = "Generating SQL and executing against the analytics warehouse...";
  const response = await fetchJson("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, workspace_id: clientConfig.default_workspace_id }),
  });
  renderAnswer(response);
  await refreshMetrics();
}

async function refreshMetrics() {
  const [metrics, history] = await Promise.all([
    fetchJson("/metrics"),
    fetchJson("/history?limit=8"),
  ]);
  metricTotal.textContent = metrics.total_queries;
  metricLatency.textContent = `${metrics.average_latency_ms} ms`;
  metricFallback.textContent = `${Math.round(metrics.fallback_rate * 100)}%`;
  historyList.innerHTML = "";
  history.forEach((item) => {
    const button = document.createElement("button");
    button.className = "history-item";
    button.type = "button";
    button.innerHTML = `${item.question}<span>${item.latency_ms} ms · ${item.row_count} rows</span>`;
    button.addEventListener("click", () => {
      input.value = item.question;
      runQuestion(item.question).catch(showError);
    });
    historyList.appendChild(button);
  });
}

function renderEvals(payload) {
  evalRate.textContent = `${Math.round(payload.pass_rate * 100)}%`;
  evalResults.innerHTML = "";
  payload.results.forEach((result) => {
    const card = document.createElement("div");
    card.className = `eval-card ${result.passed ? "pass" : "fail"}`;
    card.innerHTML = `
      <strong>${result.name}</strong>
      <p>${result.passed ? "passed" : result.failures.join(", ")}</p>
    `;
    evalResults.appendChild(card);
  });
}

function showError(error) {
  summaryTitle.textContent = "Error";
  summaryText.textContent = error.message;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  runQuestion(question).catch(showError);
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.question;
    runQuestion(button.dataset.question).catch(showError);
  });
});

runEvals.addEventListener("click", async () => {
  runEvals.disabled = true;
  runEvals.textContent = "Running";
  try {
    const payload = await fetchJson("/evals/run", { method: "POST" });
    renderEvals(payload);
    await refreshMetrics();
  } catch (error) {
    showError(error);
  } finally {
    runEvals.disabled = false;
    runEvals.textContent = "Run evals";
  }
});

async function boot() {
  clientConfig = await fetchJson("/client-config");
  const health = await fetchJson("/health");
  modeValue.textContent = health.llm_enabled ? "LLM" : "fallback";
  await refreshMetrics();
}

boot().catch(showError);
