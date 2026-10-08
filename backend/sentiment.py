"""
VADER sentiment scoring shared by the upload route and the demo dataset loader.
"""

import os

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

_nltk_dir = os.getenv("NLTK_DATA", "/tmp/nltk_data")
os.makedirs(_nltk_dir, exist_ok=True)
if _nltk_dir not in nltk.data.path:
    nltk.data.path.append(_nltk_dir)

try:
    nltk.data.find("sentiment/vader_lexicon.zip")
except LookupError:
    nltk.download("vader_lexicon", download_dir=_nltk_dir, quiet=True)

_analyzer = SentimentIntensityAnalyzer()


def get_sentiment(text: str) -> float:
    """VADER compound score in [-1, 1]."""
    return _analyzer.polarity_scores(text)["compound"]
