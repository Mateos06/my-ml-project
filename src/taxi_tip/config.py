"""Fixed policies; none of these limits are fitted on validation or test data."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
TRIPS = RAW / "yellow_tripdata_2026_sample.parquet"
ARTIFACTS = ROOT / "artifacts"
REPORTS = ROOT / "reports"
SEED = 2026
FALSE_POSITIVE_COST = 1.0
FALSE_NEGATIVE_COST = 2.0
MIN_AP_GAIN = 0.001
AIRPORTS = {1, 132, 138}
MONEY = ["fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount",
         "improvement_surcharge", "congestion_surcharge", "Airport_fee", "cbd_congestion_fee"]
SPLITS = {"train": ("2026-05-01", "2026-06-01"),
          "validation": ("2026-06-01", "2026-07-01"),
          "test": ("2026-07-01", "2026-08-01")}
FEATURE_GROUPS = {
    "fare": (["fare_amount"], []),
    "journey": (["duration_minutes", "trip_distance", "speed_mph"], []),
    "calendar": (["hour_sin", "hour_cos"], ["day_of_week", "pickup_hour"]),
    "geography": (["airport_trip"], ["PULocationID", "DOLocationID", "pickup_borough"]),
    "passengers": ([], ["passenger_count"]),
    "rate": ([], ["RatecodeID"]),
    "fees": (["extra", "mta_tax", "tolls_amount", "improvement_surcharge",
               "congestion_surcharge", "Airport_fee", "cbd_congestion_fee"], []),
    "quality": (["unknown_zone", "nonstandard_rate", "passenger_unknown"], []),
}
FORBIDDEN = {"tip_amount", "total_amount", "generous_tip", "tip_pct", "payment_type"}
