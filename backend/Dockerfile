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

# Copy application code
COPY . .

# Run model pre-download if needed
RUN python download_model.py || true

# Set default port (Hugging Face default is 7860, Cloud Run uses 8080 or PORT env var)
ENV PORT=7860
ENV ALLOW_ALL_ORIGINS=true
ENV DISABLE_BERT=true

EXPOSE 7860

CMD ["sh", "-c", "uvicorn bizinsight_api.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
