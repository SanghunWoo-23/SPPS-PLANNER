"""Independent chemistry, process ML, Excel, cancellation, evidence regression."""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

import pandas as pd
import pytest

from spps_planner.mass_balance_v9 import calculate_mass_states
from spps_planner.structure_crosscheck_v9 import independent_mass_check
from spps_planner.research_assistant_v9 import build_research_brief,search_local_evidence
from suite_gui.auto_plan_option_v9 import build_review_draft
from suite_gui.ai_excel_core_v9 import (
    create_process_excel_template,preview_file,normalize_preview,
    save_reviewed_dataset,load_reviewed_dataset,audit_reviewed_data)
from suite_gui.process_ai_v9 import train_stage_advisor,advise_stage


def test_rdkit_simple_macrocycle_matches_independent_mass_formula():
    expected=calculate_mass_states('SVS','2-CTC',side_chain_mode='none')
    outcome=independent_mass_check('SVS',expected=expected)
    if outcome['status']=='OPTIONAL_RDKIT_NOT_INSTALLED': pytest.skip('Optional RDKit not installed')
    assert outcome['status']=='CROSSCHECK_PASS'
    assert outcome['linear_formula']=='C11H21N3O6'
    assert outcome['cyclic_formula']=='C11H19N3O5'
    assert outcome['linear_mw']-outcome['cyclic_mw']==pytest.approx(18.015,abs=.002)


def test_rdkit_withholds_unsupported_annotation_and_amide():
    assert independent_mass_check('dS-dV-dS')['status']=='WITHHELD_UNSUPPORTED_TOPOLOGY'
    assert independent_mass_check('K(GGEP)')['status']=='WITHHELD_UNSUPPORTED_TOPOLOGY'
    expected=calculate_mass_states('SVS','Rink Amide AM',side_chain_mode='none')
    assert independent_mass_check('SVS',expected=expected)['status']=='WITHHELD_TERMINI_MISMATCH'


def test_auto_plan_process_risks_and_source_only():
    draft=build_review_draft('SVS',.1,'2-CTC',.7,'DIC/HOBt',1,
                             product_path='head_to_tail_protected',side_chain_mode='none')
    assert draft['process_review']['status']=='BLOCKED_REQUIRES_REVIEW'
    assert [s['id'] for s in draft['process_review']['stages']][:3]==['assembly','selective_cleavage','cyclization']
    assert draft['process_review']['stages'][2]['theoretical_mw_g_mol']==pytest.approx(273.29)
    assert draft['research_assistant']['references']
    assert draft['structure_crosscheck']['status'] in ('CROSSCHECK_PASS','OPTIONAL_RDKIT_NOT_INSTALLED')


def test_research_assistant_has_real_source_links_not_generated_conditions():
    entries=search_local_evidence('DIC Oxyma HCN')
    assert any('2020' in e['id'] for e in entries)
    assert all(e['url'].startswith('https://') for e in entries)
    brief=build_research_brief('ASCD','head_to_tail_protected','2-CTC',{'system_id':'DIC_OXYMA'})
    assert any('HCN' in r['id'] for r in brief['references'])
    assert brief['review_required'] is True


def test_process_excel_roundtrip_and_quality(tmp_path):
    path=create_process_excel_template(tmp_path/'process.xlsx')
    from openpyxl import load_workbook
    book=load_workbook(path)
    book['Process_Runs'].append(['SVS','RUN-1','cyclic_protected','cyclization','EDC/HOBt','1% TFA',
                                 .1,.7,'2-CTC','DIC/HOBt',36,1, None,65,None,None,None,None,55,
                                 '1:S(tBu);3:S(tBu)','HPLC-A',386.5])
    book.save(path)
    preview=preview_file(path)
    assert preview.mapping['cyclization_yield_percent']=='Cyclization yield %'
    frame,report=normalize_preview(preview)
    assert frame['cyclization_yield_percent'].iloc[0]==65
    assert frame['protection_profile'].iloc[0]=='1:S(tBu);3:S(tBu)'
    assert frame['observed_mz'].iloc[0]==386.5
    assert report['accepted_rows']==1


def _data(n=30, *, protected=False, same_id=False):
    rows=[]
    for i in range(n):
        rows.append(dict(sequence='A'*(i+5),scale_mmol=.1+(.02*(i%3)),loading_mmol_g=.7,
                resin='2-CTC',chemistry='DIC/HOBt',product_path='cyclic_protected' if protected else 'cyclic_deprotected',
                reaction_step='cyclization',reaction_method='EDC/HOBt',reaction_time_h=36,
                reaction_concentration_mm=1.0,protection_profile='1:S(tBu)' if protected else '',
                cyclization_yield_percent=20+i*.75,run_id='RUN-1' if same_id else f'RUN-{i}'))
    return pd.DataFrame(rows)


def test_reaction_ml_withholds_missing_protecting_group_description(tmp_path):
    records=_data(protected=True)
    records['protection_profile']=''
    outcome=train_stage_advisor(records,'cyclization_yield_percent',tmp_path,'dataset-sha')
    assert outcome['status']=='WITHHELD_UNRELIABLE'
    assert 'protecting-group' in outcome['reason']


def test_reaction_ml_withholds_conflicting_run_ids(tmp_path):
    output=train_stage_advisor(_data(same_id=True),'cyclization_yield_percent',tmp_path,'digest')
    assert output['status']=='WITHHELD_UNRELIABLE'


def test_distinct_stage_ids_are_not_false_duplicate_ids():
    data=pd.DataFrame([{'sequence':'SVS','run_id':'A1','reaction_step':'coupling','coupling_conversion_percent':80},
                       {'sequence':'SVS','run_id':'A1','reaction_step':'cyclization','cyclization_yield_percent':65}])
    assert audit_reviewed_data(data)['duplicate_run_ids']==0


