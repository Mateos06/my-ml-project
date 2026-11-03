"""Metrics, cost decisions, calibration, slices, and paired bootstrap."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score

from .config import FALSE_NEGATIVE_COST, FALSE_POSITIVE_COST, SEED


def metrics(y, scores, threshold: float = .5) -> dict:
    y, scores = np.asarray(y, dtype=int), np.asarray(scores, dtype=float)
    predicted = scores >= threshold
    prevalence = float(y.mean())
    top_n = max(1, int(np.ceil(.2 * len(y))))
    # Fractionally include the tied cutoff group, avoiding dependence on row order.
    cutoff = np.partition(scores, len(scores) - top_n)[len(scores) - top_n]
    above, tied = scores > cutoff, scores == cutoff
    captured = y[above].sum() + (top_n - above.sum()) * y[tied].mean()
    lift = float(captured / top_n / prevalence) if prevalence else float("nan")
    fp = int(((y == 0) & predicted).sum())
    fn = int(((y == 1) & ~predicted).sum())
    return {"n": len(y), "positives": int(y.sum()), "positive_rate": prevalence,
            "average_precision": float(average_precision_score(y, scores)) if y.sum() else float("nan"),
            "precision": float(precision_score(y, predicted, zero_division=0)),
            "recall": float(recall_score(y, predicted, zero_division=0)),
            "lift_at_20pct": lift, "brier": float(brier_score_loss(y, scores)),
            "threshold": float(threshold), "predicted_positive_rate": float(predicted.mean()),
            "tp": int(((y == 1) & predicted).sum()), "fp": fp, "fn": fn,
            "tn": int(((y == 0) & ~predicted).sum()),
            "cost_per_trip": (FALSE_POSITIVE_COST * fp + FALSE_NEGATIVE_COST * fn) / len(y)}


def choose_threshold(y, scores) -> tuple[float, pd.DataFrame]:
    y, scores = np.asarray(y), np.asarray(scores)
    rows = []
    for threshold in np.r_[np.linspace(0, 1, 101), 1.000001]:
        decision = scores >= threshold
        fp, fn = int(((y == 0) & decision).sum()), int(((y == 1) & ~decision).sum())
        rows.append({"threshold": threshold, "fp": fp, "fn": fn,
                     "cost_per_trip": (FALSE_POSITIVE_COST * fp + FALSE_NEGATIVE_COST * fn) / len(y)})
    table = pd.DataFrame(rows)
    # Prefer the larger threshold on equal cost to avoid gratuitous prompts.
    best = table.sort_values(["cost_per_trip", "threshold"], ascending=[True, False]).iloc[0]
    return float(best.threshold), table


def reliability(y, scores) -> pd.DataFrame:
    frame = pd.DataFrame({"y": np.asarray(y), "score": scores})
    frame["bin"] = pd.cut(frame.score, np.linspace(0, 1, 11), include_lowest=True)
    return frame.groupby("bin", observed=True).agg(n=("y", "size"), predicted=("score", "mean"), observed=("y", "mean")).reset_index()


def rate_table(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    table = frame.groupby(column, dropna=False, observed=True).generous_tip.agg(n="size", positives="sum", rate="mean").reset_index()
    z = norm.ppf(.975)
    p, n = table.rate, table.n
    center = (p + z*z/(2*n)) / (1+z*z/n)
    half = z * np.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1+z*z/n)
    table["lower_95"], table["upper_95"] = center - half, center + half
    table["difference_pp"] = 100 * (p - frame.generous_tip.mean())
    table["practically_large"] = table.difference_pp.abs() >= 5
    return table


SLICE_COLUMNS = ["fare_band", "distance_band", "duration_band", "pickup_hour", "day_of_week",
                 "airport_trip", "passenger_count", "pickup_borough", "unknown_zone", "nonstandard_rate"]


def slice_metrics(frame: pd.DataFrame, scores, threshold: float) -> pd.DataFrame:
    scored = frame.copy()
    scored["score"] = scores
    rows = []
    for column in SLICE_COLUMNS:
        for value, group in scored.groupby(column, dropna=False, observed=True):
            result = metrics(group.generous_tip, group.score, threshold)
            rows.append({"slice": column, "value": str(value), "small_sample": len(group) < 200, **result})
    return pd.DataFrame(rows)


def paired_bootstrap(y, scores, baseline, threshold: float, baseline_threshold: float,
                     repetitions: int = 500, seed: int = SEED) -> pd.DataFrame:
    """Paired trip-level bootstrap; predictions are reused, never refitted.

    Percentile intervals are conditional on this frozen model and these months.
    They do not represent uncertainty from model selection or unseen seasonal drift.
    """
    if repetitions < 100:
        raise ValueError("Use at least 100 bootstrap repetitions.")
    y, scores, baseline = np.asarray(y), np.asarray(scores), np.asarray(baseline)
    rng = np.random.default_rng(seed)
    keys = ["average_precision", "precision", "recall", "lift_at_20pct", "cost_per_trip"]
    rows = []
    point = metrics(y, scores, threshold)
    base_point = metrics(y, baseline, baseline_threshold)
    samples = {key: {"model": [], "majority": [], "difference": []} for key in keys}
    for _ in range(repetitions):
        idx = rng.integers(0, len(y), len(y))
        a, b = metrics(y[idx], scores[idx], threshold), metrics(y[idx], baseline[idx], baseline_threshold)
        for key in keys:
            samples[key]["model"].append(a[key])
            samples[key]["majority"].append(b[key])
            samples[key]["difference"].append(a[key] - b[key])
    for key in keys:
        for label in ["model", "majority", "difference"]:
            low, high = np.nanquantile(samples[key][label], [.025, .975])
            estimate = point[key] if label == "model" else base_point[key] if label == "majority" else point[key]-base_point[key]
            rows.append({"metric": key, "estimator": label, "estimate": estimate, "lower_95": low,
                         "upper_95": high, "repetitions": repetitions, "unit": "trip"})
    return pd.DataFrame(rows)
