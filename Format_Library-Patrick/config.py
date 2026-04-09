#!/usr/bin/env python3
#By Patrick Bircher

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
