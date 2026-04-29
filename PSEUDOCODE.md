
## Main Pipeline

```text
BEGIN main

    PARSE command-line arguments

    IF --list_databases selected THEN
        CALL list_databases()
        STOP
    END IF

    IF --show_config selected THEN
        LOAD configuration from file
        PRINT configuration values
        STOP
    END IF

    IF --download_ncbi selected THEN
        CALL download_ncbi_database(db_name)
        PRINT database path
        STOP
    END IF

    IF --classify selected THEN
        LOAD configuration
        LOAD BLAST results file
        CLASSIFY sequences using thresholds
        SAVE classification file
        PRINT predictions
        STOP
    END IF

    IF database creation mode selected THEN
        VALIDATE db_name, fasta_file, db_type
        CALL get_database(fasta_file, db_name, db_type)
        PRINT database path
        STOP
    END IF

    IF --run_blast selected THEN
        VALIDATE query_file
        LOAD configuration
        LOAD query FASTA sequences

        IF db_name provided THEN
            USE that database only
        ELSE
            LOAD all compatible database paths
        END IF

        IF no databases found THEN
            PRINT error
            STOP
        END IF

        CREATE BlastRunner(config)

        RUN BLAST across databases

        SAVE results to:
            results/<query_name>/<query_name>_results.txt

        STOP
    END IF

    PRINT help message

END main
