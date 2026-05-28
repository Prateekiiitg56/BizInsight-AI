from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
import re


# ================= CONCESSION PATTERNS =================

CONCESSION_PATTERNS = [
    r'\bbut\b',
    r'\bhowever\b',
    r'\bthough\b',
    r'\byet\b',
    r'\balthough\b',
    r'\beven though\b'
]


# ================= MODELS =================

vader = SentimentIntensityAnalyzer()

bert_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    truncation=True,
    max_length=512
)


# ================= HELPER FUNCTIONS =================

def _vader_score(text: str) -> float:
    """
    Returns a float in [-1, +1].

    VADER compound score interpretation:
      >= 0.05  → positive
      <= -0.05 → negative
      otherwise → neutral
    """

    scores = vader.polarity_scores(text)

    return scores["compound"]


def _normalize_bert_output(result: dict) -> float:
    """
    Convert raw transformer output into normalized score.

    BERT output format:
    {
        "label": "positive" / "negative" / "neutral",
        "score": confidence
    }

    Returns:
        float in [-1, +1]
    """

    label = result["label"].lower()

    score = result["score"]

    if label == "positive":
        return score - 0.1

    elif label == "negative":
        return -score

    return 0.0


def _bert_score(text: str) -> float:
    """
    Run sentiment inference for a single text.
    """

    result = bert_pipeline(text)[0]

    return _normalize_bert_output(result)


def _ensemble_score(vader_s: float, bert_s: float) -> float:
    """
    Weighted ensemble score.
    """

    return (0.3 * vader_s) + (0.7 * bert_s)


def _concession_penalty(text: str) -> float:
    """
    Detect concession-based sentiment reversals.

    Example:
    "The product is good but the support is terrible."

    Negative clause after concession words gets additional penalty.
    """

    text_lower = text.lower()

    for pattern in CONCESSION_PATTERNS:

        match = re.search(pattern, text_lower)

        if match:

            after = text[match.end():].strip()

            if after:

                after_score = _vader_score(after)

                if after_score < 0:

                    return after_score * 0.5

    return 0.0


def _label(score: float) -> str:
    """
    Convert numeric sentiment score into label.
    """

    if score > 0.25:
        return "Positive"

    elif score < -0.25:
        return "Negative"

    return "Neutral"


# ================= SINGLE ANALYSIS =================

def analyze(text: str) -> dict:
    """
    Analyze a single customer review.

    Returns:
        {
            label,
            score,
            vader_score,
            bert_score
        }
    """

    if not text or not str(text).strip():

        return {
            "label": "Neutral",
            "score": 0.0,
            "vader_score": 0.0,
            "bert_score": 0.0,
        }

    text = str(text).strip()

    v = _vader_score(text)

    b = _bert_score(text)

    final = (
        _ensemble_score(v, b)
        + _concession_penalty(text)
    )

    final = max(-1.0, min(1.0, final))

    return {
        "label": _label(final),
        "score": round(final, 4),
        "vader_score": round(v, 4),
        "bert_score": round(b, 4),
    }


# ================= BATCH ANALYSIS =================

def analyze_batch(
    texts: list,
    batch_size: int = 16
) -> list:
    """
    Analyze reviews in batches for significantly faster
    transformer inference throughput.

    Parameters
    ----------
    texts : list[str]
        Customer reviews.

    batch_size : int
        Transformer inference batch size.

    Returns
    -------
    list[dict]
        List of sentiment analysis results.
    """

    if not texts:
        return []

    # ── Preserve Input Alignment ──────────────────────

    cleaned_texts = [
        str(text).strip()
        for text in texts
    ]

    # ── Batch Transformer Inference ───────────────────

    bert_results = bert_pipeline(
        cleaned_texts,
        batch_size=batch_size,
        truncation=True,
        max_length=512
    )

    output = []

    # ── Ensemble Processing ───────────────────────────

    for text, bert_result in zip(
        cleaned_texts,
        bert_results
    ):

        v = _vader_score(text)

        b = _normalize_bert_output(bert_result)

        final = (
            _ensemble_score(v, b)
            + _concession_penalty(text)
        )

        final = max(-1.0, min(1.0, final))

        output.append({
            "label": _label(final),
            "score": round(final, 4),
            "vader_score": round(v, 4),
            "bert_score": round(b, 4),
        })

    return output
