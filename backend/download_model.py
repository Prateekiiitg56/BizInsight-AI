"""
Build-time model download: run once while building the image / deploy so the
server never has to fetch models on first request.

    python download_model.py
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. VADER lexicon for sentiment scoring (required).
import nltk

nltk_dir = os.getenv("NLTK_DATA", "/tmp/nltk_data")
os.makedirs(nltk_dir, exist_ok=True)
if not nltk.download("vader_lexicon", download_dir=nltk_dir, quiet=True):
    raise SystemExit("Failed to download the VADER lexicon.")
print(f"VADER lexicon saved to {nltk_dir}")

# 2. Fine-tuned complaint embedder for clustering (optional; falls back to all-MiniLM-L6-v2).
MODEL_ID = "Pardhiv17/bizinsight-complaint-embedder"
LOCAL_PATH = os.path.join(BASE_DIR, "models", "finetuned_complaint_model_final")

try:
    from sentence_transformers import SentenceTransformer

    print(f"Downloading clustering model {MODEL_ID}...")
    SentenceTransformer(MODEL_ID).save(LOCAL_PATH)
    print(f"Model saved to {LOCAL_PATH}")
except Exception as e:
    print(f"Warning: clustering model download skipped ({e}). The default embedder will be used.")
