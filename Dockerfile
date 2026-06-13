# ── Base image: lightweight Python ────────────────────────────────────────
FROM python:3.11-slim

# ── Set working directory inside the container ────────────────────────────
WORKDIR /app

# ── Install system dependencies needed by some Python packages ────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── Copy requirements first (Docker caches this layer if unchanged) ───────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy the rest of the project code ──────────────────────────────────────
COPY app/ ./app/
COPY data/ ./data/

# ── Expose the port FastAPI runs on ─────────────────────────────────────────
EXPOSE 8000

# ── Command to run when container starts ────────────────────────────────────
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]