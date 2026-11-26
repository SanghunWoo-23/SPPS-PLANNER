"""Regression: literature context must never become a recipe or silent approval."""
import json
from pathlib import Path
import pytest

from spps_planner.reaction_evidence_v9 import REACTION_REFERENCES, review_reaction_evidence
from spps_planner.reaction_planner_v9 import prepare_reaction_review, validate_stored_reaction_review, ReactionPlanError


def _draft(seq='dS-dV-dS', method='DIC_HOBT', solvent='DMF'):
    return prepare_reaction_review(seq,'2-CTC',scale_mmol=.2,copies=2,
        method_id=method,solvent=solvent,concentration_mm=1,
        reaction_time_h=36)


def test_exported_catalog_exactly_matches_runtime_registry():
    path=Path(__file__).resolve().parents[1]/'docs/REACTION_LITERATURE_V9.0.0.json'
    catalog=json.loads(path.read_text(encoding='utf-8'))
    assert catalog['version']=='V9.0.0'
    assert catalog['references']==[{'id':k,**v} for k,v in REACTION_REFERENCES.items()]
    for record in catalog['references']:
        assert record.get('pmid') or record.get('doi')
        assert record['url'].startswith('https://')


def test_draft_attaches_citable_evidence_but_no_fabricated_eq_or_approval():
    r=_draft()
    assert r['approval']=='DRAFT_NOT_APPROVED'
    assert r['method_status']=='INCOMPLETE_REVIEW_ONLY'
    assert all(q['equivalents'] is None for q in r['reagents'])
    e=r['literature_evidence']
    assert e['assessment']=='LITERATURE_CONTEXT_NOT_VALIDATED_SOP'
    assert 'MALESEVIC_2004_DILUTION' in {p['id'] for p in e['references']}
    assert 'CTC_SELECTIVE_CLEAVAGE_REVIEW' in {f['code'] for f in e['risk_flags']}
    json.dumps(r,allow_nan=False)


def test_dic_oxyma_high_severity_hcn_warning_for_dmf():
    e=_draft(method='DIC_OXYMA')['literature_evidence']
    risk=next(f for f in e['risk_flags'] if f['code']=='DIC_OXYMA_HCN')
    assert risk['severity']=='high'
    assert 'HCN' in risk['message']
    assert 'ERNY_2020_DIC_OXYMA_HCN' in risk['reference_ids']


def test_dic_oxyma_non_dmf_is_not_claimed_safe():
    e=_draft(method='DIC_OXYMA',solvent='NMP')['literature_evidence']
    risk=next(f for f in e['risk_flags'] if f['code']=='DIC_OXYMA_HCN')
    assert 'NOT evidence of safety' in risk['message']


def test_other_systems_no_misattributed_dic_oxyma_hcn():
    e=_draft(method='EDC_HOBT')['literature_evidence']
    assert not any(f['code']=='DIC_OXYMA_HCN' for f in e['risk_flags'])
    assert 'ERNY_2020_DIC_OXYMA_HCN' not in {p['id'] for p in e['references']}


def test_asp_cys_site_warnings_and_no_false_yield_probability():
    e=_draft(seq='D-S-C')['literature_evidence']
    assert {'ASP_FMOC_DEPROTECTION','CYS_ORTHOGONAL_OXIDATION_REVIEW'} <= {f['code'] for f in e['risk_flags']}
    assert 'yield_probability' not in e


def test_dform_aspartate_gets_aspartimide_caution_not_dser():
    assert 'ASP_FMOC_DEPROTECTION' in {f['code'] for f in _draft(seq='dD-S-V')['literature_evidence']['risk_flags']}
    assert 'ASP_FMOC_DEPROTECTION' not in {f['code'] for f in _draft()['literature_evidence']['risk_flags']}


def test_saved_draft_must_match_updated_provenance_and_not_approve_itself():
    r=_draft()
    validated=validate_stored_reaction_review(r,sequence='dS-dV-dS',resin='2-CTC',scale_mmol=.2,copies=2)
    assert validated==r
    r['literature_evidence']['references'][0]['url']='https://example.invalid/manipulated'
    with pytest.raises(ReactionPlanError, match='differs'):
        validate_stored_reaction_review(r,sequence='dS-dV-dS',resin='2-CTC',scale_mmol=.2,copies=2)


def test_reference_catalog_not_mutated_by_draft_edits():
    r=_draft()
    original=REACTION_REFERENCES['CONNORS_2022_PROTECTED_CYCLIZATION']['title']
    r['literature_evidence']['references'][0]['title']='wrong'
    assert REACTION_REFERENCES['CONNORS_2022_PROTECTED_CYCLIZATION']['title']==original


def test_no_method_for_unmodeled_reaction_type():
    with pytest.raises(ReactionPlanError):
        prepare_reaction_review('SGS','2-CTC',reaction_type='disulfide',scale_mmol=.1)


def test_oligomer_candidate_masses_are_stoichiometric_not_ms_peaks():
    r=_draft()
    m=r['protected_linear_mw'];water=r['loss_mw']
    entries={v['species']:v for v in r['possible_oligomers']}
    assert entries['linear_dimer_one_link']['average_neutral_mw_g_mol']==round(2*m-water,3)
    assert entries['cyclic_dimer_two_links']['average_neutral_mw_g_mol']==round(2*m-2*water,3)
    assert 'observed_ms_peak' not in r
    assert r['mass_type']=='average_neutral_mw_g_mol'
