# Installation

Make sure BLAST+ is installed:

```bash
conda install -c bioconda blast
```

---

# 1. List Available Databases

```bash
python3 main.py --list_databases
```

Output:

```
Available BLAST databases:
db1
db2
```

---

# 2. Create or Use a Database

```bash
python3 main.py --db_name db1 --fasta_file databases/db1.fasta --db_type nucl
```

This will:

* Create `databases/db1/`
* Move the FASTA into the directory
* Generate BLAST index files

---

# 3. View Configuration

```bash
python3 main.py --show_config
```

Or with custom config:

```bash
python3 main.py --show_config --config my_config.txt
```

---

# 4. Run BLAST

## Run against one database

```bash
python3 main.py --run_blast --db_name db1 --query_file queries/query1.fasta
```

## Run against ALL databases

```bash
python3 main.py --run_blast --query_file queries/query1.fasta
```

---

# Output Structure

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

Output (console):

```
query_match_bacteria	seq_bacteria_1
query_match_virus	seq_virus_1
```

Also generates:

```
results/query1/query1_classification.txt
```

---

# 6. Evaluation

Requires a ground truth file:

```
query_match_bacteria	seq_bacteria_1
query_match_virus	seq_virus_1
query_no_match	Unclassified
```

Run:

```bash
python3 main.py --evaluate results/query1/query1_classification.txt --ground_truth Evaluation_Library-Candelaria/truth_labels.txt
```

---

# Example Evaluation Output

```
=======================================================
  Classification Report
=======================================================
  Overall accuracy : 0.6667 (2/3)
  Macro F1         : 0.6667
  Weighted F1      : 0.6667
```

---

# Full Pipeline Example

```bash
# Create database
python3 main.py --db_name db1 --fasta_file databases/db1.fasta --db_type nucl

# Run BLAST
python3 main.py --run_blast --query_file queries/query1.fasta

# Classify
python3 main.py --classify results/query1/query1_results.txt

# Evaluate
python3 main.py --evaluate results/query1/query1_classification.txt --ground_truth Evaluation_Library-Candelaria/truth_labels.txt
```

---
