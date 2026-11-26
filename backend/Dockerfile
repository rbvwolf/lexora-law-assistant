# Build from the repository root:  docker build -f backend/Dockerfile -t lexora-backend .
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface

# OS-level C libraries for WeasyPrint (listed in requirements.txt)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
# CPU-only torch first: the default Linux wheel pulls several GB of CUDA libraries the server never uses
RUN pip install --index-url https://download.pytorch.org/whl/cpu torch \
    && pip install -r requirements.txt

# Non-root runtime user. It is created before the index is built so the model cache and index are
# written with the right owner directly (a later chown -R would copy ~1 GB into a second layer).
RUN useradd --create-home --uid 1000 lexora \
    && mkdir -p /app/storage/temp /app/chroma_db /app/.cache \
    && chown lexora:lexora /app /app/storage /app/storage/temp /app/chroma_db /app/.cache

COPY backend/app /app/app
COPY backend/scripts /app/scripts
COPY data/templates /app/data/templates
COPY data/fonts /app/data/fonts
COPY data/laws /app/data/laws

ENV TEMPLATES_DIR=/app/data/templates \
    FONTS_DIR=/app/data/fonts \
    CHROMA_PERSIST_DIR=/app/chroma_db

USER lexora

# The vector index is built into the image: the server never starts with an empty collection, and
# the embedding model is downloaded once here instead of on the first request. The runtime
# EMBEDDING_MODEL_NAME must match the model the index was built with.
ARG EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-base
ENV EMBEDDING_MODEL_NAME=${EMBEDDING_MODEL_NAME}
RUN python scripts/ingest_laws.py --data-dir /app/data/laws --persist-dir /app/chroma_db --reset

# The model is in the image now: never call the Hugging Face Hub at runtime (no network dependency
# on startup, no HF rate limits)
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

EXPOSE 8000

# Render and Railway pass the port in $PORT; one worker keeps a single embedding model in memory
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
