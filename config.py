"""
Configuration module for the Multi-Database BLAST Classification Tool.

This file defines all global configuration values used across the project,
including database paths, BLAST parameters, and evaluation settings.

It allows the rest of the codebase to remain modular and flexible by
centralizing adjustable parameters in one place.

Conceptual inputs:
- User-defined paths and parameters (hardcoded or read from a config file)

Conceptual outputs:
- Configuration objects or dictionaries accessed by other modules
"""

def load_config():
    """
    Load and return configuration parameters for the project.

    Inputs:
    - None (or optionally a path to a config file).

    Outputs:
    - A configuration object or dictionary containing:
      - Paths to BLAST databases
      - Query file path
      - BLAST parameters (e-value, word size, etc.)
      - Evaluation settings

    High-level steps:
    1. Define default configuration values.
    2. Optionally override defaults with user-provided settings.
    3. Return the final configuration structure.
    """
    pass
