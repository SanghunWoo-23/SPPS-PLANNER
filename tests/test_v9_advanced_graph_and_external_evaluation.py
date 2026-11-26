"""V9.0.0 advanced chemistry and independent ML acceptance tests."""
from __future__ import annotations
import math
import pytest


def graph(sequence, topology='linear'):
    from spps_planner.extended_structure_v9 import graph_crosscheck
    outcome=graph_crosscheck(sequence,'2-CTC',topology=topology,side_chain_mode='explicit')
    if outcome['status']=='OPTIONAL_RDKIT_NOT_INSTALLED':
        pytest.skip('RDKit optional')
    return outcome


@pytest.mark.parametrize('sequence', ['SKS','KED','PSP','S(tBu)KS(tBu)'])
def test_backbone_cyclization_is_not_confused_by_sidechain_nitrogen(sequence):
    product=graph(sequence,'head_to_tail')
    precursor=graph(sequence,'linear')
    assert product['status']=='CROSSCHECK_PASS',product
    assert precursor['product_graph_mw'] - product['product_graph_mw']==pytest.approx(18.01528,abs=.005)
    assert product['product_smiles']


def test_one_explicit_lysine_branch_with_mainchain_ring_supported():
    product=graph('AK(GGEP)S','lysine_branch_head_to_tail')
    precursor=graph('AK(GGEP)S','lysine_branch')
    assert product['status']=='CROSSCHECK_PASS',product
    assert precursor['product_graph_mw'] - product['product_graph_mw']==pytest.approx(18.01528,abs=.005)
    assert product['product_formula'] and product['product_exact_mass']>0


@pytest.mark.parametrize('sequence', ['Ac-AK(GGEP)S-OH','K(GGEP)','AK(GGEP)S-NH2'])
def test_branch_macrocycle_fail_closed_if_unavailable_main_terminus(sequence):
    assert graph(sequence,'lysine_branch_head_to_tail')['status'].startswith('WITHHELD')


def test_existing_branch_only_mode_not_auto_cyclized():
    normal=graph('AK(GGEP)S','lysine_branch')
    assert normal['status']=='CROSSCHECK_PASS'
    assert graph('AK(GGEP)S','head_to_tail')['status'].startswith('WITHHELD')


def test_accurate_monoisotopic_mz_only_on_sanitized_graph():
    from spps_planner.ms_ions_v9 import theoretical_ms_ions,PROTON
    product=graph('SKS','head_to_tail')
    mass=product['product_exact_mass']
    ions=product['theoretical_ms_ions']
    assert ions['status']=='THEORETICAL_ONLY_NOT_OBSERVED'
    assert ions['positive_ion_candidates'][0]['mz']==pytest.approx(mass+PROTON,abs=2e-5)
    assert ions['positive_ion_candidates'][1]['mz']==pytest.approx((mass+2*PROTON)/2,abs=2e-5)
    assert ions['negative_ion_candidates'][0]['mz']==pytest.approx(mass-PROTON,abs=2e-5)
    assert 'theoretical_ms_ions' not in graph('R(Pbf)AC')
    for bad in (0,-1,math.inf,math.nan,True,'bad'):
        with pytest.raises(ValueError): theoretical_ms_ions(bad)
    with pytest.raises(ValueError): theoretical_ms_ions(mass,max_charge=1.5)


def test_external_evaluation_rejects_shared_run_id_with_distinct_sequence(monkeypatch):
    import pandas as pd
    from tools import external_ml_validation_v9 as tool
    train=pd.DataFrame([{'sequence':'SVS','run_id':'RUN-001'}])
    external=pd.DataFrame([{'sequence':'ACD','run_id':'run-001','product_path':'linear_deprotected',
                            'reaction_step':'cyclization','cyclization_yield_percent':70.0}])
    monkeypatch.setattr(tool,'load_reviewed_dataset',lambda _:(train,{'dataset_sha256':'test'}))
    monkeypatch.setattr(tool,'preview_file',lambda _:None)
    monkeypatch.setattr(tool,'normalize_preview',lambda _: (external,{}))
    outcome=tool.evaluate_external_file('train','models','dummy',target='cyclization_yield_percent',min_independent_sequences=1)
    assert outcome['status']=='WITHHELD_RUN_ID_LEAKAGE'
    assert outcome['evaluated_rows']==0


