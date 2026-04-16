#!/usr/bin/env python3
# By Patrick Bircher

"""
database_manager.py

Manages local BLAST databases — either by downloading prebuilt databases
directly from the NCBI FTP server, or by building custom databases from
local FASTA files using makeblastdb.

Classes:
    DatabaseManager: Handles all database creation, retrieval, and downloading.

Typical usage:
    manager = DatabaseManager()
    db_path = manager.download_ncbi("16S_ribosomal_RNA")
    db_path = manager.create_from_fasta("seqs.fasta", "my_db", "nucleotide")
    db_path = manager.get_database("seqs.fasta", "my_db", "nucleotide")
"""

import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from typing import Optional


# ---------------------------------------------------------------------------
# Supported NCBI BLAST databases
# ---------------------------------------------------------------------------

NCBI_DATABASES: dict[str, dict[str, str]] = {
    # Nucleotide
    "nt":                {"type": "nucl", "description": "NCBI nucleotide collection (broad first-pass screening)"},
    "refseq_rna":        {"type": "nucl", "description": "NCBI RefSeq RNA sequences"},
    "refseq_select":     {"type": "nucl", "description": "High-quality curated RefSeq subset"},
    "16S_ribosomal_RNA": {"type": "nucl", "description": "16S rRNA (bacterial species ID)"},
    "patnt":             {"type": "nucl", "description": "Patent nucleotide sequences"},
    # Protein
    "nr":                {"type": "prot", "description": "NCBI non-redundant protein collection"},
    "swissprot":         {"type": "prot", "description": "UniProt/Swiss-Prot curated proteins"},
    "pataa":             {"type": "prot", "description": "Patent protein sequences"},
}

# File extensions for nucleotide and protein BLAST databases
NUCL_EXTENSIONS: list[str] = [".nhr", ".nin", ".nsq", ".ndb", ".not", ".ntf", ".nto"]
PROT_EXTENSIONS: list[str] = [".phr", ".pin", ".psq", ".pdb", ".pot", ".ptf", ".pto"]

# Base URL for NCBI BLAST database FTP downloads
NCBI_FTP_BASE_URL: str = "https://ftp.ncbi.nlm.nih.gov/blast/db"


# ---------------------------------------------------------------------------
# DatabaseManager class
# ---------------------------------------------------------------------------

