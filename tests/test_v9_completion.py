"""Completion regression: explicit topology, stereochemistry, external-ML leakage."""
from __future__ import annotations
import math
import pytest
from spps_planner.extended_structure_v9 import graph_crosscheck
from spps_planner.mass_balance_v9 import calculate_mass_states
from suite_gui.auto_plan_option_v9 import build_review_draft


def _graph(seq,topology,sites=None):
    value=graph_crosscheck(seq,'2-CTC',side_chain_mode='explicit',topology=topology,sites=sites)
    if value['status']=='OPTIONAL_RDKIT_NOT_INSTALLED':
        pytest.skip('Optional RDKit unavailable')
    return value


@pytest.mark.parametrize('sequence,topology,expected',[
    ('SVS','head_to_tail',273.29),
    ('dS-dV-dS','head_to_tail',273.29),
    ('S(tBu)VS(tBu)','head_to_tail',385.51),
    ('K(Boc)AD(OtBu)','linear',488.585),
    ('K(GGEP)','lysine_branch',486.525),
    ('C(Acm)AC','linear',366.465),
    ('C(StBu)AC','linear',383.561),
    ('C(Trt)AC','linear',537.707),
    ('Ac-S(tBu)-V-S(tBu)-OH','linear',445.565),
])
def test_independent_graph_is_a_real_sanitized_molecule(sequence,topology,expected):
    result=_graph(sequence,topology)
    assert result['status']=='CROSSCHECK_PASS',result
    assert result['product_graph_mw']==pytest.approx(expected,abs=.035)
    assert result['product_formula'] and result['product_smiles']
    assert math.isfinite(result['product_exact_mass'])


def test_d_chirality_changes_isomeric_smiles_not_formula():
    l=_graph('SVS','head_to_tail')
    d=_graph('dS-dV-dS','head_to_tail')
    assert l['product_formula']==d['product_formula']
    assert l['product_smiles']!=d['product_smiles']


def test_disulfide_requires_both_explicit_free_cys_sites():
    outcome=_graph('SCCS','disulfide',(2,3))
    linear=_graph('SCCS','linear')
    assert outcome['status']=='CROSSCHECK_PASS'
    assert linear['product_graph_mw']-outcome['product_graph_mw']==pytest.approx(2.016,abs=.005)
    assert _graph('SCCS','disulfide',(1,2))['status'].startswith('WITHHELD')
    assert _graph('SCCS','disulfide',(2,2))['status'].startswith('WITHHELD')
    assert _graph('SCCS','disulfide',None)['status'].startswith('WITHHELD')


def test_lactam_validates_linked_sidechain_positions():
    linear=_graph('KED','linear')
    for sites in ((1,2),(1,3)):
        closed=_graph('KED','sidechain_lactam',sites)
        assert closed['status']=='CROSSCHECK_PASS',closed
        assert linear['product_graph_mw']-closed['product_graph_mw']==pytest.approx(18.015,abs=.005)
    assert _graph('KED','sidechain_lactam',(2,3))['status'].startswith('WITHHELD')
    assert _graph('K(Boc)ED','sidechain_lactam',(1,3))['status'].startswith('WITHHELD')
    assert _graph('KED(OtBu)','sidechain_lactam',(1,3))['status'].startswith('WITHHELD')


def test_unsupported_groups_and_capped_head_to_tail_fail_closed():
    assert _graph('R(Pbf)AC','linear')['status'].startswith('WITHHELD')
    assert _graph('Ac-SVS-OH','head_to_tail')['status'].startswith('WITHHELD')
    assert _graph('SVS','lysine_branch')['status'].startswith('WITHHELD')
    assert _graph('K(GGEP)','head_to_tail')['status'].startswith('WITHHELD')
    assert _graph('SVS','disulfide',(1,3))['status'].startswith('WITHHELD')


def test_auto_plan_exposes_graph_validation_without_changing_engine():
    review=build_review_draft('S(tBu)VS(tBu)',.1,'2-CTC',.7,'DIC/HOBt',1,
                              product_path='head_to_tail_protected',side_chain_mode='explicit')
    assert review['extended_structure_review']['status'] in ('CROSSCHECK_PASS','OPTIONAL_RDKIT_NOT_INSTALLED')
    assert review['mass']['values']['head_to_tail_protected_mw']==pytest.approx(385.51)
    unprotected=build_review_draft('S(tBu)VS(tBu)',.1,'2-CTC',.7,'DIC/HOBt',1,
                                   product_path='head_to_tail_deprotected',side_chain_mode='explicit')
    assert unprotected['extended_structure_review'].get('product_graph_mw',273.29)==pytest.approx(273.29,abs=.02)


def test_external_ml_blocks_any_sequence_overlap_before_predictions(tmp_path):
    from tools.external_ml_validation_v9 import evaluate_external_file
    from suite_gui.ai_excel_core_v9 import save_reviewed_dataset
    import pandas as pd
    train=tmp_path/'train'
    source=pd.DataFrame([{'sequence':'SVS','run_id':'RUN-1','product_path':'cyclic_deprotected','reaction_step':'cyclization'}])
    save_reviewed_dataset(source,{},'test',train)
    external=pd.DataFrame([{'Sequence':'S-V-S','Run ID':'OTHER-1','Product path':'cyclic_deprotected',
                            'Reaction step':'cyclization','Cyclization yield %':45}])
    path=tmp_path/'external.csv';external.to_csv(path,index=False)
    result=evaluate_external_file(train,tmp_path/'models',path,target='cyclization_yield_percent')
    assert result['status']=='WITHHELD_LEAKAGE'
    assert result['overlapping_sequence_groups']==1
    assert 'sequence' not in result


