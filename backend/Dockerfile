FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache \
    FASTEMBED_CACHE_PATH=/app/.cache/fastembed \
    NLTK_DATA=/app/nltk_data \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Pre-download model weights so the container never fetches them at request time.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')" \
    && python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY . .
RUN python download_model.py

# Run as an unprivileged user (uid 1000 also satisfies Hugging Face Spaces).
RUN useradd --uid 1000 --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import urllib.request,os; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8080\")}/api/health')" || exit 1

CMD ["sh", "-c", "uvicorn bizinsight_api.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers"]