class DatabaseManager:
    """
    Manages local BLAST databases.

    Supports downloading prebuilt NCBI databases and building custom
    databases from local FASTA files using makeblastdb.

    Attributes:
        download_dir (str): Directory where databases are stored.
    """

    def __init__(self, download_dir: str = "databases") -> None:
        """
        Initialize the DatabaseManager.

        Args:
            download_dir (str): Directory to store all databases.
                                Defaults to 'databases'.
        """
        self.download_dir = download_dir

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _check_blast_installed(self) -> None:
        """
        Verify that makeblastdb is available on the system PATH.

        Raises:
            EnvironmentError: If makeblastdb is not found.
        """
        if not shutil.which("makeblastdb"):
            raise EnvironmentError(
                "makeblastdb not found. Please install the NCBI BLAST+ toolkit:\n"
                "  conda install -c bioconda blast\n"
                "  or visit https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/"
            )

    def _normalize_db_type(self, db_type: str) -> str:
        """
        Validate and normalize db_type to BLAST shorthand ('nucl' or 'prot').

        Args:
            db_type (str): Database type string, e.g. 'nucleotide', 'nucl',
                           'protein', or 'prot'.

        Returns:
            str: Normalized type flag, either 'nucl' or 'prot'.

        Raises:
            ValueError: If db_type is not a recognized value.
        """
        db_type = db_type.lower()
        if db_type not in ("nucl", "nucleotide", "prot", "protein"):
            raise ValueError(
                f"Invalid db_type '{db_type}'. "
                "Must be 'nucl'/'nucleotide' or 'prot'/'protein'."
            )
        return "nucl" if db_type in ("nucl", "nucleotide") else "prot"

    def _get_extensions(self, db_type_flag: str) -> list[str]:
        """
        Return the expected file extensions for a given database type.

        Args:
            db_type_flag (str): Normalized database type, 'nucl' or 'prot'.

        Returns:
            list[str]: List of expected file extensions.
        """
        return NUCL_EXTENSIONS if db_type_flag == "nucl" else PROT_EXTENSIONS

    def _db_exists(self, db_prefix: str, db_type_flag: str) -> bool:
        """
        Check whether all expected database files exist on disk.

        Args:
            db_prefix (str):    Full path prefix of the database
                                (e.g. 'databases/my_db/my_db').
            db_type_flag (str): Normalized database type, 'nucl' or 'prot'.

        Returns:
            bool: True if all expected files are present, False otherwise.
        """
        extensions = self._get_extensions(db_type_flag)
        return all(os.path.exists(db_prefix + ext) for ext in extensions)

    def _db_prefix(self, db_name: str) -> tuple[str, str]:
        """
        Construct the database directory and prefix path.

        Args:
            db_name (str): Name of the database.

        Returns:
            tuple[str, str]: (db_dir, db_prefix) where db_dir is the
                             database folder and db_prefix is the full
                             path prefix used by BLAST.
        """
        db_dir = os.path.join(self.download_dir, db_name)
        db_prefix = os.path.join(db_dir, db_name)
        return db_dir, db_prefix

    @staticmethod
    def _download_progress(block_num: int, block_size: int, total_size: int) -> None:
        """
        Print a download progress bar to stdout.

        Args:
            block_num (int):  Current block number being downloaded.
            block_size (int): Size of each block in bytes.
            total_size (int): Total file size in bytes.
        """
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100.0, downloaded * 100 / total_size)
            mb_done = downloaded / 1_000_000
            mb_total = total_size / 1_000_000
            sys.stdout.write(f"\r  {percent:.1f}%  {mb_done:.1f} / {mb_total:.1f} MB")
            sys.stdout.flush()

    # -----------------------------------------------------------------------
    # Public methods
    # -----------------------------------------------------------------------

    def create_from_fasta(
        self,
        fasta_path: str,
        db_name: str,
        db_type: str,
    ) -> str:
        """
        Create a local BLAST database from a FASTA file using makeblastdb.

        The FASTA file is moved into the database directory before
        the database is built. If the database already exists, creation
        is skipped.

        Args:
            fasta_path (str): Path to the input FASTA file.
            db_name (str):    Name to give the resulting database.
            db_type (str):    Type of sequences in the FASTA file.
                              Accepts 'nucl', 'nucleotide', 'prot', or 'protein'.

        Returns:
            str: Path prefix of the created BLAST database.

        Raises:
            EnvironmentError: If makeblastdb is not installed.
            FileNotFoundError: If the FASTA file does not exist.
            RuntimeError: If makeblastdb exits with a non-zero return code.
        """
        self._check_blast_installed()

        db_type_flag = self._normalize_db_type(db_type)
        db_dir, db_prefix = self._db_prefix(db_name)

        if self._db_exists(db_prefix, db_type_flag):
            sys.stdout.write(
                f"BLAST database '{db_name}' already exists. Skipping creation.\n"
            )
            return db_prefix

        if not os.path.isfile(fasta_path):
            raise FileNotFoundError(f"FASTA file not found: {fasta_path}")

        os.makedirs(db_dir, exist_ok=True)

        # Move FASTA file into the database directory
        fasta_filename = os.path.basename(fasta_path)
        new_fasta_path = os.path.join(db_dir, fasta_filename)

        if os.path.abspath(fasta_path) != os.path.abspath(new_fasta_path):
            shutil.move(fasta_path, new_fasta_path)
            sys.stdout.write(
                f"Moved FASTA file from '{fasta_path}' to '{new_fasta_path}'.\n"
            )
        else:
            sys.stdout.write("FASTA file is already in the database directory.\n")

        cmd: list[str] = [
            "makeblastdb",
            "-in",     new_fasta_path,
            "-dbtype", db_type_flag,
            "-out",    db_prefix,
        ]

        sys.stdout.write(
            f"Creating BLAST database '{db_name}' from '{new_fasta_path}'...\n"
        )
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(
                f"makeblastdb failed with return code {result.returncode}.\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        sys.stdout.write(f"BLAST database '{db_name}' created successfully.\n")
        return db_prefix

    def get_database(
        self,
        fasta_path: str,
        db_name: str,
        db_type: str,
    ) -> str:
        """
        Return the path to a BLAST database, creating it first if needed.

        If the database already exists on disk, returns its path immediately.
        Otherwise, builds it from the provided FASTA file.

        Args:
            fasta_path (str): Path to the FASTA file used to create the
                              database if it does not already exist.
            db_name (str):    Name of the database to use or create.
            db_type (str):    Type of sequences. Accepts 'nucl', 'nucleotide',
                              'prot', or 'protein'.

        Returns:
            str: Path prefix of the BLAST database.
        """
        db_type_flag = self._normalize_db_type(db_type)
        _, db_prefix = self._db_prefix(db_name)

        if self._db_exists(db_prefix, db_type_flag):
            sys.stdout.write(f"Using existing BLAST database '{db_name}'.\n")
            return db_prefix

        sys.stdout.write(f"BLAST database '{db_name}' not found. Creating now...\n")
        return self.create_from_fasta(fasta_path, db_name, db_type)

    def download_ncbi(
        self,
        db_name: str,
        download_dir: Optional[str] = None,
    ) -> str:
        """
        Download a prebuilt NCBI BLAST database from the NCBI FTP server.

        Downloads the compressed archive, extracts it, and removes the
        archive file. Skips download if the database already exists.

        Args:
            db_name (str):           Name of the NCBI database to download.
                                     Must be a key in NCBI_DATABASES.
            download_dir (str|None): Directory to store the database.
                                     Defaults to self.download_dir.

        Returns:
            str: Path prefix of the downloaded BLAST database.

        Raises:
            ValueError:   If db_name is not a recognized NCBI database.
            RuntimeError: If the download or extraction fails, or if
                          expected files are missing after extraction.

        Available databases:
            Nucleotide: nt, refseq_rna, refseq_select, 16S_ribosomal_RNA, patnt
            Protein:    nr, swissprot, pataa
        """
        if db_name not in NCBI_DATABASES:
            valid = "\n  ".join(
                f"{k}: {v['description']}" for k, v in NCBI_DATABASES.items()
            )
            raise ValueError(
                f"Unknown database '{db_name}'. Available databases:\n  {valid}"
            )

        target_dir = download_dir or self.download_dir
        db_info = NCBI_DATABASES[db_name]
        db_type_flag: str = db_info["type"]

        os.makedirs(target_dir, exist_ok=True)
        db_prefix = os.path.join(target_dir, db_name)

        if self._db_exists(db_prefix, db_type_flag):
            sys.stdout.write(
                f"Database '{db_name}' already exists in '{target_dir}'. "
                "Skipping download.\n"
            )
            return db_prefix

        sys.stdout.write(
            f"Downloading '{db_name}' ({db_info['description']}) from NCBI FTP...\n"
        )
        if db_name in ("nt", "nr"):
            sys.stdout.write(
                "Note: 'nt' and 'nr' are 100GB+. This may take a very long time.\n"
            )

        filename: str = f"{db_name}.tar.gz"
        url: str = f"{NCBI_FTP_BASE_URL}/{filename}"
        archive_path: str = os.path.join(target_dir, filename)

        # Step 1: Download
        sys.stdout.write(f"Fetching: {url}\n")
        try:
            urllib.request.urlretrieve(url, archive_path, reporthook=self._download_progress)
            sys.stdout.write("\n")
        except Exception as e:
            raise RuntimeError(f"Download failed: {e}")

        # Step 2: Extract
        sys.stdout.write(f"Extracting '{filename}'...\n")
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=target_dir)
        except Exception as e:
            raise RuntimeError(f"Extraction failed: {e}")

        # Step 3: Clean up archive
        os.remove(archive_path)
        sys.stdout.write(f"Cleaned up '{filename}'.\n")

        # Step 4: Verify
        if not self._db_exists(db_prefix, db_type_flag):
            extracted = os.listdir(target_dir)
            raise RuntimeError(
                f"Extraction succeeded but expected database files not found.\n"
                f"Files in '{target_dir}': {extracted}"
            )

        sys.stdout.write(f"Database '{db_name}' ready at '{db_prefix}'.\n")
        return db_prefix


