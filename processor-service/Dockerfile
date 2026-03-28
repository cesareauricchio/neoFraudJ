FROM python:3.12-slim

WORKDIR /app

COPY processor-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Shared Pydantic models (no pip package — resolved via PYTHONPATH)
COPY shared/ /app/shared/

# Service source
COPY processor-service/app/ /app/app/

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.main"]
