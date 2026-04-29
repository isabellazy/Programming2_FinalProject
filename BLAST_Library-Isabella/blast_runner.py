#!/usr/bin/env python3
#By Isabella Zuluaga Yusti

"""
BLAST execution module.

This module runs BLAST searches for query sequences against one or more local
databases and collects parsed tabular results.

Expected inputs:
- query_sequences: dict like {query_id: sequence_string}
- databases: list of database paths
- blast_params: dictionary from config.py

Expected outputs:
- Per-query BLAST hits across all databases
"""

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any


class BlastRunner:
    """
    Execute BLAST searches using a shared configuration.

    Attributes:
        blast_params (dict[str, Any]): BLAST parameter dictionary loaded from config.
        program (str): BLAST executable name, e.g. 'blastn'.
    """

    DEFAULT_OUTFMT_FIELDS: list[str] = [
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

    def __init__(self, blast_params: dict[str, Any]) -> None:
        """
        Initialize the BLAST runner with configuration parameters.

        Args:
            blast_params (dict[str, Any]): Dictionary of BLAST options.
        """
        self.blast_params = blast_params
        self.program: str = str(blast_params.get("program", "blastn"))

    def check_blast_program(self) -> None:
        """
        Verify that the requested BLAST executable exists in PATH.

        Raises:
            EnvironmentError: If the BLAST program is not found.
        """
        if not shutil.which(self.program):
            raise EnvironmentError(
                f"{self.program} not found in PATH.\n"
                "Please install NCBI BLAST+ and make sure the executable is available.\n"
                "Example:\n"
                "  conda install -c bioconda blast\n"
            )

    def write_temp_fasta(self, query_id: str, query_sequence: str) -> str:
        """
        Write one query sequence to a temporary FASTA file and return its path.

        Args:
            query_id (str): Query sequence identifier.
            query_sequence (str): Query sequence string.

        Returns:
            str: Path to the temporary FASTA file.
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

    def build_blast_command(self, query_fasta: str, database_path: str) -> list[str]:
        """
        Build the BLAST command using stored configuration parameters.

        Args:
            query_fasta (str): Path to the temporary FASTA query file.
            database_path (str): BLAST database prefix path.

        Returns:
            list[str]: Command list to pass to subprocess.run().
        """
        evalue: str = str(self.blast_params.get("evalue", 1e-3))
        word_size: str = str(self.blast_params.get("word_size", 7))
        num_threads: str = str(self.blast_params.get("num_threads", 1))
        max_target_seqs: str = str(self.blast_params.get("max_target_seqs", 10))
        dust: str = str(self.blast_params.get("dust", "no"))

        cmd: list[str] = [
            self.program,
            "-query", query_fasta,
            "-db", database_path,
            "-evalue", evalue,
            "-word_size", word_size,
            "-num_threads", num_threads,
            "-max_target_seqs", max_target_seqs,
            "-outfmt", "6",
            "-dust", dust,
        ]

        if float(self.blast_params.get("perc_identity", 0)) > 0:
            cmd.extend(["-perc_identity", str(self.blast_params["perc_identity"])])

        if float(self.blast_params.get("query_coverage", 0)) > 0:
            cmd.extend(["-qcov_hsp_perc", str(self.blast_params["query_coverage"])])

        return cmd

    def parse_blast_output(self, stdout_text: str, database_name: str) -> list[dict[str, Any]]:
        """
        Parse BLAST tabular output into a list of hit dictionaries.

        Args:
            stdout_text (str): Raw BLAST stdout in outfmt 6 format.
            database_name (str): Name of the source database.

        Returns:
            list[dict[str, Any]]: Parsed BLAST hits.
        """
        hits: list[dict[str, Any]] = []

        if not stdout_text.strip():
            return hits

        for line in stdout_text.strip().splitlines():
            parts: list[str] = line.split("\t")

            if len(parts) != 12:
                continue

            hit: dict[str, Any] = {
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

    def run_blast(self, query_id: str, query_sequence: str, database: str) -> list[dict[str, Any]]:
        """
        Run BLAST for one query against one database.

        Args:
            query_id (str): Query sequence identifier.
            query_sequence (str): Query sequence string.
            database (str): BLAST database prefix path.

        Returns:
            list[dict[str, Any]]: Parsed BLAST hits for this query/database pair.

        Raises:
            RuntimeError: If BLAST execution fails.
        """
        self.check_blast_program()

        db_path: str = database
        db_name: str = os.path.basename(database)

        query_fasta: str = self.write_temp_fasta(query_id, query_sequence)

        try:
            cmd: list[str] = self.build_blast_command(query_fasta, db_path)

            sys.stdout.write(
                f"Running {self.program} for query '{query_id}' against database '{db_name}'...\n"
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

            return self.parse_blast_output(result.stdout, db_name)

        finally:
            if os.path.exists(query_fasta):
                os.remove(query_fasta)

    def run_blast_across_databases(
        self,
        query_sequences: dict[str, str],
        databases: list[str],
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Run BLAST searches for all queries across all databases.

        Args:
            query_sequences (dict[str, str]): Dictionary like {query_id: sequence}.
            databases (list[str]): List of database prefix paths.

        Returns:
            dict[str, list[dict[str, Any]]]: Dictionary like:
                {
                    "query1": [hit1, hit2, ...],
                    "query2": [hit1, hit2, ...],
                }

        Raises:
            TypeError: If query_sequences is not a dictionary or databases is not a list.
        """
        if not isinstance(query_sequences, dict):
            raise TypeError("query_sequences must be a dictionary: {query_id: sequence}")

        if not isinstance(databases, list):
            raise TypeError("databases must be a list")

        all_results: dict[str, list[dict[str, Any]]] = {}

        for query_id, query_sequence in query_sequences.items():
            sys.stdout.write(f"Processing query: {query_id}\n")
            all_results[query_id] = []

            for database in databases:
                hits = self.run_blast(query_id, query_sequence, database)
                all_results[query_id].extend(hits)

        return all_results
