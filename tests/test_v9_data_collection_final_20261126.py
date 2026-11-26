"""Data-collection safety, lineage, and explicit AI staging, V9.0.0."""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import pytest

from suite_gui import experimental_data as data


def pair(run_id="run-1", **outcome_updates):
    snapshot = json.dumps({"scale_mmol": 0.2, "resin": "2-CTC"})
    cleavage = {"run_id":run_id, "work_item_id":"work-A", "product":"Pep-A", "sequence":"ACD",
                "tfa_ml":5.0, "cleavage_eq":80, "planner_snapshot_json":snapshot}
    outcome = {"run_id":run_id, "work_item_id":"work-A", "product":"Pep-A", "sequence":"ACD",
               "stage":"cleavage", "result":"Success", "yield_percent":68.1,
               "purity_percent":97.4, "planner_snapshot_json":snapshot}
    outcome.update(outcome_updates)
    return cleavage, outcome


def test_final_result_two_rows_one_run_and_readiness(tmp_path):
    db = tmp_path / "lab.sqlite"
    cleavage, outcome = pair()
    saved = data.add_final_measurements(cleavage, outcome, db)
    assert saved["cleavage"]["run_id"] == saved["outcome"]["run_id"] == "run-1"
    assert data.record_counts(db)["cleavage"] == 1
    assert data.record_counts(db)["outcome"] == 1
    metrics = data.data_health(db)["data_collection_readiness"]
    assert (metrics["verified_measured_outcomes"],metrics["independent_run_ids"],metrics["distinct_sequences"]) == (1,1,1)
    assert metrics["model_ready"] is None  # do not promise ML validation


def test_atomic_rollback_when_second_insert_has_foreign_key_error(tmp_path):
    db = tmp_path / "lab.sqlite"
    cleavage, outcome = pair()
    outcome["source_id"] = "nonexistent-source-id"
    with pytest.raises(sqlite3.IntegrityError):
        data.add_final_measurements(cleavage, outcome, db)
    assert data.record_counts(db)["cleavage"] == 0
    assert data.record_counts(db)["outcome"] == 0


@pytest.mark.parametrize("field, value", [("purity_percent",101), ("purity_percent",float('nan')),
                                         ("yield_percent",-1), ("yield_percent",float('inf')),
                                         ("crude_g",-0.1), ("yield_percent", "not a number")])
def test_invalid_measured_result_does_not_create_evidence(tmp_path, field, value):
    db = tmp_path / "lab.sqlite"
    cleavage, outcome = pair(**{field:value})
    with pytest.raises(ValueError):
        data.add_final_measurements(cleavage, outcome, db)
    assert data.record_counts(db)["outcome"] == 0
    assert data.record_counts(db)["cleavage"] == 0


def test_above_100_yield_can_be_kept_as_incomplete_but_not_verified(tmp_path):
    db = tmp_path / "lab.sqlite"
    cleavage, outcome = pair(yield_percent=115.0)
    with pytest.raises(ValueError,match="100%"):
        data.add_final_measurements(cleavage, outcome, db)
    saved = data.add_final_measurements(cleavage, outcome, db, outcome_status="incomplete")
    assert saved["outcome"]["status"] == "incomplete"
    report = data.data_health(db)["data_collection_readiness"]
    assert report["verified_measured_outcomes"] == 0
    assert report["awaiting_review"] == 1


def test_mismatched_run_rejected_before_write(tmp_path):
    db = tmp_path / "lab.sqlite"
    cleavage, outcome = pair()
    outcome["run_id"] = "another"
    with pytest.raises(ValueError,match="same Work Item and Run"):
        data.add_final_measurements(cleavage, outcome, db)
    assert not db.exists()


def test_export_only_verified_actuals_and_preserve_provenance(tmp_path):
    db = tmp_path / "lab.sqlite"
    first, first_result = pair()
    saved = data.add_final_measurements(first, first_result, db)
    second, second_result = pair("run-2", yield_percent=108.0)
    data.add_final_measurements(second, second_result, db, outcome_status="incomplete")
    output = tmp_path / "review.csv"
    result = data.export_verified_outcomes_csv(output, db)
    assert result["requires_ai_review"] and result["rows"] == 1
    with output.open(encoding="utf-8-sig",newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows)==1
    assert rows[0]["lab_record_id"] == saved["outcome"]["record_id"]
    assert rows[0]["run_id"] == "run-1"
    assert rows[0]["scale_mmol"] == ""  # frozen plan != observed scale
    assert rows[0]["planned_scale_mmol"] == "0.2"
    assert rows[0]["actual_yield_percent"] == "68.1"
    assert rows[0]["product_path"] == ""  # deliberately not inferred
    assert rows[0]["chemistry"] == ""
    assert not (tmp_path / "ai_excel_reviewed_v9.json").exists()


