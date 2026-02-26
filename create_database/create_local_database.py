import os
import subprocess
import shutil

def create_local_database(fasta_path, db_name, db_type):
    """
    Create a local BLAST database from a FASTA file.
    Inputs:
    - fasta_path: Path to the reference FASTA file.
    - db_name: Name of the BLAST database to be created.
    - db_type: Type of sequences (nucleotide or protein).
    Outputs:
    - A local BLAST database stored on disk.
    """
    #Check Required Dependencies
    if not shutil.which("makeblastdb"):
        raise EnvironmentError(
            "makeblastdb not found. Please install the NCBI BLAST+ toolkit:\n"
            "  conda install -c bioconda blast\n"
            "  or visit https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/"
        )

    # Step 1: Validate db_type
    db_type = db_type.lower()
    if db_type not in ("nucl", "prot", "nucleotide", "protein"):
        raise ValueError(f"Invalid db_type '{db_type}'. Must be 'nucl'/'nucleotide' or 'prot'/'protein'.")  
    db_type_flag = "nucl" if db_type in ("nucl", "nucleotide") else "prot"
    
    # Step 2: Check whether the database already exists
    extensions = [".nhr", ".nsq", ".ndb"] if db_type_flag == "nucl" else [".phr", ".pin", ".psq"]
    db_exists = all(os.path.exists(db_name + ext) for ext in extensions)
    
    if db_exists:
        print(f"BLAST database '{db_name}' already exists. Skipping creation.")
        return

    # Step 3: Validate that the input FASTA file exists
    if not os.path.isfile(fasta_path):
        raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

    # Step 4: build and call appropriate BLAST database command
    cmd = [
        "makeblastdb",
        "-in", fasta_path,
        "-dbtype", db_type_flag,
        "-out", db_name
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Step 5: Verify successful database creation
    if result.returncode != 0:
        raise RuntimeError(
            f"makeblastdb failed with return code {result.returncode}.\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )
    print(f"BLAST database '{db_name}' created successfully.")
if __name__ == "__main__":
    create_local_database(
        fasta_path="reference.fasta",
        db_name="new_blast_db",
        db_type="nucleotide"
    )
