"""问题三预测和解释评价指标。"""

from __future__ import annotations

import numpy as np


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray, classes: int = 3) -> float:
    values = []
    for c in range(classes):
        tp = float(np.sum((y_true == c) & (y_pred == c)))
        fp = float(np.sum((y_true != c) & (y_pred == c)))
        fn = float(np.sum((y_true == c) & (y_pred != c)))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        values.append(2 * precision * recall / (precision + recall) if precision + recall else 0.0)
    return float(np.mean(values))


def pearson(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if np.std(y_true) < 1e-12 or np.std(y_pred) < 1e-12:
        return 0.0
    return float(np.corrcoef(y_true, y_pred)[0, 1])


def prediction_metrics(y_true_cls: np.ndarray, pred_cls: np.ndarray, y_true_reg: np.ndarray, pred_reg: np.ndarray) -> dict[str, float]:
    return {
        "accuracy": float(np.mean(y_true_cls == pred_cls)),
        "macro_f1": macro_f1(y_true_cls, pred_cls),
        "mae": float(np.mean(np.abs(y_true_reg - pred_reg))),
        "pearson": pearson(y_true_reg, pred_reg),
    }
