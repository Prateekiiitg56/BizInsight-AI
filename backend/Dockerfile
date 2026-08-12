FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENV HF_HOME=/app/.cache
ENV FASTEMBED_CACHE_PATH=/app/.cache/fastembed

# Pre-download fastembed ONNX model weights and cross-encoder reranker weights into /app/.cache
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5')"
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Copy application code
COPY . .

# Set default port (Google Cloud Run passes PORT=8080)
ENV PORT=8080
ENV ALLOW_ALL_ORIGINS=true
ENV DISABLE_BERT=true

EXPOSE 8080

CMD ["sh", "-c", "uvicorn bizinsight_api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
