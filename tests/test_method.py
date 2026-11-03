import numpy as np
import pandas as pd
import pytest
from taxi_tip.data import clean_trips, read_split
from taxi_tip.evaluation import choose_threshold, metrics, paired_bootstrap
from taxi_tip.models import feature_columns, make_pipeline
from taxi_tip.config import FEATURE_GROUPS, FORBIDDEN


@pytest.fixture
def zones():
    return pd.DataFrame({"LocationID": [1, 132, 138, 161, 265], "Borough": ["EWR", "Queens", "Queens", "Manhattan", "Unknown"], "Zone": ["EWR", "JFK", "LGA", "Midtown", "Unknown"]})


@pytest.fixture
def raw():
    n = 12
    return pd.DataFrame({"tpep_pickup_datetime": pd.date_range("2026-05-01", periods=n, freq="h"),
                         "tpep_dropoff_datetime": pd.date_range("2026-05-01 00:20", periods=n, freq="h"),
                         "payment_type": [1]*n, "fare_amount": [20.]*n,
                         "tip_amount": [0., 5., 4., 8.]*3, "total_amount": [30.]*n,
                         "trip_distance": [3.]*n, "PULocationID": [161]*n, "DOLocationID": [132]*n,
                         "passenger_count": [1.]*n, "RatecodeID": [1.]*n,
                         "extra": [0.]*n, "mta_tax": [.5]*n, "tolls_amount": [0.]*n,
                         "improvement_surcharge": [1.]*n, "congestion_surcharge": [2.5]*n,
                         "Airport_fee": [0.]*n, "cbd_congestion_fee": [.75]*n})


def test_target_and_observability(raw, zones):
    raw.loc[0, "payment_type"] = 2
    raw.loc[2, "payment_type"] = 0
    raw.loc[3, "payment_type"] = 6
    raw.loc[4, "fare_amount"] = 0
    clean, audit = clean_trips(raw, zones)
    assert len(clean) == 8
    assert clean.iloc[0].generous_tip == 1  # exactly 25% is positive
    assert clean.payment_type.eq(1).all()
    assert audit.removed.sum() == 4


def test_invalid_journeys_and_flags(raw, zones):
    raw.loc[0, "trip_distance"] = 0
    raw.loc[1, "tpep_dropoff_datetime"] = raw.loc[1, "tpep_pickup_datetime"]
    raw.loc[2, "tip_amount"] = -1
    raw.loc[3, "PULocationID"] = 264
    raw.loc[4, "passenger_count"] = 0
    raw.loc[5, "RatecodeID"] = 2
    raw.loc[6, "extra"] = -2
    clean, _ = clean_trips(raw, zones)
    assert len(clean) == 8
    assert clean.unknown_zone.sum() == 1
    assert clean.passenger_unknown.sum() == 1
    assert clean.nonstandard_rate.sum() == 1


def test_leak_columns_cannot_change_predictions(raw, zones):
    clean, _ = clean_trips(raw, zones)
    pipeline = make_pipeline(list(FEATURE_GROUPS)).fit(clean, clean.generous_tip)
    altered = clean.copy()
    for column in FORBIDDEN:
        altered[column] = np.arange(len(clean)) * 10000
    np.testing.assert_array_equal(pipeline.predict_proba(clean), pipeline.predict_proba(altered))
    numeric, categories = feature_columns(list(FEATURE_GROUPS))
    assert not FORBIDDEN.intersection(numeric + categories)


def test_validation_cannot_refit_preprocessing(raw, zones):
    clean, _ = clean_trips(raw, zones)
    pipeline = make_pipeline(["fare", "geography"]).fit(clean, clean.generous_tip)
    imputer = pipeline.named_steps["preprocess"].named_transformers_["numeric"].named_steps["impute"]
    before = imputer.statistics_.copy()
    validation = clean.copy()
    validation["fare_amount"] = 1000000
    validation["PULocationID"] = 99999
    pipeline.predict_proba(validation)
    np.testing.assert_array_equal(before, imputer.statistics_)


def test_temporal_filter_boundaries(raw, tmp_path):
    raw.loc[:3, "tpep_pickup_datetime"] = pd.to_datetime(["2026-04-30 23:59", "2026-05-01", "2026-06-01", "2026-07-01"], format="mixed")
    path = tmp_path / "trips.parquet"
    raw.to_parquet(path)
    assert read_split("validation", path).tpep_pickup_datetime.dt.month.eq(6).all()
    assert len(read_split("test", path)) == 1


def test_cost_threshold_and_bootstrap():
    y = np.array([0, 0, 1, 1]*10)
    scores = np.array([.1, .2, .7, .8]*10)
    threshold, table = choose_threshold(y, scores)
    assert metrics(y, scores, threshold)["cost_per_trip"] == 0
    assert .2 < threshold <= .7
    intervals = paired_bootstrap(y, scores, np.full(len(y), .5), threshold, .5, 100)
    assert len(intervals) == 15
    assert (intervals.upper_95 >= intervals.lower_95).all()


def test_final_is_idempotent_without_loading_data(tmp_path, monkeypatch):
    from taxi_tip import workflow
    monkeypatch.setattr(workflow, "ARTIFACTS", tmp_path)
    (tmp_path / "final.json").write_text('{"status": "saved"}')
    monkeypatch.setattr(workflow, "read_split", lambda *args: pytest.fail("July must not be reread"))
    assert workflow.final_evaluate() == {"status": "saved"}


def test_development_refuses_after_test_opened(tmp_path, monkeypatch):
    from taxi_tip import workflow
    monkeypatch.setattr(workflow, "ARTIFACTS", tmp_path)
    (tmp_path / "july.lock").write_text("locked")
    with pytest.raises(RuntimeError, match="frozen"):
        workflow.develop()
