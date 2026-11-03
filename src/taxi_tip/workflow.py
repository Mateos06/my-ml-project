"""Development and one-time held-out evaluation, with durable provenance."""
from __future__ import annotations

import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import average_precision_score
from sklearn.tree import export_text

from .config import (ARTIFACTS, FEATURE_GROUPS, FALSE_NEGATIVE_COST, FALSE_POSITIVE_COST,
                     MIN_AP_GAIN, RAW, REPORTS, ROOT, SEED, TRIPS)
from .data import clean_trips, payment_audit, read_split, sha256
from .evaluation import (SLICE_COLUMNS, choose_threshold, metrics, paired_bootstrap,
                         rate_table, reliability, slice_metrics)
from .models import fit_fare_rule, make_pipeline, rule_scores
from .plots import evaluation_figures, exploratory, zone_map


def write_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    temporary.replace(path)


def source_hashes() -> dict:
    files = sorted((ROOT / "src" / "taxi_tip").glob("*.py"))
    return {str(p.relative_to(ROOT)).replace("\\", "/"): sha256(p) for p in files}


def develop() -> dict:
    """Read May/June only. Refuse tuning after the final evaluation begins."""
    if (ARTIFACTS / "july.lock").exists():
        raise RuntimeError("July has already been opened. Development is frozen; use existing reports.")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    tables, figures = REPORTS / "tables", REPORTS / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    # Timestamp-only structural audit is permitted before opening July outcomes.
    pickup = pd.read_parquet(TRIPS, columns=["tpep_pickup_datetime"]).iloc[:, 0]
    months = pd.to_datetime(pickup, errors="coerce").dt.strftime("%Y-%m").fillna("Invalid timestamp")
    months.value_counts().sort_index().rename_axis("pickup_month").reset_index(name="n").to_csv(tables / "pickup_month_audit.csv", index=False)
    raw_train, raw_val = read_split("train"), read_split("validation")
    train, train_audit = clean_trips(raw_train)
    validation, val_audit = clean_trips(raw_val)
    if train.generous_tip.nunique() != 2 or validation.generous_tip.nunique() != 2:
        raise ValueError("Both classes must be present in May and June.")
    for label, audit in [("train", train_audit), ("validation", val_audit)]:
        audit.to_csv(tables / f"cleaning_{label}.csv", index=False)
    payments = payment_audit(raw_train)
    payments.to_csv(tables / "payment_observability.csv", index=False)
    column_audit = []
    for column in raw_train:
        numeric = pd.to_numeric(raw_train[column], errors="coerce") if pd.api.types.is_numeric_dtype(raw_train[column]) else None
        column_audit.append({"column": column, "dtype": str(raw_train[column].dtype),
                             "missing": int(raw_train[column].isna().sum()),
                             "negative": int((numeric < 0).sum()) if numeric is not None else None})
    pd.DataFrame(column_audit).to_csv(tables / "raw_column_audit.csv", index=False)
    pd.DataFrame([{"flag": c, "n": int(train[c].sum()), "rate": float(train[c].mean())}
                  for c in ["unknown_zone", "nonstandard_rate", "passenger_unknown", "airport_trip"]]).to_csv(tables / "retained_flags.csv", index=False)
    rates = {column: rate_table(train, column) for column in SLICE_COLUMNS}
    for column, table in rates.items():
        table.to_csv(tables / f"rates_{column}.csv", index=False)
    exploratory(train, payments, rates, figures)
    zone_map(train, RAW, figures)
    print(f"Clean May: {len(train):,}; clean June: {len(validation):,}", flush=True)

    y_train, y_val = train.generous_tip.to_numpy(), validation.generous_tip.to_numpy()
    base_rate = float(y_train.mean())
    majority = np.full(len(validation), base_rate)
    rule = fit_fare_rule(train)
    rule_score = rule_scores(validation, rule)
    rule_threshold = float(rule["rates"][rule["band"]])
    rows = [{"model": "majority", **metrics(y_val, majority, .5)},
            {"model": "fare_rule", **metrics(y_val, rule_score, rule_threshold)}]

    groups = ["fare"]
    feature_rows = []
    baseline_pipeline = make_pipeline(groups).fit(train, y_train)
    best_score = float(average_precision_score(y_val, baseline_pipeline.predict_proba(validation)[:, 1]))
    feature_rows.append({"addition": "fare", "groups_tested": "fare", "june_ap": best_score,
                         "delta_ap": 0., "retained": True, "reason": "predeclared starting feature"})
    for group in list(FEATURE_GROUPS)[1:]:
        candidate_groups = [*groups, group]
        candidate = make_pipeline(candidate_groups).fit(train, y_train)
        score = float(average_precision_score(y_val, candidate.predict_proba(validation)[:, 1]))
        gain = score - best_score
        accepted = gain >= MIN_AP_GAIN
        feature_rows.append({"addition": group, "groups_tested": ", ".join(candidate_groups),
                             "june_ap": score, "delta_ap": gain, "retained": accepted,
                             "reason": "gain >= 0.001 AP" if accepted else "gain below 0.001 AP"})
        if accepted:
            groups, best_score = candidate_groups, score
        print(f"Feature {group}: AP={score:.4f}, gain={gain:+.4f}, retained={accepted}", flush=True)
    pd.DataFrame(feature_rows).to_csv(tables / "feature_comparison.csv", index=False)

    models, scores_by_name, threshold_tables = {}, {}, {}
    candidates = [("logistic", "logistic", 4, 200), ("tree_depth_2", "tree", 2, 200),
                  ("tree_depth_4", "tree", 4, 200), ("tree_depth_6", "tree", 6, 200),
                  ("tree_depth_8", "tree", 8, 200), ("tree_depth_6_leaf_1000", "tree", 6, 1000)]
    for name, family, depth, leaf in candidates:
        fitted = make_pipeline(groups, family, depth, leaf).fit(train, y_train)
        scores = fitted.predict_proba(validation)[:, 1]
        threshold, cost_table = choose_threshold(y_val, scores)
        row = {"model": name, **metrics(y_val, scores, threshold)}
        rows.append(row)
        models[name], scores_by_name[name], threshold_tables[name] = fitted, scores, cost_table
        print(f"{name}: June AP={row['average_precision']:.4f}, threshold={threshold:.2f}", flush=True)
    comparison = pd.DataFrame(rows)
    comparison.to_csv(REPORTS / "validation_metrics.csv", index=False)
    eligible = comparison.loc[comparison.model.isin(models)]
    selected = eligible.sort_values(["average_precision", "cost_per_trip", "model"], ascending=[False, True, True]).iloc[0]
    name, threshold = str(selected.model), float(selected.threshold)
    val_scores = scores_by_name[name]
    calibration = reliability(y_val, val_scores)
    calibration.to_csv(tables / "validation_reliability.csv", index=False)
    threshold_tables[name].to_csv(tables / "validation_thresholds.csv", index=False)
    slice_metrics(validation, val_scores, threshold).to_csv(tables / "validation_slices.csv", index=False)
    evaluation_figures(y_val, val_scores, calibration, threshold_tables[name], figures, "June")
    pd.DataFrame({"target": y_val, "score": val_scores}).to_parquet(ARTIFACTS / "validation_predictions.parquet", index=False)
    joblib.dump(models[name], ARTIFACTS / "model.joblib")
    joblib.dump(models["tree_depth_2"], ARTIFACTS / "depth2.joblib")
    tree = models[name].named_steps["model"]
    interpretation = {"family": type(tree).__name__}
    if hasattr(tree, "get_depth"):
        interpretation.update(depth=int(tree.get_depth()), leaves=int(tree.get_n_leaves()))
    depth2_pipeline = models["tree_depth_2"]
    feature_names = list(depth2_pipeline.named_steps["preprocess"].get_feature_names_out())
    (REPORTS / "depth2_rules.txt").write_text(
        "Numeric split thresholds are in May-standardized units. One-hot splits use 0/1.\n\n"
        + export_text(depth2_pipeline.named_steps["model"], feature_names=feature_names), encoding="utf-8")
    selection = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "seed": SEED,
        "selected_model": name, "feature_groups": groups, "threshold": threshold,
        "selection_metric": "June average precision (non-interpolated PR AUC)",
        "feature_selection": "greedy fixed-order additions; retain >=0.001 June AP gain",
        "false_positive_cost": FALSE_POSITIVE_COST, "false_negative_cost": FALSE_NEGATIVE_COST,
        "training_prevalence": base_rate, "fare_rule": rule, "rule_threshold": rule_threshold,
        "depth2_threshold": float(comparison.loc[comparison.model == "tree_depth_2", "threshold"].iloc[0]),
        "n_train_raw": len(raw_train), "n_validation_raw": len(raw_val),
        "n_train": len(train), "n_validation": len(validation),
        "data_sha256": sha256(TRIPS), "zones_sha256": sha256(RAW / "taxi_zone_lookup.csv"),
        "model_sha256": sha256(ARTIFACTS / "model.joblib"),
        "depth2_sha256": sha256(ARTIFACTS / "depth2.joblib"),
        "python": platform.python_version(), "sklearn": sklearn.__version__,
        "source_hashes": source_hashes(), "interpretation": interpretation,
    }
    write_json(ARTIFACTS / "selection.json", selection)
    write_json(REPORTS / "selection.json", selection)
    print(f"Frozen selection: {name}. July has not been read.", flush=True)
    return selection


