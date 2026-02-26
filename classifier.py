#!/usr/bin/env python3

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


def rank_hits(blast_results):
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

    db_scores = defaultdict(list)
    for hit in blast_results:
        db_scores[hit['db']].append(hit['bitscore'])

    db_min = {db: min(scores) for db, scores in db_scores.items()}
    db_max = {db: max(scores) for db, scores in db_scores.items()}

    def normalized_bitscore(hit):
        db = hit['db']
        lo, hi = db_min[db], db_max[db]
        if hi == lo:
            return 1.0          # all scores identical — treat as maximum
        return (hit['bitscore'] - lo) / (hi - lo)

    ranked = sorted(
        blast_results,
        key=lambda h: (
            -normalized_bitscore(h),   # descending normalized bitscore
            h['evalue'],               # ascending e-value
            -h['identity'],            # descending identity
        )
    )

    return ranked


def select_best_hit(blast_results):
    """
    Select the single best hit for a query from all database results.

    Inputs:
    - blast_results: list of hit dicts (same format as rank_hits input).

    Outputs:
    - The best hit dict, or None if blast_results is empty.
    """
    ranked = rank_hits(blast_results)
    return ranked[0] if ranked else None


def classify_sequences(all_query_results, evalue_threshold=1e-5, identity_threshold=70.0):
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
    predictions = {}

    for query_id, hits in all_query_results.items():
        # Filter hits that meet quality thresholds
        acceptable = [
            h for h in hits
            if h.get('evalue', 1.0) <= evalue_threshold
            and h.get('identity', 0.0) >= identity_threshold
        ]

        best = select_best_hit(acceptable)

        if best is None:
            predictions[query_id] = "Unclassified"
        else:
            # Use explicit label if present, otherwise fall back to subject_id
            predictions[query_id] = best.get('label') or best.get('subject_id', 'Unclassified')

    return predictions


def main():
    """
    Demonstration / smoke-test for the classifier module.

    In the full pipeline this module is called by main.py after
    blast_runner.py has produced the raw BLAST results.
    """
    # --- Synthetic example data ------------------------------------------
    # Two queries; hits come from two imaginary databases ("viral_db" and
    # "bacterial_db").
    example_results = {
        "query_seq_1": [
            {"db": "viral_db",     "subject_id": "NC_002023", "identity": 97.5,
             "evalue": 1e-120, "bitscore": 450, "label": "Influenza A virus"},
            {"db": "bacterial_db", "subject_id": "AB123456",  "identity": 62.0,
             "evalue": 5e-3,  "bitscore": 80,  "label": "Streptococcus pyogenes"},
        ],
        "query_seq_2": [
            {"db": "viral_db",     "subject_id": "NC_001608", "identity": 85.0,
             "evalue": 3e-60,  "bitscore": 210, "label": "Rabies lyssavirus"},
            {"db": "bacterial_db", "subject_id": "XY789012",  "identity": 88.0,
             "evalue": 1e-80,  "bitscore": 290, "label": "Escherichia coli"},
        ],
        "query_seq_3": [],   # No BLAST hits at all
    }

    print("=== Classifier Demo ===\n")

    for query_id, hits in example_results.items():
        print(f"Query: {query_id}")
        ranked = rank_hits(hits)
        if ranked:
            print(f"  Ranked hits (best first):")
            for rank, h in enumerate(ranked, 1):
                print(f"    {rank}. [{h['db']}] {h['subject_id']}  "
                      f"identity={h['identity']}%  evalue={h['evalue']:.1e}  "
                      f"bitscore={h['bitscore']}  label={h.get('label','N/A')}")
        else:
            print("  No hits.")
        print()

    predictions = classify_sequences(example_results)
    print("=== Predicted Classifications ===")
    for qid, label in predictions.items():
        print(f"  {qid}: {label}")


if __name__ == "__main__":
    main()
