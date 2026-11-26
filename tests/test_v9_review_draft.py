import json
import pytest
from suite_gui.auto_plan_option_v9 import build_review_draft, draft_to_json


def test_v9_draft_is_deterministic_and_keeps_unverified_conditions_blank():
    a=build_review_draft("Ac-EEMQRR-NH2", 0.2, "Rink Amide AM", 0.8, "DIC/HOBt", 1)
    b=build_review_draft("Ac-EEMQRR-NH2", 0.2, "Rink Amide AM", 0.8, "DIC/HOBt", 1)
    assert a == b
    assert a["inputs"]["resin_g"] == pytest.approx(0.25)
    assert a["cleavage"]["cocktail"] is None
    assert a["cleavage"]["time_minutes"] is None
    assert a["status"] == "DRAFT_NOT_APPROVED"
    assert "findings" in a["risk"]


def test_export_is_readable_and_marks_operator_notes_as_unapproved():
    draft=build_review_draft("ACCC", .1, "Rink Amide AM", .8, "DIC/HOBt", 1)
    doc=json.loads(draft_to_json(draft,"Need operator review"))
    assert doc["cleavage"]["tfa_basis_eq"] == 300
    assert doc["operator_notes"] == "Need operator review"
    assert doc["status"] == "DRAFT_NOT_APPROVED"

@pytest.mark.parametrize("sequence,scale,loading,copies", [
    ("", .1, .8, 1), ("GHK", 0, .8, 1), ("GHK", .1, 0, 1), ("GHK", .1, .8, 0)
])
def test_bad_inputs_rejected(sequence,scale,loading,copies):
    with pytest.raises(ValueError):
        build_review_draft(sequence,scale,"Rink Amide AM",loading,"DIC/HOBt",copies)
