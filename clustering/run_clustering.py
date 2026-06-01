"""
Run Clustering Module - BERTopic with embedding-based category mapping
"""

import numpy as np
from typing import List, Dict, Optional
from bertopic import BERTopic
import hdbscan
from sentence_transformers import SentenceTransformer
from sklearn.metrics import silhouette_score
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
from umap import UMAP

from clustering.preprocess import preprocess_reviews
from clustering.vectorize import load_model


# Standard categories with sentences (used for mapping)
CATEGORY_EXAMPLES = {
    "Payment": "charge billing invoice overcharged duplicate refund payment gateway",
    "Account": "login password access account verification recovery authentication",
    "Delivery": "delivery shipping courier tracking package delay order not arrived",
    "Technical": "crash error timeout freeze bug server app technical failure",
    "Product Quality": "broke defective quality poor build cheap damaged",
    "Customer Service": "rude unhelpful support agent chat refused refund",
    "Wrong Item": "wrong item incorrect missing part not as described size wrong",
    "Shipping Damage": "box crushed broken during shipping arrived damaged",
    "Subscription": "subscription cancel renew auto-renew membership charged after cancel",
    "Checkout": "checkout cart ssl error couldn't complete purchase",
    "Return/Refund": "return refund money back reimbursement credit not received"
}

def make_unique_business_name(examples: List[str]) -> str:
    """
    Generate a short business name directly from the example reviews.
    """
    if not examples:
        return "Other Issues"
    
    # Create a single text blob and extract top words (excluding stopwords)
    text = " ".join(examples).lower()
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'so', 'for', 'nor', 'yet', 
                 'of', 'to', 'in', 'on', 'at', 'with', 'without', 'by', 'about',
                 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
                 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
                 'this', 'that', 'these', 'those', 'some', 'any', 'no', 'very', 'too', 'just', 'but', 'can', 'will',
                 'not', 'so', 'get', 'got', 'go', 'went', 'come', 'came', 'see', 'saw', 'look', 'use', 'used', 'using'}
    
    # Extract words longer than 2 characters and not in stopwords
    words = [w for w in text.split() if len(w) > 2 and w not in stopwords]

    # If no valid words, fallback to first two words of first example
    if not words:
        fallback = examples[0].split()[:2]
        if fallback:
            return " ".join(fallback).title() + " Issue"
        return "Other Issues"
    
    # Get the most common words and create a base name
    word_counts = Counter(words)
    top_words = [w for w, _ in word_counts.most_common(2)]
    base = " ".join(top_words).title()
    
    # Add suffix based on base name keywords
    if any(kw in base.lower() for kw in ['delay', 'shipping', 'delivery', 'tracking', 'courier']):
        suffix = " Delay"
    elif any(kw in base.lower() for kw in ['error', 'crash', 'freeze', 'timeout', 'bug']):
        suffix = " Error"
    elif any(kw in base.lower() for kw in ['charge', 'billing', 'payment', 'invoice', 'refund']):
        suffix = " Issues"
    elif any(kw in base.lower() for kw in ['login', 'password', 'account', 'access']):
        suffix = " Issues"
    else:
        suffix = " Issues"

    # Ensure we don't end up with redundant names like "Payment Issues Issues"
    if not base.endswith(("Issues", "Error", "Delay")):
        base += suffix
    
    # Remove duplicate consecutive words 
    words_final = base.split()
    deduped = []
    for w in words_final:
        if not deduped or w != deduped[-1]:
            deduped.append(w)
    return " ".join(deduped)

def map_cluster_to_category(
    cluster_examples: List[str],
    embedding_model: SentenceTransformer,
    similarity_threshold: float = 0.7
) -> Optional[str]:
    """
    Map a cluster (using its example reviews) to one of the standard categories
    based on cosine similarity with category description sentences.
    Returns category name if similarity >= threshold, else None.
    """
    if not cluster_examples or embedding_model is None:
        return None
    
    # Encode the cluster's representative text (first example)
    cluster_embedding = embedding_model.encode([cluster_examples[0]])[0]
    
    # Pre-compute category embeddings (cache if needed)
    if not hasattr(map_cluster_to_category, "_category_embeddings"):
        map_cluster_to_category._category_embeddings = {}
        for cat, sentence in CATEGORY_EXAMPLES.items():
            map_cluster_to_category._category_embeddings[cat] = embedding_model.encode([sentence])[0]
    
    # Find the category with highest similarity
    best_cat = None
    best_sim = -1.0
    for cat, cat_emb in map_cluster_to_category._category_embeddings.items():
        sim = cosine_similarity([cluster_embedding], [cat_emb])[0][0]
        if sim > best_sim:
            best_sim = sim
            best_cat = cat
    
    if best_sim >= similarity_threshold:
        return best_cat
    return None

