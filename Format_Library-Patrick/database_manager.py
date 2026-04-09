#!/usr/bin/env python3
#By Patrick Bircher 

import os
import shutil
import subprocess
import sys


def create_local_database(fasta_path, db_name, db_type):
    """
    Create a local BLAST database from a FASTA file.

    Inputs:
    - fasta_path: Path to the input FASTA file
    - db_name: Name of the database
    - db_type: Type of sequences ('nucl', 'nucleotide', 'prot', 'protein')

    Output:
    - Returns the BLAST database prefix/path if successful
    """
    if not shutil.which("makeblastdb"):
        raise EnvironmentError(
            "makeblastdb not found. Please install the NCBI BLAST+ toolkit:\n"
            "  conda install -c bioconda blast\n"
        )

    db_type = db_type.lower()
    if db_type not in ("nucl", "nucleotide", "prot", "protein"):
        raise ValueError(
            f"Invalid db_type '{db_type}'. Must be 'nucl'/'nucleotide' or 'prot'/'protein'."
        )

    db_type_flag = "nucl" if db_type in ("nucl", "nucleotide") else "prot"

    db_dir = os.path.join("databases", db_name)
    db_prefix = os.path.join(db_dir, db_name)

    if db_type_flag == "nucl":
        extensions = [".nhr", ".nin", ".nsq", ".ndb", ".not", ".ntf", ".nto"]
    else:
        extensions = [".phr", ".pin", ".psq", ".pdb", ".pot", ".ptf", ".pto"]

    db_exists = any(os.path.exists(db_prefix + ext) for ext in extensions)

    if db_exists:
        sys.stdout.write(f"BLAST database '{db_name}' already exists. Skipping creation.\n")
        return db_prefix

    if not os.path.isfile(fasta_path):
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    os.makedirs(db_dir, exist_ok=True)

    fasta_filename = os.path.basename(fasta_path)
    new_fasta_path = os.path.join(db_dir, fasta_filename)

    if os.path.abspath(fasta_path) != os.path.abspath(new_fasta_path):
        shutil.move(fasta_path, new_fasta_path)
        sys.stdout.write(
            f"Moved FASTA file from '{fasta_path}' to '{new_fasta_path}'.\n"
        )
    else:
        sys.stdout.write(f"FASTA file is already in the database directory.\n")

    cmd = [
        "makeblastdb",
        "-in", new_fasta_path,
        "-dbtype", db_type_flag,
        "-out", db_prefix
    ]

    sys.stdout.write(
        f"Creating BLAST database '{db_name}' from '{new_fasta_path}'...\n"
    )

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"makeblastdb failed with return code {result.returncode}.\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

    sys.stdout.write(f"BLAST database '{db_name}' created successfully.\n")
    return db_prefix


def get_database(fasta_path, db_name, db_type):
    """
    Get the BLAST database path. If the database does not exist, create it first.

    Inputs:
    - fasta_path: Path to the FASTA file
    - db_name: Name of the database
    - db_type: Type of sequences ('nucl', 'nucleotide', 'prot', 'protein')

    Output:
    - Returns the BLAST database prefix/path
    """
    db_type = db_type.lower()

    if db_type in ("nucl", "nucleotide"):
        extensions = [".nhr", ".nin", ".nsq", ".ndb", ".not", ".ntf", ".nto"]
    elif db_type in ("prot", "protein"):
        extensions = [".phr", ".pin", ".psq", ".pdb", ".pot", ".ptf", ".pto"]
    else:
        raise ValueError(
            f"Invalid db_type '{db_type}'. Must be 'nucl'/'nucleotide' or 'prot'/'protein'."
        )

    db_dir = os.path.join("databases", db_name)
    db_prefix = os.path.join(db_dir, db_name)

    db_exists = any(os.path.exists(db_prefix + ext) for ext in extensions)

    if db_exists:
        sys.stdout.write(f"Using existing BLAST database '{db_name}'.\n")
        return db_prefix

    sys.stdout.write(f"BLAST database '{db_name}' not found. It will be created now.\n")
    return create_local_database(fasta_path, db_name, db_type)
