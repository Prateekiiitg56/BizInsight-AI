import re

def preprocess_reviews(reviews):
    """
    Minimal cleaning for clustering:
    - lowercase
    - remove all digits (numbers)
    - remove '#' and '@'
    - remove punctuation (keep apostrophes for contractions like don't)
    - do NOT remove stopwords or lemmatize
    """
    if isinstance(reviews, str):
        reviews = [reviews]
    
    cleaned = []
    for review in reviews:
        if not isinstance(review, str):
            review = str(review)
        
        review = review.lower()
        # Remove all digits
        review = re.sub(r'\d+', '', review)
        # Remove # and @
        review = re.sub(r'[#@]', '', review)
        # Remove punctuation except apostrophes
        review = re.sub(r'[^\w\s\']', '', review)
        # Remove extra spaces
        review = re.sub(r'\s+', ' ', review).strip()
        
        if review:
            cleaned.append(review)
    
    return cleaned