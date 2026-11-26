"""Explicit unapproved stages for Auto Plan V9; no inferred reagent recipes."""
from __future__ import annotations
from typing import Any


def build_process_review(product_path: str, mass_status: dict[str,Any], reaction_review=None) -> dict[str,Any]:
    stages=[]
    blockers=[]
    values=mass_status.get('values',{}) if mass_status.get('status')=='CALCULATED_THEORETICAL' else {}
    def add(ident,label,key=None,note='', *, manual=False):
        stages.append({'id':ident,'label':label,'theoretical_mw_g_mol':values.get(key) if key else None,
                       'requires_operator_review':True,'manual_conditions_required':manual,'note':note})
    if not values:
        blockers.append('Molecular mass unresolved; stage MW withheld until chemical annotation validated.')
    if values.get('topology')=='lysine_branch':
        add('branch_handle','Orthogonal Lys branch deprotection',note='Reagent/time require operator-approved orthogonal protection method.',manual=True)
        add('branch_elongation','Branch synthesis',note='Branch order and intermediate MW withheld without explicit process order.',manual=True)
    add('assembly','SPPS chain assembly',note='Resin-bound peptide equivalent; not isolated molecular weight.')
    if product_path in ('linear_protected','head_to_tail_protected','head_to_tail_deprotected'):
        add('selective_cleavage','Selective cleavage / protected linear precursor','selective_cleavage_mw',
            'Conditional side-chain protection retention; confirm actual termini and protective groups.',manual=True)
    if product_path.startswith('head_to_tail'):
        if not values.get('head_to_tail_allowed'):
            blockers.append('Head-to-tail requires free alpha amine and C-terminal COOH; topology/termini check failed.')
        if not reaction_review or reaction_review.get('method_status')!='OPERATOR_SUPPLIED_REVIEW_REQUIRED':
            blockers.append('Cyclization method needs reagent eq, solvent, time, concentration and operator review.')
        add('cyclization','Head-to-tail macrocyclization','head_to_tail_protected_mw',
            'Amide closure removes one H2O from protected linear monomer. Do not treat as proof of cyclization.',manual=True)
        if product_path=='head_to_tail_deprotected':
            add('deprotection','Final side-chain deprotection','head_to_tail_deprotected_mw',
                'Actual protecting-group retention/removal requires analytical confirmation.',manual=True)
    elif product_path=='linear_deprotected':
        add('full_cleavage','Full cleavage / unprotected linear product','linear_deprotected_mw',manual=True)
    elif product_path=='linear_protected':
        add('isolated_protected','Protected linear product','linear_protected_mw',manual=True)
    else:
        blockers.append('Unrecognized/unsupported topology for automated process review.')
    add('analytics','HPLC / MS analytical confirmation',note='User must record observed identity, purity and recovery; no validation inferred.')
    return {'status':'BLOCKED_REQUIRES_REVIEW' if blockers else 'UNAPPROVED_DRAFT',
            'stages':stages,'blockers':blockers,'note':'Review-only, not a lab SOP; existing Generate remains authoritative.'}


def review_disulfide_product(sequence, resin, options):
    """Exact Cys-Cys molecular review; no inferred laboratory conditions."""
    from spps_planner.extended_structure_v9 import graph_crosscheck
    positions = options.get('disulfide_sites') if isinstance(options, dict) else None
    if not isinstance(positions, (list, tuple)) or len(positions) != 2:
        return {'status': 'WITHHELD_INVALID_SITES', 'reason': 'Select two distinct Cys positions (1-based).'}
    try:
        a, b = (int(v) for v in positions)
        if a == b or a < 1 or b < 1:
            raise ValueError('Select two distinct positive Cys positions.')
    except (ValueError, TypeError):
        return {'status': 'WITHHELD_INVALID_SITES', 'reason': 'Cys positions must be distinct positive integers.'}
    result = graph_crosscheck(sequence, resin, topology='disulfide',
                              side_chain_mode='explicit', sites=(a, b))
    # Graph decides whether the specified Cys are actually unprotected and representable.
    return dict(result, disulfide_sites=[a,b],
                reaction_review_status='NOT APPROVED',
                process_stages=['Chain assembly / cleavage: operator review',
                                'Cys thiol availability and oxidation: operator review',
                                'HPLC/MS confirmation: operator review'])
