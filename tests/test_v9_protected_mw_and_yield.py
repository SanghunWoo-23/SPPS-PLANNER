"""V9 protected amino-acid and cyclization mass QA (source-level)."""
import math
import pytest
from spps_planner.parser import parse_sequence
from spps_planner.database import load_compounds, validate_compounds_dataframe
from spps_planner.mass_balance_v9 import calculate_mass_states, estimate_mass_yield, MassBalanceError, WATER_MW
from spps_planner.engine import PlanInput, generate_step_matrix


def test_h_ser_protected_is_one_reagent_and_mw_matches_catalog():
    parsed=parse_sequence('H-Ser(tBu)-OH')
    assert parsed.core_tokens == ['H-Ser(tBu)-OH']
    db=load_compounds()
    h_row=db[db['Token']=='H-Ser(tBu)-OH'].iloc[0]
    assert float(h_row['Reagent MW (g/mol)'])==pytest.approx(161.20,abs=.05)
    states=calculate_mass_states('H-Ser(tBu)-OH','2-CTC')
    assert states['linear_protected_mw']==pytest.approx(161.2,abs=.06)
    assert states['linear_deprotected_mw']==pytest.approx(105.09,abs=.06)


def test_no_fmoc_deprotection_step_for_free_alpha_amine():
    mat=generate_step_matrix(PlanInput(sequence='H-Ser(tBu)-OH',resin='2-CTC',scale_mmol=.1))
    assert not any('Fmoc removal'==u for u in mat['unit'].astype(str))
    assert mat.iloc[0]['reagent_mw']==pytest.approx(161.20,abs=.01)
    ordinary=generate_step_matrix(PlanInput(sequence='GSG',resin='2-CTC',scale_mmol=.1))
    assert 'Fmoc removal' in ordinary['unit'].values


def test_distinct_dde_and_ivdde_mass_and_parser():
    assert parse_sequence('K(Dde)').core_tokens==['K(Dde)']
    assert parse_sequence('K(ivDde)').core_tokens==['K(ivDde)']
    db=load_compounds().set_index('Token')
    assert float(db.loc['K(Dde)','Reagent MW (g/mol)'])==pytest.approx(532.63)
    assert float(db.loc['K(ivDde)','Reagent MW (g/mol)'])==pytest.approx(574.71)
    assert calculate_mass_states('K(Dde)','2-CTC')['linear_protected_mw'] != calculate_mass_states('K(ivDde)','2-CTC')['linear_protected_mw']


def test_head_to_tail_side_chain_protected_keeps_side_groups_then_loses_h2o():
    m=calculate_mass_states('dS-dV-dS','2-CTC')
    assert m['head_to_tail_allowed'] is True
    assert m['linear_protected_mw']-m['head_to_tail_protected_mw']==pytest.approx(WATER_MW,abs=.002)
    assert m['linear_deprotected_mw']-m['head_to_tail_deprotected_mw']==pytest.approx(WATER_MW,abs=.002)
    assert m['protecting_group_delta']==pytest.approx(2*56.11,abs=.002)
    assert m['selective_cleavage_mw']==m['linear_protected_mw']


def test_head_to_tail_rejects_amide_or_capped_n_terminus():
    for sequence,resin in [('SG','Rink Amide AM'),('Ac-SG','2-CTC'),('SG-NH2','2-CTC')]:
        m=calculate_mass_states(sequence,resin)
        assert not m['head_to_tail_allowed']
        assert m['head_to_tail_protected_mw'] is None


def test_missing_modified_residue_does_not_report_fictional_mw():
    with pytest.raises(MassBalanceError):
        calculate_mass_states('S(UnknownProtection)-G','2-CTC')
    branch=calculate_mass_states('K(GGEP)','2-CTC')
    assert branch['topology']=='lysine_branch'
    assert branch['head_to_tail_allowed'] is False


def test_yield_scenario_requires_operator_factors():
    unknown=estimate_mass_yield(200.,.5,copies=2,coupling_steps=3)
    assert unknown['theoretical_g']==pytest.approx(.2)
    assert unknown['scenario_g'] is None
    assumed=estimate_mass_yield(200.,.5,copies=2,coupling_steps=3,
         per_step_conversion=.95, cyclization_recovery=.8,isolation_recovery=.7)
    assert assumed['scenario_g']==pytest.approx(.2*.95**3*.8*.7,abs=1e-6)
    assert assumed['status']=='OPERATOR_SCENARIO_NOT_VALIDATED'
    with pytest.raises(ValueError):
        estimate_mass_yield(200,.5,per_step_conversion=1.1,isolation_recovery=.8)


