#!/usr/bin/env python3

'''
Database Creation:
This file will be used to create the BLAST database to compare sequences to as the reference
It will take in a fasta file with many reference sequence and organize them as a local BLAST database for the rest of the pipeline to be run against. 
'''
import sys


def create_database():
    '''
Purpose:
    create searchable BLAST databse
Input:
    database_location (str): path to database location
    database_sequences.fasta: sequences for database to built from
Output:
    BLAST database stored on local disk
    a list of validated database paths
High Level Steps:
    1.)Read sequences from fasta file
    2.) call appropriate BLAST database creation command based on sequence
    3.) create local BLAST database from fasta sequences
    4.) Verify databases were created correctly and return database references 
  '''
pass

if __name__ == "__create_databse___":
    create_database()
