"""V9 conservative single-Lys ε-amide branch total-mass QA."""
import pytest
from spps_planner.mass_balance_v9 import calculate_mass_states, MassBalanceError, WATER_MW
from spps_planner.database import load_compounds
from suite_gui.checklist_mass_v9 import make_mass_tracker
from suite_gui.auto_plan_option_v9 import preview_inputs


def test_lysine_simple_arm_has_condensation_molecule_balance():
    m=calculate_mass_states('K(GGEP)','2-CTC',side_chain_mode='none')
    base=calculate_mass_states('K','2-CTC',side_chain_mode='none')
    arm=calculate_mass_states('GGEP','2-CTC',side_chain_mode='none')
    assert m['topology']=='lysine_branch'
    assert m['linear_deprotected_mw']==pytest.approx(
        base['linear_deprotected_mw']+arm['linear_deprotected_mw']-WATER_MW,abs=.003)
    assert m['branch_anchor_position']==1
    assert [r['residue'] for r in m['branch_arm_residues']]==list('GGEP')
    assert m['head_to_tail_allowed'] is False
    assert m['head_to_tail_protected_mw'] is None


def test_lysine_anchor_protection_removed_before_branch_and_arm_protected():
    unprotected=calculate_mass_states('K(GGEP)','2-CTC',side_chain_mode='none')
    protected=calculate_mass_states('K(GGEP)','2-CTC',side_chain_mode='catalog')
    prepared=calculate_mass_states('K(Dde)(GGEP)','2-CTC',side_chain_mode='catalog')
    assert protected['linear_protected_mw']-unprotected['linear_deprotected_mw']==pytest.approx(56.11,abs=.003)
    assert prepared['linear_protected_mw']==protected['linear_protected_mw']
    assert prepared['protecting_group_delta']==pytest.approx(56.11)


def test_branch_per_step_mass_and_unsupported_arm_fail_closed():
    for seq in ['K(G-E(OtBu)-G)','K(dS-dV-dS)','K(GGEP)K(GG)','S(GGEP)']:
        with pytest.raises(MassBalanceError):
            calculate_mass_states(seq,'2-CTC')
    with pytest.raises(MassBalanceError, match='stepwise Checklist MW'):
        make_mass_tracker('K(GGEP)','2-CTC')


def test_branch_cys_count_includes_arm():
    plan=preview_inputs('K(CCG)',.1,'2-CTC',.8,'DIC/HOBt',1)
    assert plan['residues']==4
    assert plan['cys_count']==2
    assert plan['tfa_eq']==200
