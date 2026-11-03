import json
import pytest
from taxi_tip import workflow


def test_fingerprint_change_stops_before_opening_july(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "ARTIFACTS", tmp_path)
    trip_file = tmp_path / "trips"
    trip_file.write_text("changed")
    monkeypatch.setattr(workflow, "TRIPS", trip_file)
    selection = {"data_sha256": "original", "zones_sha256": "z", "model_sha256": "m", "depth2_sha256": "d"}
    (tmp_path / "selection.json").write_text(json.dumps(selection))
    monkeypatch.setattr(workflow, "read_split", lambda *args: pytest.fail("July must remain unopened"))
    with pytest.raises(RuntimeError, match="fingerprint changed"):
        workflow.final_evaluate()
    assert not (tmp_path / "july.lock").exists()


def test_interrupted_scoring_cannot_silently_repeat(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "ARTIFACTS", tmp_path)
    (tmp_path / "selection.json").write_text("{}")
    (tmp_path / "july.lock").write_text("{}")
    monkeypatch.setattr(workflow, "read_split", lambda *args: pytest.fail("July must not be reopened"))
    with pytest.raises(RuntimeError, match="without saved predictions"):
        workflow.final_evaluate()


def test_insufficient_bootstrap_rejected_before_scoring(tmp_path, monkeypatch):
    monkeypatch.setattr(workflow, "ARTIFACTS", tmp_path)
    with pytest.raises(ValueError, match="100"):
        workflow.final_evaluate(repetitions=99)
