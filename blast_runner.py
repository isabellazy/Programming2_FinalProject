# By Isabella Zuluaga Yusti  

"""
BLAST execution module.

This module handles running BLAST searches for query sequences against
multiple local databases and collecting the raw results.

It isolates BLAST-specific logic from classification and evaluation logic.

Conceptual inputs:
- Query sequences
- Local BLAST databases
- BLAST parameters

Conceptual outputs:
- Raw BLAST result records
"""

def run_blast(query_sequence, database, blast_params):
    """
    Run a BLAST search for a single query against one database.

    Inputs:
    - query_sequence: A single biological sequence.
    - database: Path or identifier of a BLAST database.
    - blast_params: Parameters such as e-value threshold and word size.

    Outputs:
    - Raw BLAST results (e.g., alignments, scores, metadata).

    High-level steps:
    1. Format the query sequence for BLAST input.
    2. Execute the BLAST command locally.
    3. Parse and return the BLAST output.
    """
    pass
    
def run_blast_across_databases(query_sequences, databases, blast_params):
    """
    Run BLAST searches for all queries across all databases.

    Inputs:
    - query_sequences: A list of sequences to classify.
    - databases: A list of BLAST databases.
    - blast_params: BLAST execution parameters.

    Outputs:
    - A structured collection of BLAST results per query and per database.

    High-level steps:
    1. Loop over each query sequence.
    2. For each query, run BLAST against every database.
    3. Store results in a unified data structure.
    """

    results = {}

    for query_id, sequence in query_sequences.items():
        results[query_id] = []

    for db in databases:
        hit = run_blast(sequence, db, blast_params)
        results[query_id].append(hit)

    return results    
