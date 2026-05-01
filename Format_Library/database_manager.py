#!/usr/bin/env python3
# By Patrick Bircher

"""
database_manager.py

Manages local BLAST databases — either by downloading prebuilt databases
directly from the NCBI FTP server, or by building custom databases from
local FASTA files using makeblastdb.

This merged version keeps:
- the class-based design for structure and extensibility
- the function-based wrappers used by main.py
- the practical project workflow:
    * create databases inside databases/<db_name>/
    * move FASTA files into the database directory
    * reuse existing databases if already present
    * download NCBI databases into their own folders
    * support both single-part and multi-part NCBI BLAST databases

Classes:
    DatabaseManager: Handles database creation, retrieval, and downloading.

Typical usage:
    manager = DatabaseManager()
    db_path = manager.get_database("seqs.fasta", "my_db", "nucleotide")

Functional usage:
    db_path = get_database("seqs.fasta", "my_db", "nucleotide")
"""

import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
import re


# ---------------------------------------------------------------------------
# Supported NCBI BLAST databases
# ---------------------------------------------------------------------------

NCBI_DATABASES: dict[str, dict[str, str]] = {
    # Nucleotide
    "refseq_rna":        {"type": "nucl", "description": "NCBI RefSeq RNA sequences"},
    "16S_ribosomal_RNA": {"type": "nucl", "description": "16S rRNA (bacterial species ID)"},
    "patnt":             {"type": "nucl", "description": "Patent nucleotide sequences"},
    # Protein
    "swissprot":         {"type": "prot", "description": "UniProt/Swiss-Prot curated proteins"},
    "pataa":             {"type": "prot", "description": "Patent protein sequences"},
}

# File extensions for nucleotide and protein BLAST databases
NUCL_EXTENSIONS: list[str] = [
    ".nhr", ".nin", ".nsq", ".ndb", ".not", ".ntf", ".nto",
    ".nog", ".nos", ".njs", ".nsi", ".nsd"
]

PROT_EXTENSIONS: list[str] = [
    ".phr", ".pin", ".psq", ".pdb", ".pot", ".ptf", ".pto",
    ".ppi", ".ppd", ".pjs", ".pog", ".pos"
]

# Base URL for NCBI BLAST database FTP downloads
NCBI_FTP_BASE_URL: str = "https://ftp.ncbi.nlm.nih.gov/blast/db"


# ---------------------------------------------------------------------------
# DatabaseManager class
# ---------------------------------------------------------------------------

