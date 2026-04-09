# Multi DB BLAST Classifier
Link to Project: https://github.com/isabellazy/Programming2_FinalProject

## Authors: 
Isabella Zuluaga Yusti - 801427563 - izuluaga@charlotte.edu - isabellazy  
Candelaria Domingo - 801481207 - cdomingo@charlotte.edu - Sci-Glo  
Patrick Bircher - 801490468 - pbircher@charlotte.edu - PBircher  

## Description: 
This project is designed to evaluate an unknown gene sequence compared to a local BLAST database and return possible sequence matches.  

This project implements a modular bioinformatics pipeline to:
1. Create local BLAST databases
2. Run BLAST queries across one or multiple databases
3. Classify sequences based on BLAST hits
4. Evaluate classification performance

---

# Project Structure

```
multi_db_blast_classifier/
├── main.py
├── Format_Library-Patrick/
│   ├── database_manager.py
│   └── config.py
├── BLAST_Library-Isabella/
│   └── blast_runner.py
├── Evaluation_Library-Candelaria/
│   ├── classifier.py
│   ├── evaluation.py
│   └── results_handler.py
├── databases/
├── queries/
├── results/
└── README.md
```

main.py: Entry Point: puts together the entire workflow of the project  
  
config.py: Centralized Configuration: defines all global configuration values used across the project  
  
database_manager.py: Local BLAST Databases: creating, validating, and managing local BLAST databases  
  
blast_runner.py: Running BLAST Searches: running BLAST searches for query sequences against multiple local databases and collecting the raw results  
  
classifier.py: Selecting the Best Hit: interpreting BLAST results and ranking hits across multiple databases  
  
evaluation.py: Accuracy & Performance: measures classification accuracy using known sequences  



## License:
All material are released under GNU GPL License, and can be freely used for both academic and commercial purposes.

## References:
1.) Camacho, C. Building a BLAST database with your (local) sequences. in BLAST® Command Line Applications User Manual [Internet] (National Center for Biotechnology Information (US), 2024).  
2.) NCBI Magic-BLAST : Create a BLAST database. https://ncbi.github.io/magicblast/cook/blastdb.html.  
3.) Altschul SF, Gish W, Miller W, Myers EW, Lipman DJ. Basic local alignment search tool. J Mol Biol. 1990 Oct 5;215(3):403-10. doi: 10.1016/S0022-2836(05)80360-2. PMID: 2231712.  
