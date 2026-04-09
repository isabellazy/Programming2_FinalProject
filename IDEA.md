# Final Project for Programming II

## **Multi-Database Local BLAST Classification Tool**

Build a tool that identifies unknown sequences by comparing them against multiple local BLAST databases.

## Core functionality:

- Create one or more local sequence databases.
- Accept a multi-sequence query file.
- Run each query sequence against **multiple target databases**.
- Identify and rank the best hit across all databases.
- Assign a likely identity or category to each query sequence.  

------

## General Explanation:
This project focuses on building a computational tool that identifies unknown biological sequences by comparing them against multiple local BLAST databases. The tool will automate classification by evaluating each sequence’s best match across several reference datasets, allowing for a more robust and comprehensive identification approach.  

## Objective:
To develop a sequence-classification tool capable of evaluating unknown sequences against multiple BLAST databases, selecting the strongest match, and accurately assigning a predicted identity or category.  

## Outcomes: 
- A working BLAST-based classification tool capable of processing many sequences and selecting the best match across multiple databases.
- An analysis of how different databases or BLAST parameters (e.g., e-value thresholds, word size) influence classification results.
- A modular framework that can be expanded with additional databases or adapted for different organisms or sequence types.