class DatabaseManager:
    """
    Manages local BLAST databases.

    Supports:
    - downloading prebuilt NCBI databases
    - building custom databases from local FASTA files using makeblastdb
    - reusing existing local databases when they already exist

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
        Check whether the BLAST database files exist on disk.

        Args:
            db_prefix (str):    Full path prefix of the database
                                (e.g. 'databases/my_db/my_db').
            db_type_flag (str): Normalized database type, 'nucl' or 'prot'.

        Returns:
            bool: True if the database is present, False otherwise.
        """
        extensions = self._get_extensions(db_type_flag)
        return any(os.path.exists(db_prefix + ext) for ext in extensions)

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

    def _downloaded_db_exists(self, db_name: str, db_type_flag: str, db_dir: str) -> bool:
        """
        Check whether a downloaded NCBI BLAST database exists.

        Supports:
        - alias files (.nal/.pal)
        - single-volume BLAST files (e.g. swissprot.phr)
        - multi-volume BLAST files (e.g. nt.000.nhr)

        Args:
            db_name (str): Database name.
            db_type_flag (str): Normalized database type, 'nucl' or 'prot'.
            db_dir (str): Directory where the downloaded database is stored.

        Returns:
            bool: True if downloaded BLAST files are detected, False otherwise.
        """
        if not os.path.isdir(db_dir):
            return False

        files = os.listdir(db_dir)

        if db_type_flag == "nucl":
            alias_ext = "nal"
            extensions = [ext.lstrip(".") for ext in NUCL_EXTENSIONS]
        else:
            alias_ext = "pal"
            extensions = [ext.lstrip(".") for ext in PROT_EXTENSIONS]

        ext_pattern = "|".join(re.escape(ext) for ext in extensions)

        pattern = rf"^{re.escape(db_name)}(\.{alias_ext}|\.(?:{ext_pattern})|\.\d+\.(?:{ext_pattern}))$"
        regex = re.compile(pattern)

        return any(regex.match(filename) for filename in files)

    def _url_exists(self, url: str) -> bool:
        """
        Check whether a remote URL exists.

        Uses curl if available, otherwise urllib.

        Args:
            url (str): URL to test.

        Returns:
            bool: True if the URL exists, False otherwise.
        """
        try:
            if shutil.which("curl"):
                cmd = ["curl", "-I", "-L", "-s", url]
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                return "200 OK" in result.stdout
            else:
                request = urllib.request.Request(url, method="HEAD")
                with urllib.request.urlopen(request):
                    return True
        except Exception:
            return False

    def _download_archive(self, url: str, archive_path: str) -> None:
        """
        Download one archive file using curl if available, otherwise urllib.

        Args:
            url (str): Remote file URL.
            archive_path (str): Local output path.

        Raises:
            RuntimeError: If the download fails.
        """
        sys.stdout.write(f"Fetching: {url}\n")

        try:
            if shutil.which("curl"):
                sys.stdout.write("Using curl for download.\n")
                cmd = ["curl", "-L", url, "-o", archive_path]
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)

                if result.returncode != 0:
                    raise RuntimeError(
                        f"curl download failed with return code {result.returncode}.\n"
                        f"STDOUT:\n{result.stdout}\n"
                        f"STDERR:\n{result.stderr}"
                    )
            else:
                sys.stdout.write("Using urllib for download.\n")
                urllib.request.urlretrieve(
                    url,
                    archive_path,
                    reporthook=self._download_progress
                )
                sys.stdout.write("\n")

        except Exception as e:
            raise RuntimeError(
                "Download failed. Python SSL may not trust the certificate chain in this environment.\n"
                "A curl-based download is recommended on this system.\n"
                f"Original error: {e}"
            )

    def _extract_archive(self, archive_path: str, db_dir: str) -> None:
        """
        Extract one .tar.gz archive into the database directory.

        Args:
            archive_path (str): Path to archive file.
            db_dir (str): Target extraction directory.

        Raises:
            RuntimeError: If extraction fails.
        """
        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=db_dir)
        except Exception as e:
            raise RuntimeError(f"Extraction failed for '{archive_path}': {e}")

    def _download_singlepart_database(self, db_name: str, db_dir: str) -> None:
        """
        Download and extract a single-part NCBI BLAST database archive.

        Args:
            db_name (str): Database name.
            db_dir (str): Local database directory.
        """
        filename = f"{db_name}.tar.gz"
        url = f"{NCBI_FTP_BASE_URL}/{filename}"
        archive_path = os.path.join(db_dir, filename)

        self._download_archive(url, archive_path)
        sys.stdout.write(f"Extracting '{filename}' into '{db_dir}'...\n")
        self._extract_archive(archive_path, db_dir)
        os.remove(archive_path)
        sys.stdout.write(f"Cleaned up '{filename}'.\n")

    def _download_multipart_database(self, db_name: str, db_dir: str) -> None:
        """
        Download and extract a multi-part NCBI BLAST database.

        Example:
            refseq_rna.00.tar.gz
            refseq_rna.01.tar.gz
            ...

        Args:
            db_name (str): Database name.
            db_dir (str): Local database directory.

        Raises:
            RuntimeError: If no parts are found.
        """
        part_index = 0
        downloaded_any = False

        while True:
            part_name = f"{db_name}.{part_index:02d}.tar.gz"
            url = f"{NCBI_FTP_BASE_URL}/{part_name}"

            if not self._url_exists(url):
                if part_index == 0:
                    raise RuntimeError(
                        f"No single-part or multi-part archives were found for database '{db_name}'."
                    )
                break

            archive_path = os.path.join(db_dir, part_name)

            self._download_archive(url, archive_path)
            sys.stdout.write(f"Extracting '{part_name}' into '{db_dir}'...\n")
            self._extract_archive(archive_path, db_dir)
            os.remove(archive_path)
            sys.stdout.write(f"Cleaned up '{part_name}'.\n")

            downloaded_any = True
            part_index += 1

        if not downloaded_any:
            raise RuntimeError(f"No archive parts were downloaded for '{db_name}'.")

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
            "-in", new_fasta_path,
            "-dbtype", db_type_flag,
            "-out", db_prefix,
        ]

        sys.stdout.write(
            f"Creating BLAST database '{db_name}' from '{new_fasta_path}'...\n"
        )
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

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

    def download_ncbi(self, db_name: str) -> str:
        """
        Download a prebuilt NCBI BLAST database from the NCBI FTP server.

        The downloaded database is always stored inside:
            databases/<db_name>/

        Supports:
        - single-part archives: db_name.tar.gz
        - multi-part archives: db_name.00.tar.gz, db_name.01.tar.gz, ...

        Args:
            db_name (str): Name of the NCBI database to download.

        Returns:
            str: Path prefix of the downloaded BLAST database.

        Raises:
            ValueError:   If db_name is not a recognized NCBI database.
            RuntimeError: If the download or extraction fails, or if
                          expected files are missing after extraction.
        """
        if db_name not in NCBI_DATABASES:
            valid = "\n  ".join(
                f"{k}: {v['description']}" for k, v in NCBI_DATABASES.items()
            )
            raise ValueError(
                f"Unknown database '{db_name}'. Available databases:\n  {valid}"
            )

        db_dir, db_prefix = self._db_prefix(db_name)
        db_info = NCBI_DATABASES[db_name]
        db_type_flag: str = db_info["type"]

        os.makedirs(db_dir, exist_ok=True)

        if self._downloaded_db_exists(db_name, db_type_flag, db_dir):
            sys.stdout.write(
                f"Database '{db_name}' already exists in '{db_dir}'. Skipping download.\n"
            )
            return db_prefix

        sys.stdout.write(
            f"Downloading '{db_name}' ({db_info['description']}) from NCBI FTP...\n"
        )

        if db_name in ("nt", "nr", "refseq_rna"):
            sys.stdout.write(
                "Note: this database may be very large and may require multiple downloads.\n"
            )

        single_url = f"{NCBI_FTP_BASE_URL}/{db_name}.tar.gz"

        if self._url_exists(single_url):
            self._download_singlepart_database(db_name, db_dir)
        else:
            self._download_multipart_database(db_name, db_dir)

        if not self._downloaded_db_exists(db_name, db_type_flag, db_dir):
            extracted = os.listdir(db_dir)
            raise RuntimeError(
                f"Extraction succeeded but expected database files not found.\n"
                f"Files in '{db_dir}': {extracted}"
            )

        sys.stdout.write(f"Database '{db_name}' ready at '{db_prefix}'.\n")
        return db_prefix

    def get_all_database_names(self) -> list[str]:
        """
        Return a list of all available BLAST database names in self.download_dir.
        """
        if not os.path.isdir(self.download_dir):
            return []

        found_databases: list[str] = []

        for entry in sorted(os.listdir(self.download_dir)):
            entry_path = os.path.join(self.download_dir, entry)

            if not os.path.isdir(entry_path):
                continue

            nucl_exists = self._db_exists(os.path.join(entry_path, entry), "nucl")
            prot_exists = self._db_exists(os.path.join(entry_path, entry), "prot")

            if nucl_exists or prot_exists:
                found_databases.append(entry)
                continue

            if self._downloaded_db_exists(entry, "nucl", entry_path) or self._downloaded_db_exists(entry, "prot", entry_path):
                found_databases.append(entry)

        return found_databases

    def get_all_database_paths(self) -> list[str]:
        """
        Return a list of BLAST database prefix paths.
        Example:
        ['databases/db1/db1', 'databases/db2/db2']
        """
        database_names = self.get_all_database_names()
        return [os.path.join(self.download_dir, db_name, db_name) for db_name in database_names]
    
    def get_all_database_paths_by_type(self, db_type: str) -> list[str]:
        """
        Return database prefix paths filtered by database type.

        Args:
            db_type (str): 'nucl'/'nucleotide' or 'prot'/'protein'

        Returns:
            list[str]: List of matching database prefix paths.
        """
        db_type_flag = self._normalize_db_type(db_type)
        matching_paths: list[str] = []

        if not os.path.isdir(self.download_dir):
            return matching_paths

        for entry in sorted(os.listdir(self.download_dir)):
            entry_path = os.path.join(self.download_dir, entry)

            if not os.path.isdir(entry_path):
                continue

            db_prefix = os.path.join(entry_path, entry)

            if self._db_exists(db_prefix, db_type_flag):
                matching_paths.append(db_prefix)
                continue

            if self._downloaded_db_exists(entry, db_type_flag, entry_path):
                matching_paths.append(db_prefix)

        return matching_paths

    def list_databases(self) -> None:
        """
        Print all available BLAST database names.
        """
        database_names = self.get_all_database_names()

        if not database_names:
            sys.stdout.write("No BLAST databases were found.\n")
            return

        sys.stdout.write("Available BLAST databases:\n")
        for db_name in database_names:
            sys.stdout.write(f"{db_name}\n")


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


def download_ncbi_database(db_name: str) -> str:
    """
    Module-level wrapper around DatabaseManager.download_ncbi.

    Args:
        db_name (str): Name of the NCBI database to download.

    Returns:
        str: Path prefix of the downloaded BLAST database.
    """
    return DatabaseManager().download_ncbi(db_name)


def get_all_database_names(download_dir: str = "databases") -> list[str]:
    """
    Module-level wrapper around DatabaseManager.get_all_database_names.
    """
    return DatabaseManager(download_dir=download_dir).get_all_database_names()


def get_all_database_paths(download_dir: str = "databases") -> list[str]:
    """
    Module-level wrapper around DatabaseManager.get_all_database_paths.
    """
    return DatabaseManager(download_dir=download_dir).get_all_database_paths()

def get_all_database_paths_by_type(
    db_type: str,
    download_dir: str = "databases"
) -> list[str]:
    """
    Module-level wrapper around DatabaseManager.get_all_database_paths_by_type.
    """
    return DatabaseManager(download_dir=download_dir).get_all_database_paths_by_type(db_type)


def list_databases(download_dir: str = "databases") -> None:
    """
    Module-level wrapper around DatabaseManager.list_databases.
    """
    DatabaseManager(download_dir=download_dir).list_databases()
