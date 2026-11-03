"""Deterministic, stateless population decisions and temporal reading."""
from __future__ import annotations

import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

from .config import AIRPORTS, MONEY, RAW, SPLITS, TRIPS

REQUIRED = {"tpep_pickup_datetime", "tpep_dropoff_datetime", "payment_type", "fare_amount",
            "tip_amount", "trip_distance", "PULocationID", "DOLocationID", "RatecodeID", "passenger_count"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_split(split: str, path: Path = TRIPS) -> pd.DataFrame:
    start, end = SPLITS[split]
    if not path.exists():
        raise FileNotFoundError("Run python data/get_data.py first.")
    return pd.read_parquet(path, filters=[
        ("tpep_pickup_datetime", ">=", pd.Timestamp(start)),
        ("tpep_pickup_datetime", "<", pd.Timestamp(end)),
    ])


def positive_rate(frame: pd.DataFrame) -> float:
    # A meaningful target exists only for valid card fares.
    eligible = frame.loc[(frame.payment_type == 1) & (frame.fare_amount > 0)
                         & np.isfinite(frame.fare_amount) & (frame.tip_amount >= 0)
                         & np.isfinite(frame.tip_amount)]
    return float((eligible.tip_amount >= .25 * eligible.fare_amount).mean()) if len(eligible) else float("nan")


def clean_trips(raw: pd.DataFrame, zones: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return cleaned card population and an ordered attrition audit.

    Fixed limits are plausibility policies, not empirical quantiles. Unknown zones,
    nonstandard fares and missing passengers are retained and flagged.
    """
    missing = REQUIRED - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    data = raw.copy()
    for column in [*MONEY, "trip_distance", "payment_type", "PULocationID", "DOLocationID", "RatecodeID", "passenger_count"]:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    for column in ["tpep_pickup_datetime", "tpep_dropoff_datetime"]:
        data[column] = pd.to_datetime(data[column], errors="coerce")
    audit = []

    def record(step: str, before: int, decision: str) -> None:
        audit.append({"step": step, "decision": decision, "before": before, "remaining": len(data),
                      "removed": before - len(data), "card_positive_rate": positive_rate(data)})

    def keep(mask: pd.Series, step: str, decision: str) -> None:
        nonlocal data
        before = len(data)
        data = data.loc[mask.fillna(False)].copy()
        record(step, before, decision)

    record("Raw rows", len(data), "audit; positive rate denominator is eligible card trips only")
    keep(~data.duplicated(), "Exact duplicates", "drop duplicate rows")
    keep(data.payment_type == 1, "Observable card tips", "drop cash, flex, no-charge, disputes, unknown and voided")
    keep((data.fare_amount > 0) & np.isfinite(data.fare_amount), "Positive fare", "drop zero, negative, missing or infinite fares")
    keep((data.tip_amount >= 0) & np.isfinite(data.tip_amount), "Valid tip", "drop negative, missing or infinite tips")
    fields = [c for c in MONEY if c in data and c not in {"fare_amount", "tip_amount"}]
    keep(~(data[fields].lt(0) | np.isinf(data[fields])).any(axis=1), "Nonnegative charges", "drop negative or infinite fees; missing fees imputed in May pipeline")
    data["duration_minutes"] = (data.tpep_dropoff_datetime - data.tpep_pickup_datetime).dt.total_seconds() / 60
    keep(data.duration_minutes.between(.5, 240), "Plausible duration", "drop missing, <30 seconds or >4 hours")
    keep(data.trip_distance.between(.01, 100), "Plausible distance", "drop missing, <0.01 or >100 miles")
    data["speed_mph"] = data.trip_distance / data.duration_minutes * 60
    keep(data.speed_mph <= 100, "Plausible average speed", "drop >100 mph")
    data["unknown_zone"] = (~data.PULocationID.between(1, 263) | ~data.DOLocationID.between(1, 263)
                            | (data.PULocationID % 1 != 0) | (data.DOLocationID % 1 != 0)).astype(int)
    for column in ["PULocationID", "DOLocationID"]:
        data.loc[~data[column].between(1, 263) | (data[column] % 1 != 0), column] = 265
    data["nonstandard_rate"] = (data.RatecodeID != 1).astype(int)
    passenger_ok = data.passenger_count.between(1, 6) & (data.passenger_count % 1 == 0)
    data["passenger_unknown"] = (~passenger_ok).astype(int)
    data.loc[~passenger_ok, "passenger_count"] = np.nan
    data["airport_trip"] = (data.PULocationID.isin(AIRPORTS) | data.DOLocationID.isin(AIRPORTS)).astype(int)
    data["generous_tip"] = (data.tip_amount >= .25 * data.fare_amount).astype(int)
    data["tip_pct"] = 100 * data.tip_amount / data.fare_amount
    data["pickup_hour"] = data.tpep_pickup_datetime.dt.hour
    data["day_of_week"] = data.tpep_pickup_datetime.dt.dayofweek
    data["hour_sin"] = np.sin(2 * np.pi * data.pickup_hour / 24)
    data["hour_cos"] = np.cos(2 * np.pi * data.pickup_hour / 24)
    data["fare_band"] = pd.cut(data.fare_amount, [0, 10, 20, 40, 80, np.inf], labels=["0–10", "10–20", "20–40", "40–80", "80+"]).astype(str)
    data["distance_band"] = pd.cut(data.trip_distance, [0, 2, 5, 10, 20, np.inf], labels=["0–2", "2–5", "5–10", "10–20", "20+"]).astype(str)
    data["duration_band"] = pd.cut(data.duration_minutes, [0, 10, 20, 40, 60, np.inf], labels=["0–10", "10–20", "20–40", "40–60", "60+"]).astype(str)
    if zones is None:
        zones = pd.read_csv(RAW / "taxi_zone_lookup.csv")
    lookup = zones[["LocationID", "Borough", "Zone"]].rename(columns={"LocationID": "PULocationID", "Borough": "pickup_borough", "Zone": "pickup_zone"})
    data = data.merge(lookup, on="PULocationID", how="left", validate="many_to_one")
    data["pickup_borough"] = data.pickup_borough.fillna("Unknown")
    record("Retain flagged cases", len(data), "flag unknown zones, nonstandard rates and unknown passengers")
    return data.reset_index(drop=True), pd.DataFrame(audit)


def payment_audit(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for payment, group in raw.groupby("payment_type", dropna=False):
        valid = group.loc[(group.fare_amount > 0) & (group.tip_amount >= 0)]
        rows.append({"payment_type": str(payment), "trips": len(group), "valid_fare_trips": len(valid),
                     "recorded_nonzero_tip_rate": float((valid.tip_amount > 0).mean()),
                     "recorded_25pct_rate": float((valid.tip_amount >= .25 * valid.fare_amount).mean()),
                     "interpretation": "observable target" if payment == 1 else "not an observable card-tip target"})
    return pd.DataFrame(rows)
