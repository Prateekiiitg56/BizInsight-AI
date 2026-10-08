"""
Vectorize Module
Converts cleaned text reviews into numerical embeddings using Sentence Transformers.
"""

import os
import threading
from typing import Any, List, Optional

import numpy as np

_DEFAULT_FINE_TUNED_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "finetuned_complaint_model_final"
)

_models: dict = {}
_lock = threading.Lock()


def load_model(model_name: str = "all-MiniLM-L6-v2", fine_tuned_path: str = _DEFAULT_FINE_TUNED_PATH):
    """Load (and cache) a sentence transformer, preferring the fine-tuned model when present."""
    model_to_load = fine_tuned_path if os.path.exists(fine_tuned_path) else model_name
    with _lock:
        if model_to_load not in _models:
            from sentence_transformers import SentenceTransformer
            _models[model_to_load] = SentenceTransformer(model_to_load)
        return _models[model_to_load]


def get_embeddings(reviews: List[str], model: Optional[Any] = None) -> np.ndarray:
    """Convert a list of reviews to vector embeddings."""
    if model is None:
        model = load_model()
    return model.encode(reviews, show_progress_bar=False)
