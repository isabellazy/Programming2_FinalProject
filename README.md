# Multi DB BLAST Classifier
Link to Project: https://github.com/isabellazy/Programming2_FinalProject

## Authors: 
Isabella Zuluaga Yusti - 801427563 - izuluaga@charlotte.edu - isabellazy  
Candelaria Domingo - 801481207 - cdomingo@charlotte.edu - Sci-Glo  
Patrick Bircher - 801490468 - pbircher@charlotte.edu - PBircher  

---

## Description: 
This project is designed to evaluate an unknown gene sequence compared to a local BLAST database and return possible sequence matches.  

This project implements a modular bioinformatics pipeline to:
1. Create local BLAST databases
2. Run BLAST queries across one or multiple databases
3. Classify sequences based on BLAST hits

---

# Project Structure

```
multi_db_blast_classifier/
├── main.py
├── Format_Library-Patrick/
│   ├── database_manager.py
│   │── file_handler.py
│   │── blast_config.txt
│   └── config.py
├── BLAST_Library-Isabella/
│   └── blast_runner.py
├── Evaluation_Library-Candelaria/
│   ├── classifier.py
│   └── results_handler.py
├── databases/
├── queries/
├── results/
├── run_test.sh
└── README.md
```

- main.py: Entry Point: puts together the entire workflow of the project  
- database_manager.py: Local BLAST Databases: creating, validating, managing local BLAST databases, and downloading supported NCBI BLAST databases  
- config.py: Centralized Configuration: defines all global configuration values used across the project  
- blast_config.txt: Configuration File: stores BLAST parameters such as program, e-value, word size, and other options  
- file_handler.py: Input File Handling: loads FASTA query files into dictionaries for the pipeline  
- blast_runner.py: Running BLAST Searches: runs BLAST searches for query sequences against multiple local databases and collects the raw results using the BlastRunner class  
- classifier.py: Selecting the Best Hit: interprets BLAST results and ranks hits across multiple databases  
- results_handler.py: Results Output Management: saves BLAST search results into the structured results/ directory  


---

## License:
All material is released under GNU GPL License, and can be freely used for both academic and commercial purposes.

---

## References:
Altschul SF, Gish W, Miller W, Myers EW, Lipman DJ. Basic local alignment search tool. J Mol Biol. 1990 Oct 5;215(3):403-10. doi: 10.1016/S0022-2836(05)80360-2. PMID: 2231712.  

Camacho, C. Building a BLAST database with your (local) sequences. in BLAST® Command Line Applications User Manual [Internet] (National Center for Biotechnology Information (US), 2024).  

NCBI Magic-BLAST : Create a BLAST database. https://ncbi.github.io/magicblast/cook/blastdb.html.  