# ---------------------------------------------------------------------------
# Module-level convenience functions (used by main.py imports)
# ---------------------------------------------------------------------------

def create_local_database(fasta_path: str, db_name: str, db_type: str) -> str:
    """
    Module-level wrapper around DatabaseManager.create_from_fasta.

    Args:
        fasta_path (str): Path to the input FASTA file.
        db_name (str):    Name of the database to create.
        db_type (str):    Type of sequences ('nucl', 'nucleotide', 'prot', 'protein').

    Returns:
        str: Path prefix of the created BLAST database.
    """
    return DatabaseManager().create_from_fasta(fasta_path, db_name, db_type)


def get_database(fasta_path: str, db_name: str, db_type: str) -> str:
    """
    Module-level wrapper around DatabaseManager.get_database.

    Args:
        fasta_path (str): Path to the FASTA file (used only if DB does not exist).
        db_name (str):    Name of the database to use or create.
        db_type (str):    Type of sequences ('nucl', 'nucleotide', 'prot', 'protein').

    Returns:
        str: Path prefix of the BLAST database.
    """
    return DatabaseManager().get_database(fasta_path, db_name, db_type)


def download_ncbi_database(db_name: str, download_dir: str = "databases") -> str:
    """
    Module-level wrapper around DatabaseManager.download_ncbi.

    Args:
        db_name (str):      Name of the NCBI database to download.
        download_dir (str): Directory to store the database. Defaults to 'databases'.

    Returns:
        str: Path prefix of the downloaded BLAST database.
    """
    return DatabaseManager(download_dir=download_dir).download_ncbi(db_name)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    manager = DatabaseManager()
 
    # Download a prebuilt NCBI database
    db_path = manager.download_ncbi("16S_ribosomal_RNA")
 
    # Build from a local FASTA file
    # db_path = manager.create_from_fasta("my_sequences.fasta", "my_db", "nucleotide")
 
    # Use existing or create if missing
    # db_path = manager.get_database("my_sequences.fasta", "my_db", "nucleotide")
 
    print(f"Database ready at: {db_path}")