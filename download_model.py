from sentence_transformers import SentenceTransformer
import os

MODEL_ID = "Pardhiv17/bizinsight-complaint-embedder"
LOCAL_PATH = "models/finetuned_complaint_model_final"

print(f"Downloading model from {MODEL_ID}...")
model = SentenceTransformer(MODEL_ID)
os.makedirs(LOCAL_PATH, exist_ok=True)
model.save(LOCAL_PATH)
print(f"Model saved to {LOCAL_PATH}")