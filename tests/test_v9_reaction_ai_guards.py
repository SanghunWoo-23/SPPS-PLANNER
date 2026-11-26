"""Fail-closed reagent entry and AI topology guards, without changing SPPS recipes."""
from __future__ import annotations

from copy import deepcopy
import pandas as pd
import pytest

from spps_planner.reaction_planner_v9 import (
    ReactionPlanError, prepare_reaction_review, validate_stored_reaction_review,
)
from suite_gui.ai_excel_core_v9 import advise_from_local_data,save_reviewed_dataset


def _good():
    return prepare_reaction_review('dS-dV-dS','2-CTC',scale_mmol=.2,copies=1,
        concentration_mm=1.,equivalents={'DIC':3,'HOBt':3},
        solvent='DMF',reaction_time_h=36.)


@pytest.mark.parametrize('params',[
    {'equivalents':{'DIC':True,'HOBt':3}},
    {'reaction_time_h':True},
    {'concentration_mm':False},
    {'temperature_c':True},
    {'reaction_type':[]},
    {'method_id':[]},
    {'solvent':{}},
    {'equivalents':[]},
])
def test_invalid_operator_inputs_fail_closed(params):
    with pytest.raises(ReactionPlanError):
        prepare_reaction_review('dS-dV-dS','2-CTC',scale_mmol=.2,**params)


def test_forged_reagent_name_is_handled_as_validation_error():
    bad=deepcopy(_good())
    bad['reagents'][0]['name']=['unhashable']
    with pytest.raises(ReactionPlanError,match='name must be text'):
        validate_stored_reaction_review(bad,sequence='dS-dV-dS',resin='2-CTC',scale_mmol=.2,copies=1)


def test_duplicate_reagent_name_is_rejected():
    bad=deepcopy(_good())
    bad['reagents'][1]['name']='DIC'
    with pytest.raises(ReactionPlanError,match='must not repeat'):
        validate_stored_reaction_review(bad,sequence='dS-dV-dS',resin='2-CTC',scale_mmol=.2,copies=1)


def test_ai_must_not_predict_cyclic_yield_from_untyped_excel(tmp_path):
    data_dir=tmp_path/'data'
    frame=pd.DataFrame([{'sequence':'dS-dV-dS','actual_yield_percent':60.}])
    save_reviewed_dataset(frame,{},'source',data_dir)
    result=advise_from_local_data({'sequence':'dS-dV-dS','product_path':'head_to_tail_protected'},
                                  data_dir,tmp_path/'models')
    assert result['status']=='TOPOLOGY_NOT_MODELED'
    assert result['prediction'] is None
    # Untyped linear observations are not comparable evidence for cyclic products.
    assert result['similar_runs'] == []


def test_ai_ordinary_linear_still_shows_similar_runs(tmp_path):
    data_dir=tmp_path/'data'
    frame=pd.DataFrame([{'sequence':'ACD','actual_yield_percent':55.}])
    save_reviewed_dataset(frame,{},'source',data_dir)
    result=advise_from_local_data({'sequence':'ACD','product_path':'linear_deprotected'},
                                  data_dir,tmp_path/'models')
    assert result['status']=='SIMILAR_EXPERIMENTS_ONLY'
    assert result['similar_runs']
