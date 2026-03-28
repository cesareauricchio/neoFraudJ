FROM python:3.12-slim

WORKDIR /app

COPY ingestion-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Shared Pydantic models (no pip package — resolved via PYTHONPATH)
COPY shared/ /app/shared/

# Service source
COPY ingestion-service/app/ /app/app/

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
