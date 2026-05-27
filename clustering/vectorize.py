"""
Vectorize Module
Converts cleaned text reviews into numerical embeddings using Sentence Transformers
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional
import streamlit as st
import os

# Global variable to cache the model (load once)
_model = None
_current_model_name = None

@st.cache_resource
def load_model(model_name: str = "all-mpnet-base-v2", fine_tuned_path: str = "models/finetuned_complaint_model_final"):
    """
    Load sentence transformer model.
    If fine-tuned model exists at fine_tuned_path, use it; otherwise fallback to model_name.
    """
    global _model, _current_model_name
    
    # Check if fine-tuned model exists
    if os.path.exists(fine_tuned_path):
        model_to_load = fine_tuned_path
        display_name = "fine-tuned model"
        st.success(f"✅ Loaded fine-tuned model")
    else:
        model_to_load = model_name
        display_name = model_name
        st.info(f"Using default model ({model_name}) - fine-tuned model not found")
    
    # Only reload if model changed
    if _model is None or _current_model_name != model_to_load:
        with st.spinner(f"Loading {display_name} (first time only)..."):
            _model = SentenceTransformer(model_to_load)
            _current_model_name = model_to_load
    
    return _model

def get_embeddings(reviews: List[str], model: Optional[SentenceTransformer] = None) -> np.ndarray:
    """
    Convert list of reviews to vector embeddings.
    """
    if model is None:
        model = load_model()
    
    progress_bar = st.progress(0)
    embeddings = model.encode(reviews, show_progress_bar=False)
    progress_bar.progress(100)
    
    return embeddings