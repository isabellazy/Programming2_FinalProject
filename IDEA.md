# Final Project for Programming II

## **Multi-Database Local BLAST Classification Tool**

Build a tool that identifies unknown sequences by comparing them against multiple local BLAST databases.

## Core functionality:

- Create one or more local sequence databases.
- Accept a multi-sequence query file.
- Run each query sequence against **multiple target databases**.
- Identify and rank the best hit across all databases.
- Assign a likely identity or category to each query sequence.

The project should include a strategy to **measure classification accuracy** and discuss how performance changes with different databases or parameters.

------

## General Explanation:
This project focuses on building a computational tool that identifies unknown biological sequences by comparing them against multiple local BLAST databases. The tool will automate classification by evaluating each sequence’s best match across several reference datasets, allowing for a more robust and comprehensive identification approach. The project will also incorporate a method to measure classification accuracy and analyze how performance changes based on the databases used or BLAST parameters selected.

## Objective:
To develop a sequence-classification tool capable of evaluating unknown sequences against multiple BLAST databases, selecting the strongest match, and accurately assigning a predicted identity or category. The project also aims to quantify classification accuracy and evaluate how performance varies depending on database composition and BLAST settings.



## Outcomes: 
- A working BLAST-based classification tool capable of processing many sequences and selecting the best match across multiple databases.
- A performance report showing classification accuracy, including confusion matrix or accuracy metrics when testing known sequences.
- An analysis of how different databases or BLAST parameters (e.g., e-value thresholds, word size) influence classification results.
- A modular framework that can be expanded with additional databases or adapted for different organisms or sequence types.
