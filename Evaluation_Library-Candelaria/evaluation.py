#!/usr/bin/env python3
#By Candelaria Domingo 

import os
import sys
from collections import defaultdict, Counter


# ---------------------------------------------------------------------------
# Core accuracy metrics
# ---------------------------------------------------------------------------

def compute_accuracy(
    predictions: dict[str, str],
    ground_truth: dict[str, str],
) -> dict[str, float | int | dict]:
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
    common_ids: set[str] = set(predictions.keys()) & set(ground_truth.keys())
    if not common_ids:
        raise ValueError("No common sequence IDs between predictions and ground_truth.")

    num_total = len(common_ids)
    num_correct = 0

    confusion: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))

    for sid in common_ids:
        true_label = ground_truth[sid]
        pred_label = predictions[sid]
        confusion[true_label][pred_label] += 1
        if true_label == pred_label:
            num_correct += 1

    accuracy: float = num_correct / num_total

    all_labels: set[str] = set(ground_truth[sid] for sid in common_ids)
    per_class: dict[str, dict[str, float | int]] = {}

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
            'support':   tp + fn,
        }

    macro_f1 = (sum(v['f1'] for v in per_class.values()) / len(per_class)
                if per_class else 0.0)

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


def print_metrics_report(
    metrics: dict[str, float | int | dict],
    title: str = "Classification Report",
) -> None:
    """
    Pretty-print a metrics dict returned by compute_accuracy().
    """
    sys.stdout.write(f"\n{'=' * 55}\n")
    sys.stdout.write(f"  {title}\n")
    sys.stdout.write(f"{'=' * 55}\n")
    sys.stdout.write(f"  Overall accuracy : {metrics['accuracy']:.4f}  "
                     f"({metrics['num_correct']}/{metrics['num_total']})\n")
    sys.stdout.write(f"  Macro F1         : {metrics['macro_f1']:.4f}\n")
    sys.stdout.write(f"  Weighted F1      : {metrics['weighted_f1']:.4f}\n")

    sys.stdout.write(f"\n  Per-class breakdown:\n")
    header = f"  {'Label':<25} {'Prec':>7} {'Rec':>7} {'F1':>7} {'Support':>9}"
    sys.stdout.write(header + "\n")
    sys.stdout.write(f"  {'-' * 57}\n")

    for label, vals in sorted(metrics['per_class'].items()):
        sys.stdout.write(
            f"  {label:<25} {vals['precision']:>7.4f} {vals['recall']:>7.4f} "
            f"{vals['f1']:>7.4f} {vals['support']:>9}\n"
        )

    sys.stdout.write(f"\n  Confusion matrix (rows=true, cols=predicted):\n")

    all_labels: list[str] = sorted(metrics['per_class'].keys())
    col_w: int = max(len(l) for l in all_labels) + 2
    header_row: str = " " * (col_w + 2) + "".join(f"{l:>{col_w}}" for l in all_labels)
    sys.stdout.write("  " + header_row + "\n")

    for true_label in all_labels:
        row: str = f"  {true_label:<{col_w}} "
        for pred_label in all_labels:
            count: int = metrics['confusion_matrix'].get(true_label, {}).get(pred_label, 0)
            row += f"{count:>{col_w}}"
        sys.stdout.write(row + "\n")

    sys.stdout.write("\n")


# ---------------------------------------------------------------------------
# Parameter / database effect analysis
# ---------------------------------------------------------------------------

def analyze_parameter_effects(
    results: dict[str, dict[str, float | int | dict]],
    parameter_settings: dict[str, dict],
) -> list[dict]:

    common_keys: set[str] = set(results.keys()) & set(parameter_settings.keys())

    summary: list[dict] = []
    
    for key in common_keys:
        metrics: dict[str, float | int | dict] = results[key]
        params: dict  = parameter_settings[key]

        entry: dict = {'setting_key': key}
        entry.update(params)
        entry['accuracy']     = metrics['accuracy']
        entry['macro_f1']     = metrics['macro_f1']
        entry['weighted_f1']  = metrics['weighted_f1']
        entry['num_correct']  = metrics['num_correct']
        entry['num_total']    = metrics['num_total']
        summary.append(entry)

    summary.sort(key=lambda x: (x['weighted_f1'], x['accuracy']), reverse=True)
    return summary


def print_parameter_effects_report(
    summary: list[dict],
    title: str = "Parameter Effect Analysis",
) -> None:

    if not summary:
        sys.stdout.write("No parameter effect data to display.\n")
        return

    sys.stdout.write(f"\n{'=' * 65}\n")
    sys.stdout.write(f"  {title}\n")
    sys.stdout.write(f"{'=' * 65}\n")

    fixed_keys: set[str] = {'setting_key', 'accuracy', 'macro_f1', 'weighted_f1',
                  'num_correct', 'num_total'}
    param_keys: list[str] = [k for k in summary[0].keys() if k not in fixed_keys]

    col_w = 18
    header: str = f"  {'Setting':<22}"
    for pk in param_keys:
        header += f"{pk:>{col_w}}"
    header += f"{'Accuracy':>{col_w}}{'MacroF1':>{col_w}}{'WeightedF1':>{col_w}}"
    sys.stdout.write(header + "\n")
    sys.stdout.write(f"  {'-' * (22 + col_w * (len(param_keys) + 3))}\n")

    for entry in summary:
        row: str = f"  {entry['setting_key']:<22}"
        for pk in param_keys:
            val: object = entry.get(pk, 'N/A')
            row += f"{str(val):>{col_w}}"
        row += (f"{entry['accuracy']:>{col_w}.4f}"
                f"{entry['macro_f1']:>{col_w}.4f}"
                f"{entry['weighted_f1']:>{col_w}.4f}")
        sys.stdout.write(row + "\n")

    best: dict  = summary[0]
    worst: dict = summary[-1]

    sys.stdout.write(f"\n  Best  setting : {best['setting_key']}  "
                     f"(weighted F1 = {best['weighted_f1']:.4f})\n")
    sys.stdout.write(f"  Worst setting : {worst['setting_key']}  "
                     f"(weighted F1 = {worst['weighted_f1']:.4f})\n")
    sys.stdout.write("\n")

def load_label_file(file_path: str) -> dict[str, str]:
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Label file not found: {file_path}")

    labels: dict[str, str] = {}
    
    with open(file_path, "r", encoding="utf-8") as infile:
        for line in infile:
            line = line.strip()

            if not line:
                continue

            parts: list[str] = line.split("\t")
            if len(parts) != 2:
                continue

            labels[parts[0]] = parts[1]

    return labels

def evaluate_classification_file(
    classification_file: str,
    ground_truth_file: str,
) -> dict[str, float | int | dict]:
    predictions: dict[str, str] = load_label_file(classification_file)
    ground_truth: dict[str, str] = load_label_file(ground_truth_file)
    return compute_accuracy(predictions, ground_truth)
