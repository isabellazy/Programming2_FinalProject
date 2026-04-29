# Installation

Make sure BLAST+ is installed:

```bash
conda create -n python_project -c conda-forge -c bioconda blast curl
conda activate python_project
```

---

# 1. List Available Databases

```bash
python3 main.py --list_databases
```

Example Output:

```
Available BLAST databases:
db1
db2
```

---
# 2. Download an NCBI Database

```bash
python3 main.py --download_ncbi 16S_ribosomal_RNA
```
This will:

* Create databases/16S_ribosomal_RNA/
* Download the database from NCBI
* Extract all BLAST files inside that folder
---
# 3. Create or Use a Database

```bash
python3 main.py --db_name db1 --fasta_file databases/db1.fasta --db_type nucl
```

This will:

* Create `databases/db1/`
* Move the FASTA into the directory
* Generate BLAST index files

---

# 4. View Configuration

```bash
python3 main.py --show_config
```

Or with custom config (you need to upload new configuration file):

```bash
python3 main.py --show_config --config my_config.txt
```

---

# 5. Run BLAST

## Run against one database

```bash
python3 main.py --run_blast --db_name db1 --query_file queries/query1.fasta
```

## Run against ALL databases

```bash
python3 main.py --run_blast --query_file queries/query1.fasta
```

---

# Example Output Structure

```
results/
└── q1/
    └── q1_results.txt
```

---

# Example BLAST Output

```
Query: query_match_bacteria
db1	seq_bacteria_1	100.0	35	5.41e-17	65.8
```

---

# 5. Classification

```bash
python3 main.py --classify results/query1/query1_results.txt
```

Example Output (console):

```
query_match_bacteria	seq_bacteria_1
query_match_virus	seq_virus_1
```

Also generates:

```
results/query1/query1_classification.txt
```

---

# Full Pipeline Example

```bash

# Download NCBI database
python3 main.py --download_ncbi 16S_ribosomal_RNA

# Create database
python3 main.py --db_name db1 --fasta_file databases/db1.fasta --db_type nucl

# Run BLAST
python3 main.py --run_blast --query_file queries/query1.fasta

# Classify
python3 main.py --classify results/query1/query1_results.txt

```

---
