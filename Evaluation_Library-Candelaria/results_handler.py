#!/usr/bin/env python3
#By Isabella Zuluaga

import os
import shutil
import sys


def save_results(blast_results, query_file):
    """
    Save BLAST results to:
    results/<query_name>/<query_name>_results.txt
    """

    query_name = os.path.splitext(os.path.basename(query_file))[0]
    results_dir = os.path.join("results", query_name)

    if os.path.exists(results_dir):
        shutil.rmtree(results_dir)

    os.makedirs(results_dir, exist_ok=True)

    output_file = os.path.join(results_dir, f"{query_name}_results.txt")

    with open(output_file, "w", encoding="utf-8") as out:

        for query_id, hits in blast_results.items():
            out.write(f"Query: {query_id}\n")

            if not hits:
                out.write("No hits found\n\n")
                continue

            for hit in hits:
                out.write(
                    f"{hit['database']}\t"
                    f"{hit['subject_id']}\t"
                    f"{hit['identity']}\t"
                    f"{hit['alignment_length']}\t"
                    f"{hit['evalue']}\t"
                    f"{hit['bitscore']}\n"
                )

            out.write("\n")

    sys.stdout.write(f"Results saved in: {output_file}\n")
