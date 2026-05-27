"""
text_analyzer.py — TF-IDF Text Similarity + Production Experience Detection

Two-pronged text analysis:
1. TF-IDF cosine similarity between JD text and candidate text
   (captures semantic relevance that keyword rules miss)
2. Production experience keyword detection in career descriptions
   (detects candidates who've actually shipped ML systems)
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import JD_TEXT, PRODUCTION_ML_KEYWORDS, NON_PRODUCTION_KEYWORDS


class TextAnalyzer:
    """
    Builds a TF-IDF model over all candidate texts + JD,
    then computes similarity scores.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=8000,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True,
        )
        self.jd_vector = None
        self.is_fitted = False

    def _extract_candidate_text(self, candidate):
        """
        Build a single text string from a candidate's profile:
        headline + summary + all career descriptions + skill names
        """
        parts = []

        profile = candidate.get("profile", {})
        parts.append(profile.get("headline", ""))
        parts.append(profile.get("summary", ""))
        parts.append(profile.get("current_title", ""))
        parts.append(profile.get("current_industry", ""))

        # Career history descriptions are the richest text signal
        for job in candidate.get("career_history", []):
            parts.append(job.get("title", ""))
            parts.append(job.get("description", ""))
            parts.append(job.get("industry", ""))

        # Skill names as text (helps with topic matching)
        for skill in candidate.get("skills", []):
            parts.append(skill.get("name", ""))

        # Certifications
        for cert in candidate.get("certifications", []):
            parts.append(cert.get("name", ""))

        # Education fields
        for edu in candidate.get("education", []):
            parts.append(edu.get("field_of_study", ""))

        text = " ".join(p for p in parts if p)
        # Basic cleaning
        text = re.sub(r"[^a-zA-Z0-9\s\-/]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def fit(self, candidates):
        """
        Fit the TF-IDF vectorizer on all candidate texts + JD.
        Call this once before scoring.
        """
        # Build corpus: JD + all candidates
        texts = [JD_TEXT]  # Index 0 is the JD
        for cand in candidates:
            texts.append(self._extract_candidate_text(cand))

        self.vectorizer.fit(texts)
        tfidf_matrix = self.vectorizer.transform(texts)

        # Store JD vector
        self.jd_vector = tfidf_matrix[0:1]  # Keep as sparse matrix

        # Store all candidate vectors
        self.candidate_vectors = tfidf_matrix[1:]
        self.is_fitted = True

        return self

    def compute_similarity_batch(self):
        """
        Compute cosine similarity between JD and all candidates.
        Returns array of similarity scores.
        """
        if not self.is_fitted:
            raise RuntimeError("Must call fit() before compute_similarity_batch()")

        similarities = cosine_similarity(self.jd_vector, self.candidate_vectors)[0]
        return similarities

    def compute_similarity_single(self, candidate):
        """
        Compute TF-IDF cosine similarity for a single candidate against JD.
        (Used for candidates not in the original fit corpus.)
        """
        if not self.is_fitted:
            raise RuntimeError("Must call fit() before scoring")

        text = self._extract_candidate_text(candidate)
        vec = self.vectorizer.transform([text])
        sim = cosine_similarity(self.jd_vector, vec)[0][0]
        return float(sim)


def compute_production_experience_score(candidate):
    """
    Detect production ML experience from career descriptions.

    This is separate from TF-IDF — it specifically looks for
    indicators that the candidate has SHIPPED real ML systems,
    not just studied or experimented with ML.

    Returns score 0-1.
    """
    all_desc = " ".join(
        job.get("description", "").lower()
        for job in candidate.get("career_history", [])
    )

    if not all_desc:
        return 0.0

    # Count production ML keyword hits
    prod_hits = 0
    for kw in PRODUCTION_ML_KEYWORDS:
        if kw in all_desc:
            prod_hits += 1

    # Count non-production keyword hits
    non_prod_hits = 0
    for kw in NON_PRODUCTION_KEYWORDS:
        if kw in all_desc:
            non_prod_hits += 1

    # Specific high-value phrase detection
    high_value_phrases = [
        "ranking system", "search system", "recommendation system",
        "retrieval system", "matching system", "scoring system",
        "deployed to production", "serving real users",
        "end-to-end ml", "end-to-end machine learning",
        "embedding", "vector search", "vector database",
        "a/b test", "evaluation framework",
        "real-time", "batch processing", "feature pipeline",
        "model training", "model serving", "inference",
    ]

    high_value_hits = sum(1 for p in high_value_phrases if p in all_desc)

    # Score calculation
    prod_score = min(1.0, prod_hits / 10)  # 10+ hits = full score
    high_value_bonus = min(0.3, high_value_hits * 0.06)
    non_prod_penalty = min(0.4, non_prod_hits * 0.05)

    score = prod_score + high_value_bonus - non_prod_penalty
    return max(0.0, min(1.0, score))