def test_external_validation_requires_distinct_predicted_groups(monkeypatch):
    import pandas as pd
    from tools import external_ml_validation_v9 as tool
    train=pd.DataFrame([{'sequence':'SVS'}])
    ext=pd.DataFrame([{'sequence':seq,'product_path':'linear_deprotected','reaction_step':'cyclization',
                       'cyclization_yield_percent':65.0}
                      for seq in ('AAA','AAC','AAD','AAE','AAF','AAG','AAH','AAI')])
    monkeypatch.setattr(tool,'load_reviewed_dataset',lambda _:(train,{'dataset_sha256':'test'}))
    monkeypatch.setattr(tool,'preview_file',lambda _:None)
    monkeypatch.setattr(tool,'normalize_preview',lambda _: (ext,{}))
    def predict(row,*_):
        return {'status':'EXPLORATORY_PREDICTION','prediction':60.0} if row['sequence']=='AAA' else {'status':'WITHHELD','reason':'out of domain'}
    monkeypatch.setattr(tool,'advise_stage',predict)
    result=tool.evaluate_external_file('train','models','dummy',target='cyclization_yield_percent',min_independent_sequences=3)
    assert result['status']=='WITHHELD_TOO_FEW_IN_DOMAIN_PREDICTIONS'
    assert result['predicted_rows']==1
    assert result['predicted_independent_sequence_groups']==1
    assert result['withheld_rows']==7


def test_external_validation_uses_true_median_for_even_row_count(monkeypatch):
    import pandas as pd
    from tools import external_ml_validation_v9 as tool
    train=pd.DataFrame([{'sequence':'SVS'}])
    ext=pd.DataFrame([{'sequence':'AAA','product_path':'linear_deprotected','reaction_step':'cyclization',
                       'cyclization_yield_percent':60.},
                      {'sequence':'AAA','product_path':'linear_deprotected','reaction_step':'cyclization',
                       'cyclization_yield_percent':70.}])
    monkeypatch.setattr(tool,'load_reviewed_dataset',lambda _:(train,{'dataset_sha256':'test'}))
    monkeypatch.setattr(tool,'preview_file',lambda _:None)
    monkeypatch.setattr(tool,'normalize_preview',lambda _: (ext,{}))
    monkeypatch.setattr(tool,'advise_stage',lambda *_:{'status':'EXPLORATORY_PREDICTION','prediction':50.,
        'calibration':{'kind':'GROUP_SPLIT_CONFORMAL_EXCHANGEABILITY_ASSUMED','group_level_radius_points':15.}})
    result=tool.evaluate_external_file('train','models','dummy',target='cyclization_yield_percent',min_independent_sequences=1)
    assert result['median_absolute_error_percent_points']==15
    assert result['sequence_balanced_mae_percent_points']==15
    assert result['empirical_row_interval_coverage']==0.5
    assert result['status']=='EXTERNAL_HOLDOUT_DESCRIPTIVE_ONLY'


def test_checklist_uses_independent_ms_ion_mz_only_for_fresh_review():
    from suite_gui.checklist_mass_v9 import append_crosslink_structure_review
    complete=graph('AK(GGEP)S','lysine_branch_head_to_tail')
    record={'status':'UNAPPROVED_REVIEW_ONLY','sequence':'AK(GGEP)S','resin':'2-CTC',
            'topology':'lysine_branch_head_to_tail','sites':None,
            'side_chain_mode':'explicit','graph':complete}
    table=[]
    append_crosslink_structure_review(table,'AK(GGEP)S','2-CTC',record)
    assert len(table)==1
    assert table[0]['peptide_mw']==f"{complete['product_graph_mw']:.3f}"
    assert '[M+H]+' in table[0]['note']
    assert 'NOT an observed' in table[0]['note']
    stale=[]
    append_crosslink_structure_review(stale,'AK(GGEP)A','2-CTC',record)
    assert stale[0]['peptide_mw']==''
    assert '[M+H]+' not in stale[0]['note']


@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'),reason='Needs an actual Tk display or Xvfb')
def test_gui_can_select_branch_mainchain_macrocycle_and_render_ms_candidate():
    import tkinter as tk
    from tkinter import ttk
    from suite_gui.structure_review_panel_v9 import open_structure_review
    root=tk.Tk();root.withdraw()
    try:
        window=open_structure_review(root,sequence='AK(GGEP)S',resin='2-CTC')
        def descend(parent):
            for child in parent.winfo_children():
                yield child
                yield from descend(child)
        selector=next(c for c in descend(window) if isinstance(c,ttk.Combobox))
        selector.set('Main-chain head-to-tail + Lys branch')
        compute=next(c for c in descend(window) if isinstance(c,ttk.Button) and c.cget('text')=='Compute molecular graph')
        compute.invoke()
        root.update()
        from tkinter.scrolledtext import ScrolledText
        details=next(c for c in descend(window) if isinstance(c,ScrolledText))
        content=details.get('1.0','end')
        assert 'CROSSCHECK_PASS' in content
        assert 'theoretical_ms_ions' in content
        window.destroy()
    finally:
        root.destroy()
