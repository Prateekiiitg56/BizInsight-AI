from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
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


vader = SentimentIntensityAnalyzer()



bert_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    truncation=True,
    max_length=512
)

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


def _bert_score(text: str) -> float:
    """
    Returns a float in [-1, +1].
    BERT returns {"label": "POSITIVE"/"NEGATIVE", "score": 0..1}
    We convert:
      POSITIVE → +score
      NEGATIVE → -score
    """
    result = bert_pipeline(text)[0]
    label = result["label"].lower()
    score = result["score"]          # confidence: 0.0 to 1.0
    if label == "positive":
        return score  -0.1               # e.g. +0.97
    elif label == "negative":
        return -score
    else:
        return 0.0

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
    Analyze a list of reviews. More efficient than calling analyze() in a loop
    because BERT processes batches faster on GPU.
 
    Parameters
    ----------
    texts : list of str
 
    Returns
    -------
    list of dicts (same structure as analyze())
    """
    # Batch BERT inference
    bert_results = bert_pipeline(texts, batch_size=16, truncation=True, max_length=512)
 
    output = []
    for text, bert_result in zip(texts, bert_results):
        v = _vader_score(text)
        # ✅ consistent with _bert_score
        label = bert_result["label"].lower()
        b = bert_result["score"] if label == "positive" else (-bert_result["score"] if label == "negative" else 0.0)
        final = _ensemble_score(v, b) + _concession_penalty(text)
        final = max(-1.0, min(1.0, final))
        output.append({
            "label":       _label(final),
            "score":       round(final, 4),
            "vader_score": round(v, 4),
            "bert_score":  round(b, 4),
        })
 
    return output