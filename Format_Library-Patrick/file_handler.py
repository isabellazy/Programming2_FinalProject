#!/usr/bin/env python3
# By Patrick Bircher

"""
file_handler.py

Handles general file input operations for the pipeline.

Currently supports:
- reading FASTA query files into dictionaries

This module is intended for input/output helper functions that do not
belong specifically to BLAST execution, classification, or database
management.

Functions:
    load_fasta: Load a FASTA file into a dictionary of sequences.

Typical usage:
    queries = load_fasta("queries/query1.fasta")
"""

import os


# ---------------------------------------------------------------------------
# FASTA input handling
# ---------------------------------------------------------------------------

def load_fasta(file_path: str) -> dict[str, str]:
    """
    Load a FASTA file into a dictionary.

    Each record in the FASTA file is converted into:
        {sequence_id: sequence_string}

    Args:
        file_path (str): Path to the FASTA file.

    Returns:
        dict[str, str]: Dictionary mapping sequence IDs to sequence strings.

    Raises:
        FileNotFoundError: If the FASTA file does not exist.

    Example:
        FASTA input:
            >seq1
            ACTG
            >seq2
            TTAA

        Output:
            {
                "seq1": "ACTG",
                "seq2": "TTAA"
            }
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Query FASTA file not found: {file_path}")

    sequences: dict[str, str] = {}
    current_id: str | None = None
    seq_lines: list[str] = []

    with open(file_path, "r", encoding="utf-8") as fasta_file:
        for line in fasta_file:
            line = line.strip()

            if not line:
                continue

            if line.startswith(">"):
                if current_id is not None:
                    sequences[current_id] = "".join(seq_lines)

                current_id = line[1:]
                seq_lines = []
            else:
                seq_lines.append(line)

    if current_id is not None:
        sequences[current_id] = "".join(seq_lines)

    return sequences