# Programming2_FinalProject
Link to Project: https://github.com/isabellazy/Programming2_FinalProject

## Authors: 
Isabella Zuluaga Yusti - 801427563 - izuluaga@charlotte.edu  
Candelaria Domingo - 801481207 - cdomingo@charlotte.edu  
Patrick Bircher - 801490468 - pbircher@charlotte.edu  

## Description: 
This project is designed to evaluate an unknown gene sequence compared to a local BLAST database, return possible sequence matches, and evaluate the strength of those matches

## Proposed Project Structure:  
Proposed Project Structure:  
multi_db_blast_classifier/     
├── main.py  
├── Format_Library-Patrick  
&nbsp;&nbsp;├── config.py  
&nbsp;&nbsp;├── database_manager.py  
├──BLAST_Library-Isabella  
&nbsp;&nbsp;├── blast_runner.py  
├──Evaluation_Library-Candelaria  
&nbsp;&nbsp;├── classifier.py  
&nbsp;&nbsp;├── evaluation.py  
├── utils.py  
└── README.md  

main.py (Entry Point: puts together the entire workflow of the project)  
config.py (Centralized Configuration: defines all global configuration values used across the project)  
database_manager.py (Local BLAST Databases: creating, validating, and managing local BLAST databases)  
blast_runner.py (Running BLAST Searches: running BLAST searches for query sequences against multiple local databases and collecting the raw results)  
classifier.py (Selecting the Best Hit: interpreting BLAST results and ranking hits across multiple databases)  
evaluation.py: (Accuracy & Performance: measures classification accuracy using known sequences)  



## License:
All material are released under GNU GPL License, and can be freely used for both academic and commercial purposes.

