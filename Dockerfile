FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_sql_analyst ./ai_sql_analyst
COPY evals.py ./evals.py
COPY manage.py ./manage.py

EXPOSE 8000

CMD ["uvicorn", "ai_sql_analyst.main:app", "--host", "0.0.0.0", "--port", "8000"]
