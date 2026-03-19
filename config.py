# By Patrick Bircher  

"""
Configuration module for the Multi-Database BLAST Classification Tool.

This file defines all global configuration values used across the project,
including database paths, BLAST parameters, and evaluation settings.

It allows the rest of the codebase to remain modular and flexible by
centralizing adjustable parameters in one place.

Conceptual inputs:
- User-defined paths and parameters (hardcoded or read from a config file)

Conceptual outputs:
- Configuration objects or dictionaries accessed by other modules
"""

def load_config():
    """
    Load and return configuration parameters for the project.

    Inputs:
    - None (or optionally a path to a config file).

    Outputs:
    - A configuration dictionary containing:
      - Paths to BLAST databases
      - Query file path
      - BLAST parameters (e-value, word size, etc.)
      - Evaluation settings

    High-level steps:
    1. Define default configuration values.
    2. Optionally override defaults with user-provided settings.
    3. Return the final configuration structure.
    """
    config = {

        # --- Database Paths ---
        "databases": [
            "/data/blast_dbs/db1",
            "/data/blast_dbs/db2",
        ],

        # --- Query File ---
        "query_file": "/data/queries/input.fasta",

        # --- Output Directory ---
        "output_dir": "/data/results/",

        # --- BLAST Parameters ---
        "blast_params": {
            # Program to use: blastn (nucleotide), blastp (protein), blastx, etc.
            "program": "blastn",

            # E-value threshold: hits with e-value above this are discarded.
            "evalue": 1e-5,

            # Word size: length of initial exact match seed.
            "word_size": 11,

            # Number of threads to use for parallel execution.
            "num_threads": 4,

            # Maximum number of aligned sequences to return per query.
            "max_target_seqs": 10,

            # Output format
            "outfmt": 6,

            # Percent identity threshold
            "perc_identity": 90.0,

            # Minimum query coverage
            "query_coverage": 80.0,
        },

        # --- Evaluation / Classification Settings ---
        "evaluation": {
            # Minimum bit score 
            "min_bitscore": 50,

            # If True, assign the top hit's taxonomy as the classification label.
            "use_top_hit": True,

            # If True, apply a lowest common ancestor strategy
            "use_lca": False,

            # Fraction of top hits to consider when applying LCA (0.0 - 1.0).
            "lca_top_fraction": 0.1,
        },
    }

    return config
