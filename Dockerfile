FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch==2.12.0+cpu --index-url https://download.pytorch.org/whl/cpu

COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY app/ ./app/
COPY data/ ./data/

EXPOSE 8000

CMD uvicorn app.api.main:app --host 0.0.0.0 --port ${PORT:-8000}