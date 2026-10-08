def test_clustering_module_imports_without_heavy_deps():
    # Regression: type hints referenced an un-imported SentenceTransformer, crashing every job.
    from clustering.run_clustering import make_unique_business_name, merge_duplicate_clusters

    assert make_unique_business_name([]) == "Other Issues"
    merged = merge_duplicate_clusters([
        {"name": "A", "count": 2, "example_reviews": ["x"], "sample_review": "x"},
        {"name": "A", "count": 3, "example_reviews": ["y"], "sample_review": "y"},
    ])
    assert merged[0]["count"] == 5


def test_verify_password_handles_non_bcrypt_hash():
    from database import verify_password

    assert verify_password("x", "GOOGLE_OAUTH_USER") is False


def test_sentiment_router_and_tenant_filter():
    from rag_api.api import sentiment_filter_for
    from rag_api.vector_store import build_where

    assert sentiment_filter_for("What are the main complaints?") == {"sentiment": {"$lt": 0}}
    assert sentiment_filter_for("What do customers love?") == {"sentiment": {"$gt": 0}}
    assert sentiment_filter_for("Summarize good and bad points") is None
    assert build_where(7) == {"user_id": 7}
    assert build_where(7, {"sentiment": {"$lt": 0}}) == {"$and": [{"user_id": 7}, {"sentiment": {"$lt": 0}}]}


def test_hashing_embedding_fallback_is_deterministic():
    from sklearn.feature_extraction.text import HashingVectorizer

    vec = HashingVectorizer(n_features=384, alternate_sign=False, norm="l2", ngram_range=(1, 2))
    a = vec.transform(["late delivery"]).toarray()
    b = vec.transform(["late delivery"]).toarray()
    assert (a == b).all()
