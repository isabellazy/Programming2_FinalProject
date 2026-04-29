#!/usr/bin/env python3
#By Candelaria Domingo

"""
Sequence classification module.

This module is responsible for interpreting BLAST results,
ranking hits across multiple databases, and assigning a predicted
identity or category to each query sequence.

Conceptual inputs:
- BLAST results from multiple databases

Conceptual outputs:
- Predicted labels or identities for each query sequence
"""

import os
import sys


def rank_hits(blast_results: list[dict]) -> list[dict]:
    """
    Rank BLAST hits across all databases for a single query.

    Inputs:
    - blast_results: list of dicts, each representing a BLAST hit with keys:
        'db'         : source database name
        'subject_id' : subject sequence ID
        'identity'   : percent identity (float, 0-100)
        'evalue'     : E-value (float, lower is better)
        'bitscore'   : bit score (float, higher is better)
        'label'      : assigned category/label from the database (optional)

    Outputs:
    - A ranked list of hit dicts, sorted from best to worst.

    Ranking criteria (in priority order):
    1. Highest bit score  (primary — comparable across databases after normalization)
    2. Lowest E-value     (tiebreaker)
    3. Highest identity   (final tiebreaker)
    """
    if not blast_results:
        return []

    # Normalize bit scores within each database so scores are comparable
    # across databases of different sizes.  We use min-max normalization
    # per database; scores from a single database are left as-is.
    from collections import defaultdict

    db_scores: defaultdict[str, list[float]] = defaultdict(list)
    for hit in blast_results:
        db_scores[hit['db']].append(hit['bitscore'])

    db_min = {db: min(scores) for db, scores in db_scores.items()}
    db_max = {db: max(scores) for db, scores in db_scores.items()}

    def normalized_bitscore(hit: dict) -> float:
        db = hit['db']
        lo, hi = db_min[db], db_max[db]
        if hi == lo:
            return 1.0          # all scores identical — treat as maximum
        return (hit['bitscore'] - lo) / (hi - lo)

    ranked: list[dict] = sorted(
        blast_results,
        key=lambda h: (
            -normalized_bitscore(h),   # descending normalized bitscore
            h['evalue'],               # ascending e-value
            -h['identity'],            # descending identity
        )
    )

    return ranked


def select_best_hit(blast_results: list[dict]) -> dict | None:
    """
    Select the single best hit for a query from all database results.

    Inputs:
    - blast_results: list of hit dicts (same format as rank_hits input).

    Outputs:
    - The best hit dict, or None if blast_results is empty.
    """
    ranked = rank_hits(blast_results)
    return ranked[0] if ranked else None


def classify_sequences(
    all_query_results: dict[str, list[dict]],
    evalue_threshold: float = 1e-5,
    identity_threshold: float = 70.0,
) -> dict[str, str]:
    """
    Assign a predicted identity/category to every query sequence.

    Inputs:
    - all_query_results: dict mapping query_id -> list of hit dicts
        (one list per query, each list may contain hits from multiple databases).
    - evalue_threshold: maximum E-value to accept a hit (default 1e-5).
    - identity_threshold: minimum percent identity to accept a hit (default 70.0).

    Outputs:
    - predictions: dict mapping query_id -> predicted label string.
        Queries with no acceptable hit are labelled "Unclassified".

    Example:
    >>> results = {
    ...     "seq1": [{"db": "db1", "subject_id": "virus_A", "identity": 98.0,
    ...               "evalue": 1e-50, "bitscore": 300, "label": "Influenza A"}],
    ...     "seq2": [],
    ... }
    >>> classify_sequences(results)
    {'seq1': 'Influenza A', 'seq2': 'Unclassified'}
    """
    predictions: dict[str, str] = {}


    for query_id, hits in all_query_results.items():
        # Filter hits that meet quality thresholds
        acceptable: list[dict] = [
            h for h in hits
            if h.get('evalue', 1.0) <= evalue_threshold
            and h.get('identity', 0.0) >= identity_threshold
        ]

        best: dict | None = select_best_hit(acceptable)

        if best is None:
            predictions[query_id] = "Unclassified"
        else:
            # Use explicit label if present, otherwise fall back to subject_id
            predictions[query_id] = best.get('label') or best.get('subject_id', 'Unclassified')

    return predictions

def load_blast_results(results_file: str) -> dict[str, list[dict]]:
    """
    Load BLAST results from a text file with this format:

    Query: query_name
    db1    subject_id    identity    alignment_length    evalue    bitscore

    Output:
    - dict mapping query_id -> list of hit dicts
    """
    if not os.path.isfile(results_file):
        raise FileNotFoundError(f"Results file not found: {results_file}")

    all_query_results: dict[str, list[dict]] = {}
    current_query: str | None = None

    with open(results_file, "r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()

            if not line:
                continue

            if line.startswith("Query: "):
                current_query = line.replace("Query: ", "", 1)
                all_query_results[current_query] = []
                continue

            parts: list[str] = line.split("\t")

            if len(parts) != 6:
                continue

            hit = {
                "db": parts[0],
                "subject_id": parts[1],
                "identity": float(parts[2]),
                "alignment_length": int(parts[3]),
                "evalue": float(parts[4]),
                "bitscore": float(parts[5]),
            }

            if current_query is not None:
                all_query_results[current_query].append(hit)

    return all_query_results



def classify_results_file(results_file, evalue_threshold=1e-5, identity_threshold=70.0):
    """
    Read a BLAST results file and classify all queries.

    Output:
    - dict mapping query_id -> predicted label
    """
    all_query_results = load_blast_results(results_file)

    predictions = classify_sequences(
        all_query_results,
        evalue_threshold=evalue_threshold,
        identity_threshold=identity_threshold
    )

    return predictions

def save_classification_results(predictions: dict[str, str], results_file: str) -> str:
    """
    Save classification results in the same results directory.

    Example:
    results/q1/q1_results.txt -> results/q1/q1_classification.txt
    """
    if not os.path.isfile(results_file):
        raise FileNotFoundError(f"Results file not found: {results_file}")

    results_dir = os.path.dirname(results_file)
    results_base = os.path.basename(results_file)

    if results_base.endswith("_results.txt"):
        output_name = results_base.replace("_results.txt", "_classification.txt")
    else:
        output_name = "classification.txt"

    output_file = os.path.join(results_dir, output_name)

    with open(output_file, "w", encoding="utf-8") as out:
        for query_id, label in predictions.items():
            out.write(f"{query_id}\t{label}\n")

    sys.stdout.write(f"Classification results saved in: {output_file}\n")
    return output_file


def classify_results_file(
    results_file: str,
    evalue_threshold: float = 1e-5,
    identity_threshold: float = 70.0,
    save_output: bool = False,
) -> dict[str, str]:
    all_query_results: dict[str, list[dict]] = load_blast_results(results_file)

    predictions: dict[str, str] = classify_sequences(
        all_query_results,
        evalue_threshold=evalue_threshold,
        identity_threshold=identity_threshold
    )

    if save_output:
        save_classification_results(predictions, results_file)

    return predictions