def final_evaluate(repetitions: int = 500) -> dict:
    """One score pass. Subsequent calls return reports without loading July.

    An exclusive lock survives failures; cached predictions allow report recovery.
    If the process failed before saving predictions, an explicit documented manual
    recovery is needed. There is deliberately no --force switch.
    """
    selection_path = ARTIFACTS / "selection.json"
    final_path = ARTIFACTS / "final.json"
    if final_path.exists():
        print("July already evaluated; returning saved results without scoring again.", flush=True)
        return json.loads(final_path.read_text(encoding="utf-8"))
    if repetitions < 100:
        raise ValueError("Use at least 100 bootstrap repetitions.")
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    cache = ARTIFACTS / "july_predictions.parquet"
    lock = ARTIFACTS / "july.lock"
    if not lock.exists():
        for label, path, expected in [
            ("trips", TRIPS, selection["data_sha256"]),
            ("zones", RAW / "taxi_zone_lookup.csv", selection["zones_sha256"]),
            ("model", ARTIFACTS / "model.joblib", selection["model_sha256"]),
            ("depth2", ARTIFACTS / "depth2.joblib", selection["depth2_sha256"]),
        ]:
            if sha256(path) != expected:
                raise RuntimeError(f"Frozen {label} fingerprint changed. Refusing July evaluation.")
        if source_hashes() != selection["source_hashes"]:
            raise RuntimeError("Source changed after freezing. Re-run develop before opening July.")
        # Exclusive creation is atomic; concurrent processes cannot both score.
        with lock.open("x", encoding="utf-8") as stream:
            json.dump({"selection_sha256": sha256(selection_path), "opened_utc": datetime.now(timezone.utc).isoformat()}, stream)
        frame, audit = clean_trips(read_split("test"))
        audit.to_csv(REPORTS / "tables" / "cleaning_test.csv", index=False)
        chosen = joblib.load(ARTIFACTS / "model.joblib")
        depth2 = joblib.load(ARTIFACTS / "depth2.joblib")
        scored = frame[["generous_tip", *SLICE_COLUMNS]].copy()
        scored["selected_score"] = chosen.predict_proba(frame)[:, 1]
        scored["majority_score"] = selection["training_prevalence"]
        scored["rule_score"] = rule_scores(frame, selection["fare_rule"])
        scored["depth2_score"] = (scored.selected_score if selection["selected_model"] == "tree_depth_2"
                                  else depth2.predict_proba(frame)[:, 1])
        temporary = cache.with_suffix(".part.parquet")
        scored.to_parquet(temporary, index=False)
        temporary.replace(cache)
        write_json(ARTIFACTS / "july_predictions.sha256.json", {"sha256": sha256(cache)})
    elif not cache.exists():
        raise RuntimeError("July lock exists without saved predictions. Investigate the interruption; do not silently rescore.")
    else:
        cached_hash = json.loads((ARTIFACTS / "july_predictions.sha256.json").read_text())["sha256"]
        locked_selection = json.loads(lock.read_text())["selection_sha256"]
        if sha256(cache) != cached_hash or sha256(selection_path) != locked_selection:
            raise RuntimeError("Saved prediction or selection fingerprint changed.")
    scored = pd.read_parquet(cache)
    y = scored.generous_tip.to_numpy()
    variants = [("majority", "majority_score", .5), ("fare_rule", "rule_score", selection["rule_threshold"]),
                ("tree_depth_2", "depth2_score", selection["depth2_threshold"]),
                ("selected", "selected_score", selection["threshold"])]
    table = pd.DataFrame([{"model": name, **metrics(y, scored[column], threshold)} for name, column, threshold in variants])
    table.to_csv(REPORTS / "test_metrics.csv", index=False)
    print(f"July scored once: {len(y):,} eligible trips. Bootstrapping saved predictions…", flush=True)
    intervals = paired_bootstrap(y, scored.selected_score, scored.majority_score, selection["threshold"], .5, repetitions)
    intervals.to_csv(REPORTS / "tables" / "bootstrap_intervals.csv", index=False)
    calibration = reliability(y, scored.selected_score)
    calibration.to_csv(REPORTS / "tables" / "test_reliability.csv", index=False)
    slice_metrics(scored, scored.selected_score, selection["threshold"]).to_csv(REPORTS / "tables" / "test_slices.csv", index=False)
    evaluation_figures(y, scored.selected_score, calibration, None, REPORTS / "figures", "July")
    final = {"completed_utc": datetime.now(timezone.utc).isoformat(), "n_test": len(y),
             "selected_model": selection["selected_model"], "bootstrap_repetitions": repetitions,
             "selection_sha256": sha256(selection_path), "predictions_sha256": sha256(cache),
             "data_sha256": selection["data_sha256"], "model_sha256": selection["model_sha256"],
             "result": table.loc[table.model == "selected"].iloc[0].to_dict()}
    write_json(final_path, final)
    write_json(REPORTS / "final.json", final)
    return final