def test_crossref_metadata_opt_in_query_is_bounded_and_does_not_include_peptide_data():
    import json
    from urllib.parse import urlparse,parse_qs
    from spps_planner.online_bibliography_v9 import search_crossref_metadata
    observed=[]
    payload={'status':'ok','message':{'items':[{'DOI':'10.1002/pep2.24254',
        'title':['<i>Protected peptide cyclization</i>'],'published':{'date-parts':[[2022,3,2]]}}]}}
    def fake(url):
        observed.append(url)
        return json.dumps(payload).encode()
    response=search_crossref_metadata('protected peptide cyclization',fetch=fake)
    assert response['references'][0]['year']==2022
    assert '<' not in response['references'][0]['title']
    assert response['references'][0]['url']=='https://doi.org/10.1002/pep2.24254'
    url=urlparse(observed[0]);args=parse_qs(url.query)
    assert url.netloc=='api.crossref.org'
    assert args['query.bibliographic']==['protected peptide cyclization']
    assert 'select' in args
    with pytest.raises(ValueError):
        search_crossref_metadata('X'*161,fetch=fake)
    with pytest.raises(ValueError):
        search_crossref_metadata('a\nprivate sequence',fetch=fake)


@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'),reason='Needs Xvfb')
def test_tk_structure_review_dialog_is_reachable_and_closes_cleanly():
    import tkinter as tk
    from suite_gui.structure_review_panel_v9 import open_structure_review
    root=tk.Tk();root.withdraw()
    try:
        review=open_structure_review(root,sequence='S(tBu)VS(tBu)',resin='2-CTC')
        root.update()
        assert 'V9.0.0' in review.title()
        review.destroy();root.update()
    finally:
        root.destroy()


def test_stbu_disulfide_group_mass_matches_real_precursor_formula():
    from spps_planner.mass_balance_v9 import PROTECTING_DELTA
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    from spps_planner.extended_structure_v9 import graph_crosscheck
    # Fmoc-Cys(StBu)-OH formula C22H25NO4S2, catalog MW ~431.57.
    # Subtract Fmoc substitution from the RDKit structure to cross-check.
    v=graph_crosscheck('C(StBu)AC','2-CTC')
    assert v['status']=='CROSSCHECK_PASS'
    assert PROTECTING_DELTA['StBu']==pytest.approx(88.17,abs=.01)
    assert v['product_graph_mw']-graph_crosscheck('CAC','2-CTC')['product_graph_mw']==pytest.approx(88.175,abs=.01)


def test_checklist_crosslink_review_revalidates_saved_structure():
    from suite_gui.checklist_mass_v9 import append_crosslink_structure_review
    graph=_graph('SCCS','disulfide',(2,3))
    record={'status':'UNAPPROVED_REVIEW_ONLY','sequence':'SCCS','resin':'2-CTC',
            'topology':'disulfide','sites':(2,3),'side_chain_mode':'explicit','graph':graph}
    rows=[]
    append_crosslink_structure_review(rows,'SCCS','2-CTC',record)
    assert len(rows)==1 and rows[0]['peptide_mw']
    assert 'NO synthesis step' in rows[0]['operation']
    assert 'review pending' in rows[0]['mw_form']
    rows=[]
    append_crosslink_structure_review(rows,'SVS','2-CTC',record)
    assert len(rows)==1 and rows[0]['peptide_mw']==''
    modified=dict(record,graph={**graph,'product_graph_mw':999.})
    rows=[]
    append_crosslink_structure_review(rows,'SCCS','2-CTC',modified)
    assert rows[0]['peptide_mw']==''


def test_add_dialog_disulfide_saves_explicit_sites_and_theoretical_graph():
    from suite_gui.modules.add_peptide_dialog import build_item_payload, _dialog_values_from_item
    from types import SimpleNamespace
    data = dict(project='QA', peptide='SS', sequence='SCCS', scale='0.1', copies='1',
                resin='2-CTC', loading='0.8', reagent='DIC', additive='HOBt (anhydrous)',
                base='', solvent='DMF', preset='Custom', synthesis_form='cyclic',
                cyclic_product='disulfide', cyclic_groups='explicit',
                disulfide_site_a='2', disulfide_site_b='3')
    item = build_item_payload(SimpleNamespace(), data)
    options = item['v9_mass_options']
    assert options['disulfide_sites'] == [2, 3]
    assert options['reaction_review'] is None
    assert options['disulfide_structure_review']['status'] == 'CROSSCHECK_PASS'
    assert options['disulfide_structure_review']['product_graph_mw'] == pytest.approx(396.447, abs=0.005)
    assert _dialog_values_from_item(item)['disulfide_site_a'] == '2'
    for invalid in (dict(disulfide_site_b='2'), dict(disulfide_site_a='1'),
                    dict(sequence='C(Acm)CS', disulfide_site_a='1', disulfide_site_b='2')):
        with pytest.raises(ValueError):
            build_item_payload(SimpleNamespace(), dict(data, **invalid))

def test_disulfide_review_preserves_blocked_reaction_state():
    from suite_gui.auto_plan_evolution_v9 import review_disulfide_product
    item = review_disulfide_product('SCCS','2-CTC', {'disulfide_sites':['2','3']})
    assert item['status']=='CROSSCHECK_PASS'
    assert item['reaction_review_status']=='NOT APPROVED'
    assert item['product_graph_mw'] < item['linear_graph_mw']
    for sites in ((2,2),(1,2),None):
        assert review_disulfide_product('SCCS','2-CTC', {'disulfide_sites':sites})['status'] != 'CROSSCHECK_PASS'
