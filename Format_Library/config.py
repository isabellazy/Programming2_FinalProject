#!/usr/bin/env python3
#By Patrick Bircher

"""
config.py

Handles configuration loading for the pipeline.

Currently supports:
- reading BLAST parameter settings from a configuration text file
- converting configuration entries into a Python dictionary
- printing loaded configuration values

This module is intended for centralized configuration management so the
pipeline can be controlled without changing the source code.

Functions:
    load_config: Load configuration values from a text file.
    print_config: Print configuration values in a readable format.

Typical usage:
    config = load_config("Format_Library-Patrick/blast_config.txt")
    print_config(config)
"""

import pandas as pd
import sys


def load_config(config_path):
    """
    Load configuration file into a dictionary using pandas.

    Input:
    - config_path: path to config .txt file

    Output:
    - dict with configuration parameters
    """
    try:
        df = pd.read_csv(config_path)
    except Exception as e:
        raise RuntimeError(f"Error reading config file: {e}")

    if "parameter" not in df.columns or "value" not in df.columns:
        raise ValueError("Config file must contain 'parameter' and 'value' columns.")

    config_dict = {}

    for _, row in df.iterrows():
        key = row["parameter"]
        value = row["value"]

        # Try to convert numeric values
        try:
            if "." in str(value) or "e" in str(value).lower():
                value = float(value)
            else:
                value = int(value)
        except:
            pass  # keep as string

        config_dict[key] = value

    return config_dict


def print_config(config_dict):
    """
    Print loaded configuration nicely.
    """
    sys.stdout.write("Loaded configuration:\n")
    for key, value in config_dict.items():
        sys.stdout.write(f"{key}: {value}\n")
