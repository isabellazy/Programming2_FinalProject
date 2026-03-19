# By Candelaria Domingo  

#!/usr/bin/env python3

"""
Evaluation and performance analysis module.

This module measures classification accuracy using known sequences
and analyzes how performance changes with different databases
or BLAST parameter settings.

Conceptual inputs:
- Predicted classifications
- Ground truth labels

Conceptual outputs:
- Accuracy metrics and evaluation reports
"""

import os
import sys
from collections import defaultdict, Counter


# ---------------------------------------------------------------------------
# Core accuracy metrics
# ---------------------------------------------------------------------------

def compute_accuracy(predictions, ground_truth):
    """
    Compute classification accuracy metrics.

    Inputs:
    - predictions:   dict  {sequence_id -> predicted_label}
    - ground_truth:  dict  {sequence_id -> true_label}

    Outputs:
    - metrics: dict containing:
        'accuracy'          : float  — fraction of correct predictions
        'num_correct'       : int
        'num_total'         : int
        'confusion_matrix'  : dict[true_label][pred_label] = count
        'per_class'         : dict[label] -> {'tp', 'fp', 'fn', 'precision',
                                               'recall', 'f1'}
        'macro_f1'          : float  — unweighted mean F1 across all classes
        'weighted_f1'       : float  — support-weighted mean F1

    Example:
    >>> preds  = {"s1": "A", "s2": "B", "s3": "A"}
    >>> truths = {"s1": "A", "s2": "A", "s3": "B"}
    >>> m = compute_accuracy(preds, truths)
    >>> m['accuracy']
    0.3333...
    """
    # Only evaluate sequences that appear in both dicts
    common_ids = set(predictions.keys()) & set(ground_truth.keys())
    if not common_ids:
        raise ValueError("No common sequence IDs between predictions and ground_truth.")

    num_total = len(common_ids)
    num_correct = 0

    # Build confusion matrix: confusion[true][pred] = count
    confusion = defaultdict(lambda: defaultdict(int))
    for sid in common_ids:
        true_label = ground_truth[sid]
        pred_label = predictions[sid]
        confusion[true_label][pred_label] += 1
        if true_label == pred_label:
            num_correct += 1

    accuracy = num_correct / num_total

    # Per-class precision, recall, F1
    all_labels = set(ground_truth[sid] for sid in common_ids)
    per_class = {}
    for label in all_labels:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in all_labels if other != label)
        fn = sum(confusion[label][other] for other in all_labels if other != label)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)

        per_class[label] = {
            'tp': tp, 'fp': fp, 'fn': fn,
            'precision': precision,
            'recall':    recall,
            'f1':        f1,
            'support':   tp + fn,   # true positives + false negatives = actual count
        }

    # Macro F1 (unweighted)
    macro_f1 = (sum(v['f1'] for v in per_class.values()) / len(per_class)
                if per_class else 0.0)

    # Weighted F1
    total_support = sum(v['support'] for v in per_class.values())
    weighted_f1 = (
        sum(v['f1'] * v['support'] for v in per_class.values()) / total_support
        if total_support > 0 else 0.0
    )

    return {
        'accuracy':         accuracy,
        'num_correct':      num_correct,
        'num_total':        num_total,
        'confusion_matrix': {k: dict(v) for k, v in confusion.items()},
        'per_class':        per_class,
        'macro_f1':         macro_f1,
        'weighted_f1':      weighted_f1,
    }


