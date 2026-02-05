main.py

"""
Main entry point for the Multi-Database Local BLAST Classification Tool.

This script orchestrates the entire workflow of the project.
It coordinates database preparation, BLAST execution, result aggregation,
sequence classification, and performance evaluation.

This file does not implement the core logic itself; instead, it connects
the different modules of the project into a single executable pipeline.

Conceptual inputs:
- A multi-sequence query FASTA file
- Configuration parameters (databases, BLAST settings)

Conceptual outputs:
- Classification results for each query sequence
- Performance metrics and summary reports
"""

def main():
    """
    Coordinate the full BLAST-based classification workflow.

    Inputs:
    - None directly (configuration and file paths are read from config files
      or command-line arguments).

    Outputs:
    - Writes classification results to disk.
    - Writes performance evaluation metrics to disk or prints them to screen.

    High-level steps:
    1. Load configuration parameters (databases, BLAST options, file paths).
    2. Ensure all local BLAST databases are created and available.
    3. Load the query sequences from a multi-FASTA file.
    4. Run each query sequence against all configured BLAST databases.
    5. Collect and normalize BLAST results across databases.
    6. Identify the best hit for each query sequence.
    7. Assign a predicted identity or category to each query.
    8. If ground truth labels exist, evaluate classification accuracy.
    9. Save results and evaluation summaries.
    """
    pass