def test_repeated_run_is_flagged_as_review_not_deleted(tmp_path):
    db = tmp_path / "lab.sqlite"
    one,two = pair()
    data.add_final_measurements(one,two,db)
    data.add_outcome(two,db,status="verified")
    health=data.data_health(db)["data_collection_readiness"]
    assert health["possible_duplicate_measurement_groups"] == 1
    assert health["independent_run_ids"] == 1
    assert health["verified_measured_outcomes"] == 2
    assert health["review_actions"]


def test_empty_export_does_not_write_or_overwrite(tmp_path):
    db = tmp_path / "lab.sqlite"
    target = tmp_path / "review.csv"
    target.write_text("existing data",encoding="utf-8")
    with pytest.raises(ValueError,match="No verified"):
        data.export_verified_outcomes_csv(target,db)
    assert target.read_text(encoding="utf-8")=="existing data"


@pytest.mark.parametrize("value", [-0.1, float("nan"), float("inf"), "wrong unit"])
def test_measured_loading_must_be_finite_and_nonnegative(tmp_path, value):
    db = tmp_path / "lab.sqlite"
    with pytest.raises(ValueError):
        data.add_record("loading", {"resin_type": "2-CTC", "amino_acid_raw": "Fmoc-Ala-OH",
                                    "loading_rate_mmol_g":value}, db)
    assert data.record_counts(db)["loading"] == 0


def test_verified_csv_is_readable_in_existing_ai_review_pipeline(tmp_path):
    from suite_gui.ai_excel_core_v9 import preview_file, normalize_preview, ml_readiness_report
    db = tmp_path / "lab.sqlite"
    data.add_final_measurements(*pair(), db)
    exported = tmp_path / "lab.csv"
    data.export_verified_outcomes_csv(exported, db)
    preview=preview_file(exported)
    assert preview.mapping["actual_yield_percent"] == "actual_yield_percent"
    reviewed, _ = normalize_preview(preview)
    assert len(reviewed) == 1
    assert reviewed.iloc[0]["actual_yield_percent"] == 68.1
    assert ml_readiness_report(reviewed)["targets"]["actual_yield_percent"]["ready"] is False


def test_controller_keeps_frozen_planner_context_on_both_linked_rows(tmp_path):
    from types import SimpleNamespace
    from suite_gui import experimental_workflow
    db = tmp_path / "lab.sqlite"
    gui = SimpleNamespace(
        pm_items=[{"peptide":"Pep-A", "sequence":"ACD", "scale":"0.2", "resin":"2-CTC"}],
        _v2097_active_index=0, experimental_db_path=db,
    )
    cleavage = {"product":"Pep-A", "sequence":"ACD", "tfa_ml":2.0}
    outcome = {"product":"Pep-A", "sequence":"ACD", "stage":"cleavage", "yield_percent":60.5}
    saved = experimental_workflow.add_final_measurements(gui, cleavage, outcome)
    assert saved["cleavage"]["run_id"] == saved["outcome"]["run_id"]
    assert saved["cleavage"]["work_item_id"] == saved["outcome"]["work_item_id"]
    assert saved["cleavage"]["planner_snapshot_json"] == saved["outcome"]["planner_snapshot_json"]
    assert json.loads(saved["outcome"]["planner_snapshot_json"])["sequence"] == "ACD"
    export=experimental_workflow.export_verified_lab_qc(gui,tmp_path/"lab.csv")
    assert export["rows"] == 1


def test_loading_health_optimized_loo_matches_previous_implementation():
    import random
    from suite_gui.experimental_reporting import _loading_leave_one_out_error
    rng=random.Random(42)
    for n in range(1,35):
        for _ in range(10):
            values=[rng.choice([0.0,0.25,0.5,1.0,1.5,2.0]) for _ in range(n)]
            expected=[]
            if n>=2:
                for i,observed in enumerate(values):
                    peers=values[:i]+values[i+1:]
                    expected.append(abs(observed-sorted(peers)[len(peers)//2]))
            actual, count=_loading_leave_one_out_error({('r','AA'):values})
            assert count == len(expected)
            assert actual == pytest.approx(sum(expected)/len(expected)) if expected else actual is None
