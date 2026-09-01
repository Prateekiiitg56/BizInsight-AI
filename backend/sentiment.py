import os
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
import re

CONCESSION_PATTERNS = [
    r'\bbut\b', r'\bhowever\b', r'\bthough\b', 
    r'\byet\b', r'\balthough\b', r'\beven though\b'
]

def _concession_penalty(text: str) -> float:
    """
    If a concession word is found, check if the part after it
    is negative — if so, apply a dampening penalty.
    """
    text_lower = text.lower()
    for pattern in CONCESSION_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            after = text[match.end():].strip()
            if after:
                after_score = _vader_score(after)
                if after_score < 0:
                    return after_score * 0.5  # penalty for negative clause after concession
    return 0.0
nltk_dir = os.getenv("NLTK_DATA", "/tmp/nltk_data")
os.makedirs(nltk_dir, exist_ok=True)
if nltk_dir not in nltk.data.path:
    nltk.data.path.append(nltk_dir)

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", download_dir=nltk_dir, quiet=True)

vader = SentimentIntensityAnalyzer()

bert_pipeline = None

def _get_bert_pipeline():
    global bert_pipeline
    if bert_pipeline is None:
        from transformers import pipeline
        bert_pipeline = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            truncation=True,
            max_length=512
        )
    return bert_pipeline

def _vader_score(text: str) -> float:
    """
    Returns a float in [-1, +1].
    VADER's compound score:
      >= 0.05  → positive signal
      <= -0.05 → negative signal
      in between → neutral
    """
    scores = vader.polarity_scores(text)
    return scores["compound"]

def _convert_bert_prediction(label: str, score: float) -> float:
    """
    Convert model output into a normalized sentiment score.
    Keeps single-review and batch-review paths consistent.
    """
    label = label.lower()

    if label == "positive":
        return score - 0.1

    if label == "negative":
        return -score

    return 0.0
def _bert_score(text: str) -> float:
    """
    Returns a float in [-1, +1].
    Uses RoBERTa model if available, falling back safely to VADER under low-memory environments.
    """
    if os.getenv("DISABLE_BERT", "true").lower() == "true":
        return _vader_score(text)

    try:
        result = _get_bert_pipeline()(text)[0]
        label = result["label"].lower()
        score = result["score"]
        return _convert_bert_prediction(label, score)
    except Exception as e:
        logger.warning(f"BERT model skipped ({e}). Using VADER fallback.")
        return _vader_score(text)

def _ensemble_score(vader_s: float, bert_s: float) -> float:
    
    return 0.3 * vader_s + 0.7 * bert_s

def _label(score: float) -> str:
    """
    Map final score to a human-readable label.
    Thresholds calibrated for business review data:
      > 0.25  → Positive  (clear positive sentiment)
      < -0.25 → Negative  (clear negative sentiment)
      else    → Neutral   (mixed or ambiguous)
    """
    if score > 0.25:
        return "Positive"
    elif score < -0.25:
        return "Negative"
    else:
        return "Neutral"
    
def analyze(text: str) -> dict:
    """
    Main function — call this from app.py.
 
    Parameters
    ----------
    text : str
        A single customer review string.
 
    Returns
    -------
    dict with keys:
        label       → "Positive" / "Neutral" / "Negative"
        score       → float in [-1, +1]  (final ensemble score)
        vader_score → float in [-1, +1]  (raw VADER score)
        bert_score  → float in [-1, +1]  (raw BERT score)
 
    Example
    -------
    >>> result = analyze("The product is okay but shipping was terrible.")
    >>> result["label"]
    'Negative'
    """
    v = _vader_score(text)
    b = _bert_score(text)
    final = _ensemble_score(v, b) + _concession_penalty(text)
    final = max(-1.0, min(1.0, final))
 
    return {
        "label":       _label(final),
        "score":       round(final, 4),
        "vader_score": round(v, 4),
        "bert_score":  round(b, 4),
    }
 
 
def analyze_batch(texts: list) -> list:
    """
    Analyze a list of reviews using VADER + RoBERTa ensemble with automatic low-memory fallback.
    """
    if os.getenv("DISABLE_BERT", "true").lower() == "true":
        return [analyze(text) for text in texts]

    try:
        bert_results = _get_bert_pipeline()(texts, batch_size=16, truncation=True, max_length=512)
        output = []
        for text, bert_result in zip(texts, bert_results):
            v = _vader_score(text)
            label = bert_result["label"]
            b = _convert_bert_prediction(label, bert_result["score"])
            final = _ensemble_score(v, b) + _concession_penalty(text)
            final = max(-1.0, min(1.0, final))
            output.append({
                "label":       _label(final),
                "score":       round(final, 4),
                "vader_score": round(v, 4),
                "bert_score":  round(b, 4),
            })
        return output
    except Exception as e:
        logger.warning(f"Batch BERT inference skipped ({e}); using VADER.")
        return [analyze(text) for text in texts]