def test_stage_training_is_review_only_and_blocks_stale_models(tmp_path):
    rows=_data(30)
    local=tmp_path/'data';model_dir=tmp_path/'models'
    save_reviewed_dataset(rows,{},'local',local)
    source,dataset=load_reviewed_dataset(local)
    metadata=train_stage_advisor(source,'cyclization_yield_percent',model_dir,dataset['dataset_sha256'])
    assert metadata['status']=='EXPERIMENTAL_REVIEW_ONLY'
    assert metadata['chosen_candidate'] in ('RandomForest','ExtraTrees')
    context=source.iloc[10].to_dict()
    checked=advise_stage(context,local,model_dir,'cyclization_yield_percent')
    assert checked['status']=='EXPLORATORY_PREDICTION'
    assert 0<=checked['prediction']<=100
    context['product_path']='branched_protected'
    assert advise_stage(context,local,model_dir,'cyclization_yield_percent')['status']=='WITHHELD'
    save_reviewed_dataset(rows.iloc[:28],{},'new import',local)
    assert advise_stage(source.iloc[10].to_dict(),local,model_dir,'cyclization_yield_percent')['status']=='WITHHELD'


def test_group_split_conformal_uses_reserved_calibration_groups(tmp_path):
    outcome=train_stage_advisor(_data(50),'cyclization_yield_percent',tmp_path,'digest')
    assert outcome['status']=='EXPERIMENTAL_REVIEW_ONLY'
    assert outcome['calibration']['kind']=='GROUP_SPLIT_CONFORMAL_EXCHANGEABILITY_ASSUMED'
    assert outcome['calibration']['calibration_sequence_groups']>=10


@pytest.mark.skipif(os.name!='nt' and not os.getenv('DISPLAY'),reason='Needs a Tk display')
def test_isolated_process_training_can_be_cancelled_without_widget_corruption(tmp_path):
    import tkinter as tk
    from suite_gui.ai_background_v9 import UiBackgroundRunner
    root=tk.Tk();root.withdraw()
    try:
        child=tk.Toplevel(root)
        state=[];runner=UiBackgroundRunner(child,lambda busy:state.append(busy),poll_ms=10)
        # Nonexistent dataset: might fail quickly, but cancellation must never crash Tk.
        assert runner.submit_training_process('linear',tmp_path/'empty',tmp_path/'models',
               'actual_yield_percent',lambda _:state.append('done'),lambda _:state.append('failed'))
        assert runner.cancel_training() in (True,False)
        for _ in range(4):root.update();time.sleep(.01)
        assert not runner.busy
        assert 'done' not in state
        runner.close()
    finally:root.destroy()


def test_one_click_stage_training_splits_topologies_instead_of_mixing(tmp_path):
    from suite_gui.process_ai_v9 import train_partitioned_stage_advisors
    prepared=_data(30)
    protected=_data(2,protected=True)
    protected['run_id']=['protected-1','protected-2']
    mixed=pd.concat([prepared,protected],ignore_index=True)
    result=train_partitioned_stage_advisors(mixed,'cyclization_yield_percent',tmp_path,'dataset-sha')
    assert result['status']=='STAGE_PARTITIONS_REVIEW_ONLY'
    assert result['models']['cyclic_deprotected']['status']=='EXPERIMENTAL_REVIEW_ONLY'
    assert result['models']['cyclic_protected']['status']=='WITHHELD_UNRELIABLE'
    assert result['trained_models']==1


@pytest.mark.skipif(os.name!='nt' and not os.getenv('DISPLAY'),reason='Needs Tk display')
def test_isolated_stage_process_finishes_and_keeps_tk_responsive(tmp_path):
    import tkinter as tk
    from suite_gui.ai_background_v9 import UiBackgroundRunner
    source=_data(30)
    data=tmp_path/'data'
    save_reviewed_dataset(source,{},'measured-source',data)
    root=tk.Tk();root.withdraw()
    try:
        child=tk.Toplevel(root)
        events=[]
        runner=UiBackgroundRunner(child,lambda busy:events.append(('busy',busy)),poll_ms=12)
        assert runner.submit_training_process('stage',data,tmp_path/'models',
                   'cyclization_yield_percent',lambda output:events.append(('success',output)),
                   lambda error:events.append(('error',str(error))))
        root.after(40,lambda:events.append(('tick',True)))
        deadline=time.monotonic()+24
        while time.monotonic()<deadline and not any(x[0] in ('error','success') for x in events):
            root.update();time.sleep(.008)
        assert ('tick',True) in events
        assert any(x[0]=='success' for x in events),events[-4:]
        assert not runner.busy
        runner.close()
    finally:root.destroy()


def test_observed_process_feedback_keeps_stage_endpoints_separate():
    from suite_gui.experiment_feedback_v9 import summarize_stage_feedback
    records=pd.DataFrame([
       {'run_id':'X1','sequence':'SVS','reaction_step':'cyclization','cyclization_yield_percent':55},
       {'run_id':'X1','sequence':'SVS','reaction_step':'purification','purification_recovery_percent':60},
       {'run_id':'X2','sequence':'AVS','reaction_step':'cyclization','cyclization_yield_percent':65}])
    summary=summarize_stage_feedback(records)
    assert summary['stage_summaries']['cyclization']['median_observed_percent']==60
    assert summary['stage_summaries']['purification']['median_observed_percent']==60
    assert summary['runs_with_multiple_measured_stages']['X1']==['cyclization','purification']
    assert 'overall_yield' not in summary
