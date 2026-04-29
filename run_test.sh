#!/bin/bash

set -e

echo "===== STEP 1: Unzipping dataset ====="
unzip -o databases/H1N1_2025.zip -d databases/

echo "===== STEP 2: Listing databases (before) ====="
python3 main.py --list_databases

echo "===== STEP 3: Creating BLAST database ====="
python3 main.py \
  --db_name H1N1 \
  --fasta_file databases/H1N1_2025.fasta \
  --db_type nucl

echo "===== STEP 4: Listing databases (after) ====="
python3 main.py --list_databases

echo "===== STEP 5: Showing configuration ====="
python3 main.py --show_config

echo "===== STEP 6: Running BLAST ====="
python3 main.py \
  --run_blast \
  --query_file queries/H1N1_Unknown.fasta

echo "===== STEP 7: Classifying results ====="
python3 main.py \
  --classify results/H1N1_Unknown/H1N1_Unknown_results.txt
