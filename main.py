#!/usr/bin/env python3
#By Isabella Zuluaga Yusti

import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(BASE_DIR, "Format_Library-Patrick"))
sys.path.append(os.path.join(BASE_DIR, "BLAST_Library-Isabella"))
sys.path.append(os.path.join(BASE_DIR, "Evaluation_Library-Candelaria"))

from database_manager import get_database
from config import load_config, print_config
from blast_runner import run_blast_across_databases
from classifier import classify_results_file
from evaluation import evaluate_classification_file, print_metrics_report
from results_handler import save_results


def parse_args():
    """
    Parse command-line arguments.
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
        "--evaluate",
        help="Path to a classification results file"
    )

    parser.add_argument(
        "--ground_truth",
        help="Path to the ground truth labels file"
    )

    return parser.parse_args()


def get_all_database_names(databases_dir="databases"):
    """
    Return a list of all available BLAST database names.
    """
    if not os.path.isdir(databases_dir):
        return []

    found_databases = []
    valid_extensions = (
        ".nhr", ".nin", ".nsq", ".ndb", ".not", ".ntf", ".nto",
        ".phr", ".pin", ".psq", ".pdb", ".pot", ".ptf", ".pto"
    )

    for entry in sorted(os.listdir(databases_dir)):
        entry_path = os.path.join(databases_dir, entry)

        if not os.path.isdir(entry_path):
            continue

        has_database_files = False

        for filename in os.listdir(entry_path):
            if filename.startswith(entry) and filename.endswith(valid_extensions):
                has_database_files = True
                break

        if has_database_files:
            found_databases.append(entry)

    return found_databases


def get_all_database_paths(databases_dir="databases"):
    """
    Return a list of BLAST database prefix paths.
    Example:
    ['databases/db1/db1', 'databases/db2/db2']
    """
    database_names = get_all_database_names(databases_dir)
    return [os.path.join(databases_dir, db_name, db_name) for db_name in database_names]


def list_databases(databases_dir="databases"):
    """
    List database names found inside the databases directory.
    """
    database_names = get_all_database_names(databases_dir)

    if not database_names:
        sys.stdout.write("No BLAST databases were found.\n")
        return

    sys.stdout.write("Available BLAST databases:\n")
    for db_name in database_names:
        sys.stdout.write(f"{db_name}\n")


def load_fasta(file_path):
    """
    Load a FASTA file into a dictionary:
    {sequence_id: sequence}
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Query FASTA file not found: {file_path}")

    sequences = {}
    current_id = None
    seq_lines = []

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


def main():
    args = parse_args()

    if args.list_databases:
        list_databases()
        return

    if args.show_config:
        config = load_config(args.config)
        print_config(config)
        return

    if args.evaluate:
        if not args.ground_truth:
            sys.stderr.write("Error: --evaluate requires --ground_truth.\n")
            sys.exit(1)

        metrics = evaluate_classification_file(
            classification_file=args.evaluate,
            ground_truth_file=args.ground_truth
        )

        print_metrics_report(metrics, title="Evaluation Report")
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
            databases = get_all_database_paths()

        if not databases:
            sys.stderr.write("Error: No BLAST databases available.\n")
            sys.exit(1)

        blast_results = run_blast_across_databases(
            query_sequences=queries,
            databases=databases,
            blast_params=config
        )

        save_results(blast_results, args.query_file)
        return

    sys.stdout.write(
        "No action selected.\n"
        "Use one of the following options:\n"
        "  --list_databases\n"
        "  --show_config [--config <file>]\n"
        "  --db_name <name> --fasta_file <file> --db_type <nucl|prot>\n"
        "  --run_blast --query_file <file> [--db_name <name>] [--config <file>]\n"
        "  --classify <results_file> [--config <file>]\n"
        "  --evaluate <classification_file> --ground_truth <truth_file>\n"
    )


if __name__ == "__main__":
    main()
