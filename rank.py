#!/usr/bin/env python3
"""
rank.py — Main Entry Point for Candidate Ranking

Intelligent Candidate Discovery & Ranking System for Redrob Hackathon.

Usage:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Architecture:
    Stage 1: Fast filter (all 100K) → top 3K by cheap features
    Stage 2: TF-IDF text model (top 3K) → semantic similarity
    Stage 3: Deep scoring (top 3K) → 6-dimension weighted composite
    Stage 4: Honeypot filtering → eliminate impossible profiles
    Stage 5: Final ranking + reasoning → top 100 CSV

Constraints: ≤5 min, ≤16 GB RAM, CPU only, no network calls.
"""

import argparse
import csv
import json
import sys
import time
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scorer import CandidateRanker
from src.reasoning_generator import generate_all_reasonings


def load_candidates(filepath, verbose=True):
    """
    Load candidates from JSONL file, streaming line-by-line.
    """
    candidates = []
    if verbose:
        print(f"Loading candidates from {filepath}...")

    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
                candidates.append(candidate)
            except json.JSONDecodeError as e:
                print(f"  Warning: Skipping line {i+1} (JSON parse error: {e})")

            if verbose and (i + 1) % 25000 == 0:
                print(f"  Loaded {i+1} candidates...")

    if verbose:
        print(f"  → Total candidates loaded: {len(candidates)}")

    return candidates


def validate_submission(output_path, candidate_ids_set):
    """
    Validate the submission CSV matches spec requirements.
    """
    errors = []

    with open(output_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Check row count
    if len(rows) != 100:
        errors.append(f"Expected 100 rows, got {len(rows)}")

    # Check ranks
    ranks = [int(r["rank"]) for r in rows]
    if sorted(ranks) != list(range(1, 101)):
        errors.append("Ranks must be exactly 1-100, each used once")

    # Check candidate IDs exist
    for r in rows:
        if r["candidate_id"] not in candidate_ids_set:
            errors.append(f"candidate_id {r['candidate_id']} not in dataset")

    # Check duplicate IDs
    ids = [r["candidate_id"] for r in rows]
    if len(set(ids)) != len(ids):
        errors.append("Duplicate candidate_ids found")

    # Check score monotonicity
    scores = [float(r["score"]) for r in rows]
    for i in range(1, len(scores)):
        if scores[i] > scores[i-1]:
            errors.append(f"Scores not monotonically non-increasing at rank {i+1}")
            break

    return errors


def write_submission(output_path, ranked_candidates, reasonings):
    """
    Write the final submission CSV.
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank_idx, (entry, reasoning) in enumerate(
            zip(ranked_candidates, reasonings)
        ):
            rank = rank_idx + 1
            cand_id = entry["candidate"]["candidate_id"]
            score = round(entry["score"], 4)

            # Escape reasoning for CSV
            reasoning_clean = reasoning.replace('"', "'")

            writer.writerow([cand_id, rank, score, reasoning_clean])


def main():
    parser = argparse.ArgumentParser(
        description="Rank candidates for Redrob hackathon"
    )
    parser.add_argument(
        "--candidates",
        type=str,
        default="./India_runs_data_and_ai_challenge/candidates.jsonl",
        help="Path to candidates JSONL file",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="./submission.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=3000,
        help="Number of candidates to keep after Stage 1 filtering",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )
    args = parser.parse_args()

    verbose = not args.quiet
    total_start = time.time()

    # ─── Load candidates ───
    candidates = load_candidates(args.candidates, verbose)

    if not candidates:
        print("ERROR: No candidates loaded!")
        sys.exit(1)

    # Build candidate ID set for validation
    candidate_ids = {c["candidate_id"] for c in candidates}

    # ─── Run ranking pipeline ───
    ranker = CandidateRanker(
        top_n_stage1=args.top_n,
        final_top_k=100,
    )
    ranked = ranker.rank(candidates, verbose=verbose)

    # ─── Generate reasoning ───
    if verbose:
        print("\n[Reasoning] Generating fact-based reasoning for top 100...")

    reasonings = generate_all_reasonings(ranked)

    # ─── Write submission ───
    write_submission(args.out, ranked, reasonings)

    if verbose:
        print(f"\n[Output] Written to {args.out}")

    # ─── Validate ───
    if verbose:
        print("\n[Validation] Checking submission format...")

    errors = validate_submission(args.out, candidate_ids)
    if errors:
        print("  ⚠ VALIDATION ERRORS:")
        for e in errors:
            print(f"    - {e}")
    else:
        print("  ✓ All validation checks passed!")

    # ─── Print summary ───
    total_elapsed = time.time() - total_start

    if verbose:
        print(f"\n{'='*60}")
        print(f"RANKING COMPLETE")
        print(f"{'='*60}")
        print(f"  Total time: {total_elapsed:.1f}s")
        print(f"  Candidates processed: {len(candidates)}")
        print(f"  Output: {args.out}")
        print(f"  Top 5 candidates:")
        for i, entry in enumerate(ranked[:5]):
            c = entry["candidate"]
            print(
                f"    {i+1}. {c['candidate_id']} | "
                f"{c['profile']['current_title']} at {c['profile']['current_company']} | "
                f"Score: {entry['score']:.4f} | "
                f"YoE: {c['profile']['years_of_experience']}"
            )

        print(f"\n  Bottom 5 (of top 100):")
        for i, entry in enumerate(ranked[95:100]):
            c = entry["candidate"]
            print(
                f"    {96+i}. {c['candidate_id']} | "
                f"{c['profile']['current_title']} at {c['profile']['current_company']} | "
                f"Score: {entry['score']:.4f}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