def merge_duplicate_clusters(clusters: List[Dict]) -> List[Dict]:
    """Merge clusters with identical names."""
    merged = {}
    for c in clusters:
        name = c["name"]
        if name not in merged:
            merged[name] = {
                "name": name,
                "count": 0,
                "examples": [],
                "sample_review": c["sample_review"],
            }
        merged[name]["count"] += c["count"]
        merged[name]["examples"].extend(c["example_reviews"][:2])
    
    result = []
    for name, data in merged.items():
        result.append({
            "id": hash(name) % 10000,
            "name": name,
            "count": data["count"],
            "percentage": 0.0,
            "example_reviews": data["examples"][:3],
            "sample_review": data["sample_review"],
        })
    return result

def run_pipeline(
    reviews: List[str],
    embedding_model: Optional[SentenceTransformer] = None,
    min_topic_size: int = 10, # minimum number of reviews per cluster
    similarity_threshold: float = 0.4, # lower threshold for category mapping to allow more clusters to be categorized, can be tuned based on dataset
    verbose: bool = True 
) -> Dict:
    """
    Main clustering pipeline using BERTopic, then maps clusters to standard categories
    using embedding similarity.
    """
    if len(reviews) < 10: # require at least 10 reviews for meaningful clustering
        return {
            "success": False,
            "message": f"Only {len(reviews)} reviews. Need at least 10.",
            "clusters": [],
            "total_reviews": len(reviews),
            "n_topics": 0,
            "silhouette_score": None,
            "noise_count": len(reviews),
            "noise_percentage": 100.0
        }

    # 1. Preprocess
    cleaned_reviews = preprocess_reviews(reviews)
    
    if len(cleaned_reviews) < 10: # Check if enough reviews remain after cleaning
        return {
            "success": False,
            "message": f"After cleaning, only {len(cleaned_reviews)} reviews left. Need at least 10.",
            "clusters": [],
            "total_reviews": len(reviews),
            "n_topics": 0,
            "silhouette_score": None,
            "noise_count": len(reviews),
            "noise_percentage": 100.0
        }

    # 2. Load embedding model
    if embedding_model is None:
        embedding_model = load_model()
    
    # BerTopic with custom vectorizer and tuned parameters for better performance on small datasets
    vectorizer_model = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 2), # unigrams and bigrams for better topic representation, can be tuned based on dataset size and diversity
        max_df=0.8, # ignore words that appear in more than 80% of documents to focus on more distinctive terms, can be tuned based on dataset size and diversity
        min_df=1 # include words that appear in at least 1 document, can be increased for larger datasets to reduce noise
    )
    
    umap_model = UMAP(
        n_neighbors=15, # default is 15, can be tuned based on dataset size (smaller for smaller datasets to capture finer structure, larger for bigger datasets to capture broader structure)
        n_components=5, # reduce to 5 dimensions for better clustering performance (instead of 2D which is only for visualization), can be tuned based on dataset size and complexity
        min_dist=0.0, # set to 0 to allow tighter clusters, can be increased for larger datasets to allow more spread out clusters
        metric='cosine', # cosine distance is often better for text embeddings, can be changed to 'euclidean' if using non-normalized embeddings or if it performs better on the specific dataset
        random_state=42 # fixed random state for reproducibility
    )

    hdbscan_model = hdbscan.HDBSCAN(
        min_cluster_size=min_topic_size, # minimum cluster size, can be tuned based on dataset size (smaller for smaller datasets to find more clusters, larger for bigger datasets to find more robust clusters)
        min_samples=3, # minimum samples in a cluster, can be tuned based on dataset size (smaller for smaller datasets to allow more clusters, larger for bigger datasets to reduce noise)
        cluster_selection_epsilon=0.2, # increase epsilon to allow merging of nearby clusters, can be tuned based on dataset size and diversity 
        metric='euclidean', # HDBSCAN works best with euclidean distance on UMAP-reduced embeddings, can be changed to 'cosine' if using non-UMAP embeddings or if it performs better on the specific dataset
        prediction_data=True # enable prediction data for silhouette score calculation, can be set to False if silhouette score is not needed or if it causes performance issues on larger datasets
    )

    # 3. Create and fit BERTopic model for clustering and topic extraction
    topic_model = BERTopic(
        embedding_model=embedding_model, 
        min_topic_size=min_topic_size, 
        umap_model=umap_model,        
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        verbose=verbose,
        calculate_probabilities=True
    )
    
    # Fit the model and get topics
    topics, probs = topic_model.fit_transform(cleaned_reviews)
    
    # 4. Get topic info
    topic_info = topic_model.get_topic_info()
    valid_topics = topic_info[topic_info.Topic != -1] # filter out noise topic (-1)
    n_topics = len(valid_topics) 
    total_reviews = len(cleaned_reviews)
    noise_count = topic_info[topic_info.Topic == -1]['Count'].values[0] if -1 in topic_info.Topic.values else 0 # count of noise reviews
    noise_percentage = (noise_count / total_reviews) * 100 if total_reviews > 0 else 0 # percentage of noise reviews
    
    # 5. Prepare clusters and map to standard categories
    clusters = []
    for _, row in valid_topics.iterrows(): # iterate only over valid topics (exclude noise)
        topic_id = row['Topic']
        size = row['Count']
        
        # Get representative reviews for the topic (fallback to first few reviews in the cluster if get_representative_docs is not available)
        try:
            representative_docs = topic_model.get_representative_docs(topic_id)
            examples = representative_docs[:3] if representative_docs else []
        except AttributeError:
            indices = [i for i, t in enumerate(topics) if t == topic_id]
            examples = [cleaned_reviews[i] for i in indices[:3]]
        
        # Generate original business name from examples (fallback to generic name if examples are not available)
        original_name = make_unique_business_name(examples)
        
        # Map to standard category using embedding similarity
        mapped_cat = map_cluster_to_category(examples, embedding_model, similarity_threshold)
        
        # If mapped to a standard category, use that name; otherwise use the original generated name
        if mapped_cat:
            cluster_name = f"{mapped_cat} Issues"
        else:
            cluster_name = original_name
        
        # Add cluster info to the list
        clusters.append({
            "id": int(topic_id),
            "name": cluster_name,
            "count": size,
            "percentage": (size / total_reviews) * 100,
            "example_reviews": examples,
            "sample_review": examples[0] if examples else "No sample",
        })
    
    # Merge duplicate names (e.g., two clusters both mapped to "Payment Issues")
    clusters = merge_duplicate_clusters(clusters)
    for c in clusters: # recalculate percentage after merging
        c["percentage"] = (c["count"] / total_reviews) * 100
    clusters.sort(key=lambda x: x["count"], reverse=True) # sort clusters by count after merging (largest first)
    n_topics = len(clusters)
    
    # 6. Silhouette score (only if we have enough clusters and noise is not overwhelming, otherwise it may not be meaningful)
    # Use this to see silhouette score on UMAP-reduced embeddings of non-noise reviews while testing different parameters
    # try:
    #     reduced_embeddings = topic_model.umap_model.embedding_ if hasattr(topic_model, 'umap_model') else None
    #     if reduced_embeddings is not None and n_topics >= 2: # silhouette score requires at least 2 clusters and meaningful embeddings
    #         non_noise_mask = np.array(topics) != -1 # only consider non-noise reviews for silhouette score
    #         if np.sum(non_noise_mask) > n_topics: # need more non-noise reviews than clusters for silhouette score to be meaningful
    #             sil_score = silhouette_score( # calculate silhouette score on UMAP-reduced embeddings of non-noise reviews
    #                 reduced_embeddings[non_noise_mask], 
    #                 np.array(topics)[non_noise_mask]
    #             ) 
    #         else:
    #             sil_score = None
    #     else:
    #         sil_score = None
    # except Exception:
    #     sil_score = None
    
    return {
        "success": True,
        "message": f"Found {n_topics} complaint topics with {noise_percentage:.1f}% noise",
        "total_negative_reviews": total_reviews,
        "n_clusters": n_topics,
        "n_topics": n_topics,
        "labels": topics,
        "noise_count": noise_count,
        "noise_percentage": noise_percentage,
        # "silhouette_score": round(sil_score, 4) if sil_score else None,
        "clusters": clusters,
        "topic_model": topic_model,
        "cleaned_reviews": cleaned_reviews
    }