def print_metrics_report(metrics, title="Classification Report"):
    """
    Pretty-print a metrics dict returned by compute_accuracy().

    Inputs:
    - metrics: dict as returned by compute_accuracy()
    - title:   string header for the report
    """
    print(f"\n{'=' * 55}")
    print(f"  {title}")
    print(f"{'=' * 55}")
    print(f"  Overall accuracy : {metrics['accuracy']:.4f}  "
          f"({metrics['num_correct']}/{metrics['num_total']})")
    print(f"  Macro F1         : {metrics['macro_f1']:.4f}")
    print(f"  Weighted F1      : {metrics['weighted_f1']:.4f}")

    print(f"\n  Per-class breakdown:")
    header = f"  {'Label':<25} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Support':>9}"
    print(header)
    print(f"  {'-' * 57}")
    for label, vals in sorted(metrics['per_class'].items()):
        print(f"  {label:<25} {vals['precision']:>7.4f} {vals['recall']:>7.4f} "
              f"{vals['f1']:>7.4f} {vals['support']:>9}")

    print(f"\n  Confusion matrix (rows=true, cols=predicted):")
    all_labels = sorted(metrics['per_class'].keys())
    col_w = max(len(l) for l in all_labels) + 2
    header_row = " " * (col_w + 2) + "".join(f"{l:>{col_w}}" for l in all_labels)
    print("  " + header_row)
    for true_label in all_labels:
        row = f"  {true_label:<{col_w}} "
        for pred_label in all_labels:
            count = metrics['confusion_matrix'].get(true_label, {}).get(pred_label, 0)
            row += f"{count:>{col_w}}"
        print(row)
    print()


# ---------------------------------------------------------------------------
# Parameter / database effect analysis
# ---------------------------------------------------------------------------

def analyze_parameter_effects(results, parameter_settings):
    """
    Analyze how BLAST parameters or database composition affect performance.

    Inputs:
    - results: dict mapping a setting_key -> metrics dict
        (as returned by compute_accuracy()).
        Example:
        {
            "evalue_1e-3":  compute_accuracy(preds_1e3,  truth),
            "evalue_1e-10": compute_accuracy(preds_1e10, truth),
            "word_size_4":  compute_accuracy(preds_ws4,  truth),
        }

    - parameter_settings: dict mapping the same setting_keys -> parameter dict
        Example:
        {
            "evalue_1e-3":  {"evalue": 1e-3,  "word_size": 11},
            "evalue_1e-10": {"evalue": 1e-10, "word_size": 11},
            "word_size_4":  {"evalue": 1e-5,  "word_size": 4},
        }

    Outputs:
    - summary: list of dicts, one per setting, sorted by weighted F1 descending.
        Each dict contains:
            'setting_key', all parameter_settings fields,
            'accuracy', 'macro_f1', 'weighted_f1',
            'num_correct', 'num_total'

    Notes:
    - If a setting_key appears in parameter_settings but not results (or vice
      versa) it is silently skipped.
    """
    common_keys = set(results.keys()) & set(parameter_settings.keys())

    summary = []
    for key in common_keys:
        metrics = results[key]
        params  = parameter_settings[key]

        entry = {'setting_key': key}
        entry.update(params)                        # add all parameter values
        entry['accuracy']     = metrics['accuracy']
        entry['macro_f1']     = metrics['macro_f1']
        entry['weighted_f1']  = metrics['weighted_f1']
        entry['num_correct']  = metrics['num_correct']
        entry['num_total']    = metrics['num_total']
        summary.append(entry)

    # Sort by weighted F1, then accuracy, descending
    summary.sort(key=lambda x: (x['weighted_f1'], x['accuracy']), reverse=True)
    return summary


