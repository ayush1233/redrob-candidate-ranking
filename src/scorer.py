"""
scorer.py — Multi-Dimensional Weighted Scoring Engine

Combines all feature dimensions into a single composite score.
Two-stage approach:
  Stage 1: Fast filtering on cheap features (all 100K)
  Stage 2: Deep scoring on rich features (top ~3K)
"""

import numpy as np
from src.config import DIMENSION_WEIGHTS
from src.feature_engine import extract_all_features, extract_fast_features
from src.text_analyzer import TextAnalyzer, compute_production_experience_score
from src.honeypot_detector import detect_honeypot


def compute_composite_score(features, text_sim_score=0.0):
    """
    Compute the final composite score from all dimension scores.

    Args:
        features: dict of dimension_name → score (0-1)
        text_sim_score: TF-IDF similarity score (0-1)

    Returns:
        float: composite score (0-1)
    """
    # Add text similarity to features
    features["text_similarity"] = text_sim_score

    score = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        score += weight * features.get(dim, 0.0)

    return score


class CandidateRanker:
    """
    Two-stage candidate ranking engine.

    Stage 1: Fast filter — cheap features on all 100K candidates
             → keep top N candidates
    Stage 2: Deep scoring — full features + TF-IDF on top N
             → produce final ranking
    """

    def __init__(self, top_n_stage1=3000, final_top_k=100):
        self.top_n_stage1 = top_n_stage1
        self.final_top_k = final_top_k
        self.text_analyzer = TextAnalyzer()

    def rank(self, candidates, verbose=True):
        """
        Full ranking pipeline.

        Args:
            candidates: list of candidate dicts
            verbose: print progress

        Returns:
            list of (candidate, score, features, honeypot_prob) tuples,
            sorted by score descending, length = final_top_k
        """
        import time
        start = time.time()

        # ─── STAGE 1: Fast filtering ───
        if verbose:
            print(f"[Stage 1] Fast filtering {len(candidates)} candidates...")

        fast_scores = []
        for i, cand in enumerate(candidates):
            fast = extract_fast_features(cand)
            fast_scores.append((i, fast))
            if verbose and (i + 1) % 20000 == 0:
                print(f"  Processed {i+1}/{len(candidates)}")

        # Sort by fast score and keep top N
        fast_scores.sort(key=lambda x: x[1], reverse=True)
        stage1_indices = [idx for idx, _ in fast_scores[:self.top_n_stage1]]

        stage1_candidates = [candidates[i] for i in stage1_indices]

        if verbose:
            elapsed = time.time() - start
            print(f"  → Kept {len(stage1_candidates)} candidates "
                  f"(min fast score: {fast_scores[self.top_n_stage1-1][1]:.3f})")
            print(f"  → Stage 1 took {elapsed:.1f}s")

        # ─── STAGE 2: TF-IDF fitting on shortlisted candidates ───
        if verbose:
            print(f"\n[Stage 2] Building TF-IDF model on {len(stage1_candidates)} candidates...")

        self.text_analyzer.fit(stage1_candidates)
        tfidf_similarities = self.text_analyzer.compute_similarity_batch()

        if verbose:
            elapsed = time.time() - start
            print(f"  → TF-IDF model built ({elapsed:.1f}s)")

        # ─── STAGE 3: Deep scoring ───
        if verbose:
            print(f"\n[Stage 3] Deep scoring {len(stage1_candidates)} candidates...")

        scored_candidates = []
        for i, cand in enumerate(stage1_candidates):
            # Full feature extraction
            features = extract_all_features(cand)

            # TF-IDF similarity
            text_sim = float(tfidf_similarities[i])

            # Production experience (from text_analyzer)
            prod_exp = compute_production_experience_score(cand)

            # Combined text score: TF-IDF + production keywords
            combined_text_score = 0.6 * text_sim + 0.4 * prod_exp

            # Honeypot detection
            hp_prob = detect_honeypot(cand)

            # Composite score
            composite = compute_composite_score(features, combined_text_score)

            # Apply honeypot penalty
            if hp_prob >= 0.5:
                composite *= 0.0  # Hard zero for likely honeypots
            elif hp_prob >= 0.3:
                composite *= 0.3  # Severe penalty for suspicious
            elif hp_prob >= 0.2:
                composite *= 0.7  # Moderate penalty

            scored_candidates.append({
                "candidate": cand,
                "score": composite,
                "features": features,
                "text_similarity": text_sim,
                "production_exp": prod_exp,
                "honeypot_prob": hp_prob,
            })

            if verbose and (i + 1) % 1000 == 0:
                print(f"  Scored {i+1}/{len(stage1_candidates)}")

        # Sort by score descending
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        # Take top K
        top_k = scored_candidates[:self.final_top_k]

        if verbose:
            elapsed = time.time() - start
            print(f"\n[Done] Ranking complete in {elapsed:.1f}s")
            print(f"  Top score: {top_k[0]['score']:.4f}")
            print(f"  #100 score: {top_k[-1]['score']:.4f}")

            # Stats
            hp_count = sum(1 for c in top_k if c["honeypot_prob"] >= 0.3)
            print(f"  Honeypots in top 100: {hp_count}")

        return top_k
