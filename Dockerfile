FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python packages
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application code into WORKDIR
COPY backend/ .

# Run model pre-download if needed
RUN python download_model.py || true

# Set default port (Google Cloud Run passes PORT=8080)
ENV PORT=8080
ENV ALLOW_ALL_ORIGINS=true
ENV DISABLE_BERT=true

EXPOSE 8080

CMD ["sh", "-c", "uvicorn bizinsight_api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