def test_catalog_v9_protected_rows_have_no_duplicate_tokens():
    issues=validate_compounds_dataframe(load_compounds())
    assert issues.empty,issues.to_string(index=False)
    names=load_compounds()['Token'].astype(str).tolist()
    for name in ('H-Ser(tBu)-OH','H-Arg(Pbf)-OH','H-Glu(OtBu)-OH','H-Cys(Trt)-OH','H-Lys(Boc)-OH'):
        assert name in names


def test_autoplan_draft_embeds_protected_stages_without_approval():
    from suite_gui.auto_plan_option_v9 import build_review_draft
    draft=build_review_draft('dS-dV-dS',.1,'2-CTC',.8,'DIC/HOBt',1,product_path='head_to_tail_protected')
    assert draft['format'].startswith('SPPS Planner V9.0.0')
    assert draft['status']=='DRAFT_NOT_APPROVED'
    assert draft['mass']['status']=='CALCULATED_THEORETICAL'
    assert draft['mass']['values']['head_to_tail_protected_mw'] is not None
    assert draft['yield']['status']=='NO_ESTIMATE_UNTIL_OPERATOR_FACTORS'


def test_v9_checklist_displays_mw_after_coupling_and_after_final_depro(monkeypatch):
    from types import SimpleNamespace
    from suite_gui.modules import plan_workflow
    import spps_planner.engine as engine
    class Tree:
        def __init__(self,rs):self.rows=rs
        def get_children(self):return list(range(len(self.rows)))
        def item(self,iid,field=None):
            if field=='values':return tuple(self.rows[iid].values())
            return {'values':tuple(self.rows[iid].values())}
        def __getitem__(self,key):
            if key=='columns':return list(self.rows[0]);raise KeyError(key)
    # _row_dict maps column order by the tree's "columns"; no GUI required.
    row={name:'' for name in plan_workflow.PLAN_COLUMNS}
    row.update({'No':'1','Unit name':'Fmoc-Gly-OH','Unit eq':'5','Unit mmol':'.5',
        'Reagent 1':'DIC','R1 mmol':'.5','Reagent 2 / catalyst':'HOBt','R2 mmol':'.5',
        'Coupling solvent':'DMF','Solvent mL':'10','Repeat':'1'})
    gui=SimpleNamespace(pm_selected_plan_tree=Tree([row]))
    inp=SimpleNamespace(sequence='G',resin='Rink Amide AM',scale_mmol=.1,
        resin_loading_mmol_g=.8,apply_resin_loading=False,deprotection_count=2,
        deprotection_ratio='20% in DMF',deprotection_base='Piperidine')
    _,checklist=plan_workflow._visible_protocol(gui,{},inp)
    coupling=next(x for x in checklist if 'Coupling' in x['operation'])
    terminal=[x for x in checklist if 'Last Fmoc deprotection' in x['operation']]
    assert float(coupling['peptide_mw'])==pytest.approx(74.08+222.24,abs=.02)
    assert len(terminal)==2
    assert float(terminal[-1]['peptide_mw'])==pytest.approx(74.08,abs=.02)


def test_three_letter_protected_names_and_free_alpha_aliases():
    assert parse_sequence('Ser(tBu)-Val').core_tokens == ['S','V']
    assert parse_sequence('H-S(tBu)-OH').core_tokens == ['H-Ser(tBu)-OH']
    assert parse_sequence('H-D-S(tBu)-OH').core_tokens == ['H-D-Ser(tBu)-OH']
    assert calculate_mass_states('Ser(Trt)-Val','2-CTC')['residues'][0]['protecting_group']=='Trt'
    assert parse_sequence('SER').core_tokens==['S','E','R']


def test_ac_protected_aa_no_double_count_cap_and_single_amino_acid_not_cyclic():
    a=calculate_mass_states('Ac-Ser(tBu)-OH-G','2-CTC')
    b=calculate_mass_states('Ac-S(tBu)-G','2-CTC')
    assert a['linear_protected_mw']==pytest.approx(b['linear_protected_mw'],abs=.02)
    assert a['head_to_tail_protected_mw'] is None
    one=calculate_mass_states('H-Ser(tBu)-OH','2-CTC')
    assert one['head_to_tail_protected_mw'] is None


def test_process_review_stage_respects_retained_groups_and_cyclization():
    from suite_gui.checklist_mass_v9 import add_process_stages
    mass=calculate_mass_states('dS-dV-dS','2-CTC')
    rows=[]
    add_process_stages(rows,mass,{'product_path':'head_to_tail_deprotected'})
    assert [r['operation'] for r in rows]==[
        'Selective cleavage — protected form',
        'Head-to-tail cyclization — review',
        'Global side-chain deprotection — review',
    ]
    assert [float(r['peptide_mw']) for r in rows]==pytest.approx(
        [mass['linear_protected_mw'],mass['head_to_tail_protected_mw'],mass['head_to_tail_deprotected_mw']])
