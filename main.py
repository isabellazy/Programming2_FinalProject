#!/usr/bin/env python3
# By Isabella Zuluaga Yusti

"""
main.py

Main entry point for the multi-database BLAST classifier pipeline.

This script coordinates the complete workflow of the project, including:
- listing available databases
- downloading NCBI databases
- creating or reusing local databases
- loading configuration files
- running BLAST searches
- classifying BLAST results

The script acts as the central orchestrator of the pipeline and delegates
specific tasks to the corresponding modules.

Typical usage:
    python3 main.py --list_databases
    python3 main.py --download_ncbi 16S_ribosomal_RNA
    python3 main.py --db_name db1 --fasta_file databases/db1.fasta --db_type nucl
    python3 main.py --run_blast --query_file queries/query1.fasta
    python3 main.py --classify results/query1/query1_results.txt
"""

import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(BASE_DIR, "Format_Library-Patrick"))
sys.path.append(os.path.join(BASE_DIR, "BLAST_Library-Isabella"))
sys.path.append(os.path.join(BASE_DIR, "Evaluation_Library-Candelaria"))

from database_manager import (
    get_database,
    download_ncbi_database,
    get_all_database_paths_by_type,
    list_databases,
)
from config import load_config, print_config
from file_handler import load_fasta
from blast_runner import BlastRunner
from classifier import classify_results_file
from results_handler import save_results


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Multi-database BLAST classifier"
    )

    parser.add_argument(
        "--db_name",
        help="Name of the BLAST database"
    )

    parser.add_argument(
        "--fasta_file",
        help="Path to the FASTA file used to create the database"
    )

    parser.add_argument(
        "--db_type",
        choices=["nucl", "nucleotide", "prot", "protein"],
        help="Type of database sequence"
    )

    parser.add_argument(
        "--list_databases",
        action="store_true",
        help="List available BLAST databases"
    )

    parser.add_argument(
        "--config",
        default="Format_Library-Patrick/blast_config.txt",
        help="Path to the configuration file"
    )

    parser.add_argument(
        "--show_config",
        action="store_true",
        help="Print the loaded configuration"
    )

    parser.add_argument(
        "--query_file",
        help="Path to the query FASTA file"
    )

    parser.add_argument(
        "--run_blast",
        action="store_true",
        help="Run BLAST using the selected query file"
    )

    parser.add_argument(
        "--classify",
        help="Path to a BLAST results file"
    )

    parser.add_argument(
        "--download_ncbi",
        help="Download a prebuilt NCBI BLAST database"
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Main workflow controller for the pipeline.

    This function interprets command-line arguments and routes execution
    to the appropriate module.

    Supported actions:
    - list databases
    - show configuration
    - download NCBI database
    - create or reuse local database
    - run BLAST searches
    - classify BLAST results
    """
    args = parse_args()

    if args.list_databases:
        list_databases()
        return

    if args.show_config:
        config = load_config(args.config)
        print_config(config)
        return

    if args.download_ncbi:
        db_path = download_ncbi_database(args.download_ncbi)
        sys.stdout.write(f"Downloaded database ready: {db_path}\n")
        return

    if args.classify:
        config = load_config(args.config)

        predictions = classify_results_file(
            results_file=args.classify,
            evalue_threshold=float(config.get("evalue", 1e-5)),
            identity_threshold=float(config.get("perc_identity", 70.0)),
            save_output=True
        )

        sys.stdout.write("Predicted classifications:\n")
        for query_id, label in predictions.items():
            sys.stdout.write(f"{query_id}\t{label}\n")
        return

    if args.db_name or args.fasta_file or args.db_type:
        if not args.run_blast:
            if not (args.db_name and args.fasta_file and args.db_type):
                sys.stderr.write(
                    "Error: --db_name, --fasta_file, and --db_type must be provided together.\n"
                )
                sys.exit(1)

            db_path = get_database(
                fasta_path=args.fasta_file,
                db_name=args.db_name,
                db_type=args.db_type
            )

            sys.stdout.write(f"Database ready: {db_path}\n")
            return

    if args.run_blast:
        if not args.query_file:
            sys.stderr.write(
                "Error: --run_blast requires --query_file.\n"
            )
            sys.exit(1)

        config = load_config(args.config)
        queries = load_fasta(args.query_file)

        if args.db_name:
            databases = [os.path.join("databases", args.db_name, args.db_name)]
        else:
            program = str(config.get("program", "blastn")).lower()

            if program == "blastn":
                databases = get_all_database_paths_by_type("nucl")
            elif program == "blastp":
                databases = get_all_database_paths_by_type("prot")
            else:
                sys.stderr.write(f"Error: Unsupported BLAST program '{program}'.\n")
                sys.exit(1)

        if not databases:
            sys.stderr.write("Error: No BLAST databases available.\n")
            sys.exit(1)

        runner = BlastRunner(config)

        blast_results = runner.run_blast_across_databases(
            query_sequences=queries,
            databases=databases
        )

        save_results(blast_results, args.query_file)
        return

    sys.stdout.write(
        "No action selected.\n"
        "Use one of the following options:\n"
        "  --list_databases\n"
        "  --show_config [--config <file>]\n"
        "  --download_ncbi <db_name>\n"
        "  --db_name <name> --fasta_file <file> --db_type <nucl|prot>\n"
        "  --run_blast --query_file <file> [--db_name <name>] [--config <file>]\n"
        "  --classify <results_file> [--config <file>]\n"
    )


if __name__ == "__main__":
    main()
