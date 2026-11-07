"""Export the frozen study for the interactive lab. Never refit or reopen July.

May is used for additional descriptive aggregates. Curves and error examples use
already-cached June/July predictions. Browser inference is exported from the
actual fitted preprocessing and tree, then checked against sklearn separately.
"""
from pathlib import Path
import json
import math
import joblib
import numpy as np
import pandas as pd
import shapefile
from sklearn.metrics import precision_recall_curve
from taxi_tip.config import ROOT, RAW, REPORTS, ARTIFACTS
from taxi_tip.data import read_split, clean_trips, sha256
from taxi_tip.workflow import source_hashes

OUT = ROOT / "docs" / "assets" / "lab"


def native(value):
    if isinstance(value, dict):
        return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [native(v) for v in value]
    if isinstance(value, np.generic):
        return native(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def save(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(native(value), separators=(",", ":"), allow_nan=False), encoding="utf-8")


def table(name):
    return pd.read_csv(REPORTS / "tables" / name).to_dict("records")


def export_model(pipeline, threshold):
    pre = pipeline.named_steps["preprocess"]
    num = pre.named_transformers_["numeric"]
    encoder = pre.named_transformers_["category"].named_steps["encode"]
    estimator = pipeline.named_steps["model"]
    tree = estimator.tree_
    names = pre.get_feature_names_out().tolist()
    numeric = list(pre.transformers_[0][2])
    categorical = list(pre.transformers_[1][2])
    descriptors = [{"name": name, "kind": "numeric", "mean": num.named_steps["scale"].mean_[i],
                    "scale": num.named_steps["scale"].scale_[i], "median": num.named_steps["impute"].statistics_[i]}
                   for i, name in enumerate(numeric)]
    for column, categories in zip(categorical, encoder.categories_):
        descriptors.extend({"name": column, "kind": "category", "category": str(cat)} for cat in categories)
    return {"threshold": threshold, "features": descriptors, "feature_names": names,
            "numeric_columns": numeric, "categorical_columns": categorical,
            "left": tree.children_left.tolist(), "right": tree.children_right.tolist(),
            "feature": tree.feature.tolist(), "split": tree.threshold.tolist(),
            "probability": (tree.value[:, 0, 1] / tree.value[:, 0, :].sum(axis=1)).tolist(),
            "samples": tree.n_node_samples.tolist(), "depth": int(tree.max_depth),
            "classes": estimator.classes_.tolist(), "input_dtype": "float32 after preprocessing"}


def curve(y, scores):
    precision, recall, thresholds = precision_recall_curve(y, scores)
    return [{"precision": float(p), "recall": float(r), "threshold": float(t)}
            for p, r, t in zip(precision[:-1], recall[:-1], thresholds)] + [{"precision": 1., "recall": 0., "threshold": None}]


def export():
    selection = json.loads((REPORTS / "selection.json").read_text())
    assert source_hashes() == selection["source_hashes"], "Frozen analytical source changed"
    assert sha256(RAW / "yellow_tripdata_2026_sample.parquet") == selection["data_sha256"]
    assert sha256(RAW / "taxi_zone_lookup.csv") == selection["zones_sha256"]
    assert sha256(ARTIFACTS / "model.joblib") == selection["model_sha256"]
    assert sha256(ARTIFACTS / "depth2.joblib") == selection["depth2_sha256"]
    final = json.loads((REPORTS / "final.json").read_text())
    assert sha256(ARTIFACTS / "july_predictions.parquet") == final["predictions_sha256"]
    may, _ = clean_trips(read_split("train"))
    zones = pd.read_csv(RAW / "taxi_zone_lookup.csv").fillna("Unknown")
    selected = export_model(joblib.load(ARTIFACTS / "model.joblib"), selection["threshold"])
    depth2 = export_model(joblib.load(ARTIFACTS / "depth2.joblib"), selection["depth2_threshold"])
    save("model.json", {"selected": selected, "depth2": depth2, "model_sha256": selection["model_sha256"],
                        "zones": zones.to_dict("records"), "groups": selection["feature_groups"]})
    histogram, edges = np.histogram(may.tip_pct.clip(upper=100), bins=np.arange(0, 102))
    distribution = [{"percentage": int(i), "count": int(n), "share": float(n / len(may))} for i, n in enumerate(histogram)]
    june = pd.read_parquet(ARTIFACTS / "validation_predictions.parquet")
    july = pd.read_parquet(ARTIFACTS / "july_predictions.parquet")
    thresholds = []
    for row in table("validation_thresholds.csv"):
        y = june.target.to_numpy()
        predicted = june.score.to_numpy() >= row["threshold"]
        tp, tn = int(((y == 1) & predicted).sum()), int(((y == 0) & ~predicted).sum())
        thresholds.append({**row, "tp": tp, "tn": tn, "precision": tp / max(1, tp + row["fp"]),
                           "recall": tp / max(1, tp + row["fn"])})
    failures = []
    for kind, mask in [("False positive", (july.selected_score >= selection["threshold"]) & (july.generous_tip == 0)),
                       ("False negative", (july.selected_score < selection["threshold"]) & (july.generous_tip == 1))]:
        example = july.loc[mask].iloc[0]
        failures.append({"kind": kind, "probability": float(example.selected_score), "target": int(example.generous_tip),
                         "fare_band": example.fare_band, "duration_band": example.duration_band,
                         "distance_band": example.distance_band, "hour": int(example.pickup_hour)})
    data = {"selection": selection, "final": final, "may_n": len(may), "histogram": distribution,
            "rates": {name: table(f"rates_{name}.csv") for name in ["fare_band", "pickup_hour", "day_of_week", "airport_trip", "distance_band", "duration_band", "passenger_count", "pickup_borough"]},
            "funnel": {split: table(f"cleaning_{split}.csv") for split in ["train", "validation", "test"]},
            "months": table("pickup_month_audit.csv"), "payments": table("payment_observability.csv"),
            "features": table("feature_comparison.csv"), "intervals": table("bootstrap_intervals.csv"),
            "metrics": {"June": pd.read_csv(REPORTS / "validation_metrics.csv").to_dict("records"),
                        "July": pd.read_csv(REPORTS / "test_metrics.csv").to_dict("records")},
            "curves": {"June": curve(june.target, june.score), "July": curve(july.generous_tip, july.selected_score)},
            "reliability": {"June": table("validation_reliability.csv"), "July": table("test_reliability.csv")},
            "thresholds": thresholds, "failures": failures, "slices": table("test_slices.csv")}
    save("study.json", data)

    # Render native StatePlane feet through a uniform affine transform. No fake
    # longitude/latitude or geographic basemap is involved. Preserve polygon holes.
    reader = shapefile.Reader(str(next(RAW.rglob("*.shp"))))
    minx, miny, maxx, maxy = reader.bbox
    scale = min(850/(maxx-minx), 850/(maxy-miny))
    xpad, ypad = (900-(maxx-minx)*scale)/2, (900-(maxy-miny)*scale)/2
    grouped = may.groupby("PULocationID").generous_tip.agg(["size", "sum", "mean"])
    lookup = zones.set_index("LocationID").to_dict("index")
    paths = {}
    for sr in reader.iterShapeRecords():
        loc = int(sr.record.as_dict()["LocationID"])
        starts = list(sr.shape.parts)+[len(sr.shape.points)]
        commands = []
        for start, end in zip(starts[:-1], starts[1:]):
            points = [(round(xpad+(x-minx)*scale, 1), round(ypad+(maxy-y)*scale, 1)) for x, y in sr.shape.points[start:end]]
            points = [p for i, p in enumerate(points) if i == 0 or p != points[i-1]]
            if len(points) < 3:
                continue
            commands.append("M"+"L".join(f"{x},{y}" for x,y in points)+"Z")
        if loc not in paths:
            stat = grouped.loc[loc] if loc in grouped.index else None
            paths[loc] = {"id":loc, "name":lookup.get(loc, {}).get("Zone", "Unknown"),
                          "borough":lookup.get(loc, {}).get("Borough", "Unknown"), "path":"",
                          "n": int(stat['size']) if stat is not None else 0,
                          "rate": float(stat['mean']) if stat is not None else None,
                          "airport": {1:"Newark (EWR)",132:"John F. Kennedy (JFK)",138:"LaGuardia (LGA)"}.get(loc)}
        paths[loc]["path"] += "".join(commands)
    save("zones.json", {"viewBox":"0 0 900 900", "coordinate_system":"NAD83 / New York Long Island, US survey feet; uniform screen transform", "zones":list(paths.values())})
    # Held-out training records are not published. Conformance fixtures stay local.
    sample = may.sample(1000, random_state=2026)
    model = joblib.load(ARTIFACTS / "model.joblib")
    columns = selected["numeric_columns"] + selected["categorical_columns"]
    fixtures = {"rows": sample[columns].to_dict("records"), "probabilities": model.predict_proba(sample)[:,1].tolist()}
    (ARTIFACTS / "browser_fixtures.json").write_text(json.dumps(native(fixtures)), encoding="utf-8")
    print(f"Exported May aggregates, cached evaluation, {len(paths)} real zone boundaries and {len(selected['left'])} model nodes.")


if __name__ == "__main__":
    export()
