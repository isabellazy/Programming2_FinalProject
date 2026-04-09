#!/usr/bin/env python3
#By Isabella Zuluaga Yusti

"""
BLAST execution module.

This module runs BLAST searches for query sequences against one or more local
databases and collects parsed tabular results.

Expected inputs:
- query_sequences: dict like {query_id: sequence_string}
- databases: list of database paths or names
- blast_params: dictionary from config.py

Expected outputs:
- Per-query BLAST hits across all databases
"""

import os
import shutil
import subprocess
import sys
import tempfile


DEFAULT_OUTFMT_FIELDS = [
    "qseqid",
    "sseqid",
    "pident",
    "length",
    "mismatch",
    "gapopen",
    "qstart",
    "qend",
    "sstart",
    "send",
    "evalue",
    "bitscore",
]


def check_blast_program(program):
    """
    Verify that the requested BLAST executable exists in PATH.
    """
    if not shutil.which(program):
        raise EnvironmentError(
            f"{program} not found in PATH.\n"
            "Please install NCBI BLAST+ and make sure the executable is available.\n"
            "Example:\n"
            "  conda install -c bioconda blast\n"
        )

def write_temp_fasta(query_id, query_sequence):
    """
    Write one query sequence to a temporary FASTA file and return its path.
    """
    temp_handle = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".fasta",
        delete=False,
        encoding="utf-8",
    )

    with temp_handle as fasta_out:
        fasta_out.write(f">{query_id}\n")
        fasta_out.write(f"{query_sequence}\n")

    return temp_handle.name


def build_blast_command(query_fasta, database_path, blast_params):
    program = blast_params.get("program", "blastn")
    evalue = str(blast_params.get("evalue", 1e-3))
    word_size = str(blast_params.get("word_size", 7))
    num_threads = str(blast_params.get("num_threads", 1))
    max_target_seqs = str(blast_params.get("max_target_seqs", 10))
    dust = blast_params.get("dust", "no")

    cmd = [
        program,
        "-query", query_fasta,
        "-db", database_path,
        "-evalue", evalue,
        "-word_size", word_size,
        "-num_threads", num_threads,
        "-max_target_seqs", max_target_seqs,
        "-outfmt", "6",
        "-dust", dust,
    ]

    if float(blast_params.get("perc_identity", 0)) > 0:
        cmd.extend(["-perc_identity", str(blast_params["perc_identity"])])

    if float(blast_params.get("query_coverage", 0)) > 0:
        cmd.extend(["-qcov_hsp_perc", str(blast_params["query_coverage"])])

    return cmd


def parse_blast_output(stdout_text, database_name):
    hits = []

    if not stdout_text.strip():
        return hits

    for line in stdout_text.strip().splitlines():
        parts = line.split("\t")

        if len(parts) != 12:
            continue

        hit = {
            "database": database_name,
            "query_id": parts[0],
            "subject_id": parts[1],
            "identity": float(parts[2]),
            "alignment_length": int(parts[3]),
            "mismatches": int(parts[4]),
            "gap_opens": int(parts[5]),
            "query_start": int(parts[6]),
            "query_end": int(parts[7]),
            "subject_start": int(parts[8]),
            "subject_end": int(parts[9]),
            "evalue": float(parts[10]),
            "bitscore": float(parts[11]),
        }

        hits.append(hit)

    return hits


def run_blast(query_id, query_sequence, database, blast_params):
    """
    Run BLAST for one query against one database.
    """
    program = blast_params.get("program", "blastn")
    check_blast_program(program)

    db_path = database
    db_name = os.path.basename(database)

    query_fasta = write_temp_fasta(query_id, query_sequence)

    try:
        cmd = build_blast_command(query_fasta, db_path, blast_params)

        sys.stdout.write(
            f"Running {program} for query '{query_id}' against database '{db_name}'...\n"
        )

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"BLAST failed for query '{query_id}' against '{db_name}'.\n"
                f"Command: {' '.join(cmd)}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        return parse_blast_output(result.stdout, db_name)

    finally:
        if os.path.exists(query_fasta):
            os.remove(query_fasta)


def run_blast_across_databases(query_sequences, databases, blast_params):
    """
    Run BLAST searches for all queries across all databases.

    Input:
    - query_sequences: dict like {query_id: sequence}
    - databases: list of database paths or database dictionaries
    - blast_params: dictionary of BLAST options

    Output:
    - dict like:
      {
          "query1": [hit1, hit2, ...],
          "query2": [hit1, hit2, ...],
      }
    """
    if not isinstance(query_sequences, dict):
        raise TypeError("query_sequences must be a dictionary: {query_id: sequence}")

    if not isinstance(databases, list):
        raise TypeError("databases must be a list")

    all_results = {}

    for query_id, query_sequence in query_sequences.items():
        sys.stdout.write(f"Processing query: {query_id}\n")
        all_results[query_id] = []

        for database in databases:
            hits = run_blast(query_id, query_sequence, database, blast_params)
            all_results[query_id].extend(hits)
    return all_results

