# Running the run_test.sh Script
This script runs a predefined test to verify that the program is working correctly:

# Installation

Make sure BLAST+ is installed:

```bash
conda create -n project_py -c conda-forge -c bioconda blast curl
conda activate project_py
```
Or create the enviroment using the yml 
```bash
conda env create -f environment.yml
conda activate project_py
```
---
# Gives permissions to the run_test.sh and execute run_test.sh 
You can run the test and this will unzip the H1N1 zip, create a database based on the fasta file, run blast againts a H1N1 Unknow query file  and classify it.
```bash
chmod +x run_test.sh
./run_test.sh 
```

---
# Manual Execution Instructions
To run the program manually in a general way, follow these instructions:

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
python3 main.py --db_name H1N1 --fasta_file databases/H1N1_2025.fasta --db_type nucl
```

This will:

* Create `databases/H1N1/`
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

Now we will use the 16S ribosomal RNA database downloaded from NCBI. We will run the analysis manually and use the unknown 16S query as a test case.es

```bash
python3 main.py --run_blast --db_name 16S_ribosomal_RNA --query_file queries/16S_Unknown.fasta
```

## Run against ALL databases

```bash
python3 main.py --run_blast --query_file queries/16S_Unknown.fasta
```

---

# Example Output Structure

```
results/
└── 16S_Unknown/
    └── 16S_Unknown_results.txt
```

---

# Example BLAST Output

```
Query: 16S_Unknown_1
database                subject_id      identity        alignment_length        evalue          bitscore
16S_ribosomal_RNA       NR_042538.1     81.818          187                     2.07e-35        148.0
```

---

# 5. Classification

```bash
python3 main.py --classify results/16S_Unknown/16S_Unknown_results.txt
```

Example Output (console):

```
16S_Unknown_1   NR_042538.1
16S_Unknown_2   NR_156073.1
16S_Unknown_3   NR_156073.1
```

Also generates:

```
results/16S_Unknown/16S_Unknown_classification.txt
```

---

# Full Pipeline Example

```bash

# Download NCBI database
python3 main.py --download_ncbi 16S_ribosomal_RNA

# Create database
python3 main.py --db_name H1N1 --fasta_file databases/H1N1_2025.fasta --db_type nucl

# Run BLAST
python3 main.py --run_blast --query_file queries/16S_Unknown.fasta

# Classify
python3 main.py --classify results/16S_Unknown/16S_Unknown_results.txt

```

---
