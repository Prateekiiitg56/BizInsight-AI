"""
test_sentiment_accuracy.py — Accuracy Evaluation for Ensemble Sentiment Analyzer
==================================================================================
Tests the VADER + BERT ensemble against:
  1. A hand-labeled dataset of tricky reviews
  2. Accuracy, Precision, Recall, F1 per class
  3. Confusion matrix
  4. Comparison against old TextBlob baseline

Run with:
    python test_sentiment_accuracy.py
"""

import time
from sentiment import analyze, analyze_batch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")  # non-interactive backend (no display needed)

# ─────────────────────────────────────────────────────────────────────────────
# LABELED TEST DATASET
# 60 reviews hand-labeled as Positive / Neutral / Negative
# Includes tricky cases: sarcasm, negation, mixed sentiment, short reviews
# ─────────────────────────────────────────────────────────────────────────────
TEST_DATA = [
    # ── Clear Positives ───────────────────────────────────────────────────────
    ("Absolutely love this product! Best purchase I've made all year.",          "Positive"),
    ("Great quality, fast shipping, will definitely order again.",               "Positive"),
    ("The customer service team was incredibly helpful and friendly.",           "Positive"),
    ("Works perfectly, exactly as described. Very happy!",                       "Positive"),
    ("Outstanding experience from start to finish.",                             "Positive"),
    ("Five stars! Exceeded all my expectations.",                                "Positive"),
    ("Really impressed with the build quality and design.",                      "Positive"),
    ("My kids absolutely love it. Worth every penny.",                           "Positive"),
    ("Smooth checkout, arrived early, great packaging.",                         "Positive"),
    ("Honestly the best app I've used in years.",                                "Positive"),

    # ── Tricky Positives (sarcasm-free but understated) ───────────────────────
    ("Not bad at all, actually quite good.",                                     "Positive"),  # negation
    ("I was skeptical at first but it works great.",                             "Positive"),  # doubt → positive
    ("Surprisingly good for the price.",                                         "Positive"),
    ("Does exactly what it says on the tin.",                                    "Positive"),
    ("Better than I expected honestly.",                                         "Positive"),

    # ── Clear Negatives ───────────────────────────────────────────────────────
    ("Terrible quality. Broke after 2 days. Complete waste of money.",           "Negative"),
    ("Worst customer service I have ever experienced. Absolutely appalling.",    "Negative"),
    ("Product arrived damaged and support never responded.",                     "Negative"),
    ("Total scam. Do not buy this.",                                             "Negative"),
    ("Horrible experience. Will never shop here again.",                         "Negative"),
    ("The app crashes every time I open it. Useless.",                           "Negative"),
    ("Took 3 weeks to arrive and it was the wrong item.",                        "Negative"),
    ("Instructions were impossible to follow and the product doesn't work.",     "Negative"),
    ("Cheap plastic, nothing like the photos. Very disappointed.",               "Negative"),
    ("Rude staff, long wait, and overpriced food.",                              "Negative"),

    # ── Tricky Negatives (sarcasm, backhanded) ───────────────────────────────
    ("Oh wow, another product that breaks in a week. Shocking.",                 "Negative"),  # sarcasm
    ("Yeah great, waited 3 weeks for a broken item. Really fantastic.",          "Negative"),  # sarcasm
    ("The packaging was nice I guess, too bad the product is garbage.",          "Negative"),  # mixed → negative
    ("Started off great but completely fell apart after a month.",               "Negative"),  # time-based
    ("Not the worst I've seen but still pretty bad.",                            "Negative"),  # understatement

    # ── Clear Neutrals ────────────────────────────────────────────────────────
    ("It arrived on time.",                                                      "Neutral"),
    ("The product is okay.",                                                     "Neutral"),
    ("Does what it's supposed to do, nothing more.",                             "Neutral"),
    ("Average quality for the price.",                                           "Neutral"),
    ("It's fine.",                                                               "Neutral"),
    ("Neither impressed nor disappointed.",                                      "Neutral"),
    ("Shipping was normal speed.",                                               "Neutral"),
    ("The instructions were clear enough.",                                      "Neutral"),
    ("It works.",                                                                "Neutral"),
    ("Received the item as described.",                                          "Neutral"),

    # ── Tricky Neutrals (mixed sentiment) ─────────────────────────────────────
    ("Great product but terrible shipping.",                                     "Neutral"),   # mixed
    ("Love the design, hate the price.",                                         "Neutral"),   # mixed
    ("Fast delivery but the quality could be better.",                           "Neutral"),   # mixed
    ("Some features are great, others are disappointing.",                       "Neutral"),   # mixed
    ("Good for the price but don't expect premium quality.",                     "Neutral"),   # qualified

    # ── Edge Cases ────────────────────────────────────────────────────────────
    ("ok",                                                                       "Neutral"),   # very short
    ("WORST PRODUCT EVER!!!",                                                    "Negative"),  # all caps
    ("best. purchase. ever.",                                                    "Positive"),  # punctuation style
    ("meh",                                                                      "Neutral"),   # slang
    ("10/10 would recommend",                                                    "Positive"),  # numeric rating
    ("0/10 do not recommend",                                                    "Negative"),  # numeric rating
    ("It is what it is.",                                                        "Neutral"),
    ("Could be worse I suppose.",                                                "Neutral"),
    ("Not worth the hype but not terrible either.",                              "Neutral"),
    ("I've had better, I've had worse.",                                         "Neutral"),
]

