"""V9.0.0 regression tests for data-integrity and operator-input safety."""
from copy import deepcopy
import json
import pytest

from spps_planner.mass_balance_v9 import estimate_mass_yield, checked_integer
from spps_planner.reaction_planner_v9 import (
    prepare_reaction_review, validate_stored_reaction_review, ReactionPlanError,
)
from suite_gui.auto_plan_option_v9 import preview_inputs, build_review_draft

SEQ = 'dS-dV-dS'
RESIN = '2-CTC'


def good_review():
    return prepare_reaction_review(
        SEQ, RESIN, scale_mmol=.2, copies=2,
        concentration_mm=1, solvent='DMF', reaction_time_h=36,
        equivalents={'DIC':3, 'HOBt':3},
    )


@pytest.mark.parametrize('bad', [True, False, 0, -1, 1.25, '1.25', 'nan', 'Inf', '', '1e1000000'])
def test_positive_integer_rejects_unsafe_values(bad):
    with pytest.raises(ValueError):
        checked_integer(bad, 'copies')
    with pytest.raises(ValueError):
        preview_inputs(SEQ, .1, RESIN, .8, 'DIC/HOBt', bad)


def test_integral_numeric_copies_are_accepted_without_truncation():
    assert checked_integer(2.0, 'copies') == 2
    assert preview_inputs(SEQ,.1,RESIN,.8,'DIC/HOBt','2.0')['copies']==2


@pytest.mark.parametrize('bad', [True, '1.5', -2, 'NaN', 'Inf', '1e1000000'])
def test_yield_rejects_invalid_steps_and_copies(bad):
    with pytest.raises(ValueError):
        estimate_mass_yield(200, .1, copies=bad)
    with pytest.raises(ValueError):
        estimate_mass_yield(200, .1, coupling_steps=bad)


def test_yield_arithmetic_overflow_is_explicit_error():
    with pytest.raises(ValueError, match='not finite'):
        estimate_mass_yield(1e308, 1e308)


def test_tiny_nonzero_reaction_quantity_is_not_rounded_to_zero():
    record = prepare_reaction_review(SEQ, RESIN,
            scale_mmol=1e-9, concentration_mm=1., solvent='DMF',
            reaction_time_h=24, equivalents={'DIC':1., 'HOBt':1.})
    assert record['reagents'][0]['mmol_total'] == pytest.approx(1e-9)
    assert record['volume_total_ml'] == pytest.approx(1e-6)
    json.dumps(record, allow_nan=False)


def test_reaction_overflow_rejected_before_json_export():
    with pytest.raises(ReactionPlanError, match='not a finite'):
        prepare_reaction_review(SEQ, RESIN,
            scale_mmol=1e308, concentration_mm=1e-250,
            equivalents={'DIC':1e308,'HOBt':1}, solvent='DMF', reaction_time_h=1)


def test_full_reaction_roundtrip_recomputes_mw_and_reagent_mmol():
    record=good_review()
    assert validate_stored_reaction_review(record, sequence=SEQ, resin=RESIN,
                                           scale_mmol=.2, copies=2)==record
    document=build_review_draft(SEQ,.2,RESIN,.8,'DIC/HOBt',2,
                                product_path='head_to_tail_protected',reaction_review=record)
    assert document['reaction_review']['system_id']=='DIC_HOBT'


@pytest.mark.parametrize('key,value',[
    ('protected_cyclic_mw',999.9), ('approval','APPROVED'),
    ('method_status','VALIDATED'), ('volume_total_ml',42.0),
    ('system_label','fake method'), ('scale_mmol_per_copy',.3),
    ('copies',3), ('warnings',[]),
])
def test_stale_or_forged_draft_rejected(key,value):
    record=good_review()
    record[key]=value
    with pytest.raises(ReactionPlanError):
        validate_stored_reaction_review(record, sequence=SEQ, resin=RESIN,
                                        scale_mmol=.2,copies=2)
    with pytest.raises(ValueError,match='stale or invalid'):
        build_review_draft(SEQ,.2,RESIN,.8,'DIC/HOBt',2,
                           product_path='head_to_tail_protected',reaction_review=record)


def test_unknown_or_changed_protecting_group_policy_blocks_review():
    with pytest.raises(ReactionPlanError):
        validate_stored_reaction_review(good_review(), sequence=SEQ,resin=RESIN,
                                        scale_mmol=.2,copies=2,side_chain_mode='none')