def print_parameter_effects_report(summary, title="Parameter Effect Analysis"):
    """
    Pretty-print the summary list returned by analyze_parameter_effects().

    Inputs:
    - summary: list of dicts as returned by analyze_parameter_effects()
    - title:   string header
    """
    if not summary:
        print("No parameter effect data to display.")
        return

    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print(f"{'=' * 65}")

    # Discover parameter columns (all keys except the fixed metric keys)
    fixed_keys = {'setting_key', 'accuracy', 'macro_f1', 'weighted_f1',
                  'num_correct', 'num_total'}
    param_keys = [k for k in summary[0].keys() if k not in fixed_keys]

    col_w = 18
    header = f"  {'Setting':<22}"
    for pk in param_keys:
        header += f"{pk:>{col_w}}"
    header += f"{'Accuracy':>{col_w}}{'MacroF1':>{col_w}}{'WeightedF1':>{col_w}}"
    print(header)
    print(f"  {'-' * (22 + col_w * (len(param_keys) + 3))}")

    for entry in summary:
        row = f"  {entry['setting_key']:<22}"
        for pk in param_keys:
            val = entry.get(pk, 'N/A')
            row += f"{str(val):>{col_w}}"
        row += (f"{entry['accuracy']:>{col_w}.4f}"
                f"{entry['macro_f1']:>{col_w}.4f}"
                f"{entry['weighted_f1']:>{col_w}.4f}")
        print(row)

    # Identify best / worst settings
    best  = summary[0]
    worst = summary[-1]
    print(f"\n  Best  setting : {best['setting_key']}  "
          f"(weighted F1 = {best['weighted_f1']:.4f})")
    print(f"  Worst setting : {worst['setting_key']}  "
          f"(weighted F1 = {worst['weighted_f1']:.4f})")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """
    Demonstration / smoke-test for the evaluation module.

    In the full pipeline this is called from main.py after
    classifier.py has produced the predictions dict.
    """

    # -----------------------------------------------------------------------
    # Part 1 — compute_accuracy demo
    # -----------------------------------------------------------------------
    print("=== Evaluation Module Demo ===\n")

    ground_truth = {
        "seq1": "Influenza A",
        "seq2": "Influenza A",
        "seq3": "Rabies virus",
        "seq4": "Rabies virus",
        "seq5": "E. coli",
        "seq6": "E. coli",
        "seq7": "Unclassified",
    }

    # Simulate classifier output with some errors
    predictions_run1 = {
        "seq1": "Influenza A",    # correct
        "seq2": "Influenza A",    # correct
        "seq3": "Rabies virus",   # correct
        "seq4": "Influenza A",    # wrong
        "seq5": "E. coli",        # correct
        "seq6": "Unclassified",   # wrong
        "seq7": "Unclassified",   # correct
    }

    metrics_run1 = compute_accuracy(predictions_run1, ground_truth)
    print_metrics_report(metrics_run1, title="Run 1 — default parameters (e-value 1e-5, word_size 11)")

    # -----------------------------------------------------------------------
    # Part 2 — analyze_parameter_effects demo
    # -----------------------------------------------------------------------

    # Stricter e-value: more predictions become "Unclassified"
    predictions_run2 = {
        "seq1": "Influenza A",
        "seq2": "Influenza A",
        "seq3": "Rabies virus",
        "seq4": "Unclassified",   # strict threshold rejected borderline hit
        "seq5": "E. coli",
        "seq6": "Unclassified",
        "seq7": "Unclassified",
    }
    metrics_run2 = compute_accuracy(predictions_run2, ground_truth)

    # Smaller word size: more hits, but some extra false positives
    predictions_run3 = {
        "seq1": "Influenza A",
        "seq2": "Influenza A",
        "seq3": "Rabies virus",
        "seq4": "Rabies virus",   # now correct
        "seq5": "E. coli",
        "seq6": "E. coli",        # now correct
        "seq7": "E. coli",        # false positive — should be Unclassified
    }
    metrics_run3 = compute_accuracy(predictions_run3, ground_truth)

    results_by_setting = {
        "evalue_1e-5_ws11":  metrics_run1,
        "evalue_1e-20_ws11": metrics_run2,
        "evalue_1e-5_ws4":   metrics_run3,
    }

    param_settings = {
        "evalue_1e-5_ws11":  {"evalue": 1e-5,  "word_size": 11},
        "evalue_1e-20_ws11": {"evalue": 1e-20, "word_size": 11},
        "evalue_1e-5_ws4":   {"evalue": 1e-5,  "word_size": 4},
    }

    summary = analyze_parameter_effects(results_by_setting, param_settings)
    print_parameter_effects_report(summary, title="Effect of E-value Threshold and Word Size")

    print("Interpretation:")
    print("  - Smaller word sizes can improve sensitivity (more true positives)")
    print("    but may also increase false positives.")
    print("  - Stricter E-value thresholds reduce false positives at the cost")
    print("    of more sequences labelled Unclassified (missed classifications).")
    print("  - Choose parameters that balance precision and recall for your use case.")


if __name__ == "__main__":
    main()