# ─────────────────────────────────────────────────────────────────────────────
# TEXTBLOB BASELINE (for comparison)
# ─────────────────────────────────────────────────────────────────────────────
def textblob_predict(texts):
    """Run TextBlob on same test set for comparison."""
    try:
        from textblob import TextBlob
        predictions = []
        for text in texts:
            polarity = TextBlob(text).sentiment.polarity
            if polarity > 0.05:
                predictions.append("Positive")
            elif polarity < -0.05:
                predictions.append("Negative")
            else:
                predictions.append("Neutral")
        return predictions
    except ImportError:
        print("  TextBlob not installed — skipping baseline comparison.")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
def evaluate():
    texts      = [item[0] for item in TEST_DATA]
    true_labels = [item[1] for item in TEST_DATA]

    print("=" * 65)
    print("  SENTIMENT ENSEMBLE — ACCURACY EVALUATION")
    print("=" * 65)
    print(f"  Test set size: {len(texts)} reviews\n")

    # ── Run ensemble ──────────────────────────────────────────────────────────
    print("  Running VADER + BERT ensemble...")
    t0 = time.time()
    results = analyze_batch(texts)
    elapsed = time.time() - t0

    ensemble_preds = [r["label"] for r in results]
    ensemble_scores = [r["score"] for r in results]

    # ── Metrics ───────────────────────────────────────────────────────────────
    acc = accuracy_score(true_labels, ensemble_preds)

    print(f"\n  ✅ Ensemble Accuracy:  {acc * 100:.1f}%")
    print(f"  ⏱  Inference time:    {elapsed:.2f}s for {len(texts)} reviews")
    print(f"     ({elapsed/len(texts)*1000:.0f}ms per review)\n")

    print("  Per-class metrics:")
    print("  " + "-" * 50)
    report = classification_report(
        true_labels, ensemble_preds,
        target_names=["Negative", "Neutral", "Positive"],
        digits=3
    )
    # Indent report lines
    for line in report.split("\n"):
        print("  " + line)

    # ── Confusion matrix ──────────────────────────────────────────────────────
    cm = confusion_matrix(true_labels, ensemble_preds, labels=["Positive", "Neutral", "Negative"])
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=["Positive", "Neutral", "Negative"])

    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, colorbar=False, cmap="Blues")
    ax.set_title("Ensemble Model — Confusion Matrix", fontsize=13, pad=12)
    plt.tight_layout()
    plt.savefig("confusion_matrix_ensemble.png", dpi=150)
    print("\n  📊 Confusion matrix saved → confusion_matrix_ensemble.png")

    # ── TextBlob baseline comparison ──────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  TEXTBLOB BASELINE COMPARISON")
    print("=" * 65)

    tb_preds = textblob_predict(texts)
    if tb_preds:
        tb_acc = accuracy_score(true_labels, tb_preds)
        print(f"\n  TextBlob Accuracy:  {tb_acc * 100:.1f}%")
        print(f"  Ensemble Accuracy:  {acc * 100:.1f}%")
        improvement = (acc - tb_acc) * 100
        symbol = "✅ +" if improvement >= 0 else "❌ "
        print(f"  Improvement:        {symbol}{improvement:.1f}%\n")

    # ── Per-review breakdown (failures) ───────────────────────────────────────
    print("=" * 65)
    print("  MISCLASSIFIED REVIEWS")
    print("=" * 65)
    misses = [
        (texts[i], true_labels[i], ensemble_preds[i], ensemble_scores[i])
        for i in range(len(texts))
        if true_labels[i] != ensemble_preds[i]
    ]
    if not misses:
        print("  🎉 No misclassifications!")
    else:
        for review, true, pred, score in misses:
            print(f"\n  Review : {review[:70]}...")
            print(f"  True   : {true}")
            print(f"  Pred   : {pred}  (score: {score:+.3f})")

    print("\n" + "=" * 65)
    print(f"  Done. {len(misses)} misclassified out of {len(texts)} reviews.")
    print("=" * 65)


if __name__ == "__main__":
    evaluate()