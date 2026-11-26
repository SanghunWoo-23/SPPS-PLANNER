"""V9.0.0 review-only reaction method editor for *head-to-tail* cyclization.

No default reagent equivalents, solvent recipes or empirical success claims.
Other topology/reactions deliberately fail closed until supported by an atom graph.
All mass results are sourced from mass_balance_v9, never recalculated here.
"""
from __future__ import annotations
import math
from typing import Any

from .mass_balance_v9 import MassBalanceError, calculate_mass_states, checked_integer
from .reaction_evidence_v9 import review_reaction_evidence

class ReactionPlanError(ValueError):
    """Unsupported chemistry, invalid input, or an unsafe inference."""

# Co-reagents are categorized by actual chemical function, not mislabeled as catalysts.
# Numeric reagent quantities require operator-supplied equivalents.
REACTION_METHODS = {
    'HBTU_NMM': {
        'label': 'HBTU / NMM',
        'reagents': [('HBTU', 'coupling_reagent'), ('NMM', 'base')],
    },
    'HBTU_DIEA': {
        'label': 'HBTU / DIEA',
        'reagents': [('HBTU', 'coupling_reagent'), ('DIEA', 'base')],
    },
    'DIC_HOBT': {
        'label': 'DIC / HOBt',
        'reagents': [('DIC', 'coupling_reagent'), ('HOBt', 'additive')],
    },
    'EDC_HOBT': {
        'label': 'EDC·HCl / HOBt',
        'reagents': [('EDC·HCl', 'coupling_reagent'), ('HOBt', 'additive')],
    },
    'EDC_NHS': {
        'label': 'EDC·HCl / NHS',
        'reagents': [('EDC·HCl', 'coupling_reagent'), ('NHS', 'additive')],
    },
    'HATU_DIEA': {
        'label': 'HATU / DIEA',
        'reagents': [('HATU', 'coupling_reagent'), ('DIEA', 'base')],
    },
    'PYBOP_NMM': {
        'label': 'PyBOP / NMM',
        'reagents': [('PyBOP', 'coupling_reagent'), ('NMM', 'base')],
    },
    'DIC_OXYMA': {
        'label': 'DIC / Oxyma Pure',
        'reagents': [('DIC', 'coupling_reagent'), ('Oxyma Pure', 'additive')],
    },
}

# Selective acidolysis choices are *unapproved formulation descriptions*, not
# validated cleavage protocols. Times, compatibility, and scale-dependent volumes
# are deliberately never assumed.
SELECTIVE_CLEAVAGE_SYSTEMS = {
    'TFA_DCM_1_5': {'label':'1.5% TFA / DCM', 'tfa_percent':1.5, 'solvent':'DCM'},
    'TFA_DCM_1': {'label':'1% TFA / DCM', 'tfa_percent':1.0, 'solvent':'DCM'},
    'TFA_DCM_2': {'label':'2% TFA / DCM', 'tfa_percent':2.0, 'solvent':'DCM'},
    'HFIP_DCM': {'label':'HFIP / DCM (operator-defined)', 'tfa_percent':None, 'solvent':'DCM'},
    'CUSTOM': {'label':'Custom / operator-defined', 'tfa_percent':None, 'solvent':''},
}


def prepare_selective_cleavage_review(method_id='TFA_DCM_1_5', *,
                                      resin='', contact_time_min=None, total_volume_ml=None, notes=''):
    if method_id not in SELECTIVE_CLEAVAGE_SYSTEMS:
        raise ReactionPlanError('Choose a registered selective cleavage method.')
    if len(str(notes)) > 1000:
        raise ReactionPlanError('Selective cleavage notes are too long.')
    contact_time = _positive_number(contact_time_min, 'Selective cleavage time (min)', required=False)
    volume = _positive_number(total_volume_ml, 'Selective cleavage solution volume (mL)', required=False)
    method = SELECTIVE_CLEAVAGE_SYSTEMS[method_id]
    # These are candidates for resin cleavage with retained protecting groups;
    # CTC compatibility depends on product and resin chemistry. Do not infer a
    # protected free acid from a Rink Amide linker.
    resin_name = str(resin or '').lower()
    compatible_resin = 'ctc' in resin_name or 'chlorotrityl' in resin_name
    return {
        'schema':'V9.0.0-selective-cleavage-review-1',
        'system_id':method_id, 'system_label':method['label'],
        'tfa_percent_v_v':method['tfa_percent'], 'diluent':method['solvent'],
        'contact_time_min':contact_time, 'total_volume_ml':volume,
        'tfa_volume_ml':round(volume*method['tfa_percent']/100,6) if volume is not None and method['tfa_percent'] is not None else None,
        'dcm_volume_ml':round(volume*(100-method['tfa_percent'])/100,6) if volume is not None and method['tfa_percent'] is not None else None,
        'notes':str(notes),
        'status':'DRAFT_NOT_APPROVED' if compatible_resin else 'RESIN_COMPATIBILITY_REVIEW_REQUIRED',
        'warning':'Confirm resin/linker acid-lability, side-chain protection retention and experimental workup; no volumes or reaction completion inferred.',
    }



# Global deprotection/cleavage is a different operation from mild cleavage of
# a protected head-to-tail precursor. All quantities are operator-controlled.
# Literature: Front Chem 2020, 8:447 (doi:10.3389/fchem.2020.00447),
# Merck Fmoc Cys protocols (Trt/Acm have different deprotection behavior).
GLOBAL_CLEAVAGE_SYSTEMS = {
    'TFA_TIS_WATER_95': {'label': '95% TFA / 2.5% TIS / 2.5% H2O',
                         'fractions': (0.95, 0.025, 0.025)},
}


def prepare_global_cleavage_review(*, method_id='TFA_TIS_WATER_95',
                                   total_volume_ml='', tfa_equivalents='',
                                   scale_mmol=None):
    if method_id not in GLOBAL_CLEAVAGE_SYSTEMS:
        raise ReactionPlanError('Unknown global cleavage cocktail.')
    volume = _positive_number(total_volume_ml, 'Global cleavage volume (mL)', required=False)
    equivalents = _positive_number(tfa_equivalents, 'Global TFA equivalents', required=False)
    if equivalents is not None and (scale_mmol is None or _positive_number(scale_mmol, 'Scale (mmol)') <= 0):
        raise ReactionPlanError('Global TFA equivalents require a positive peptide scale.')
    tfa_fraction, tis_fraction, water_fraction = GLOBAL_CLEAVAGE_SYSTEMS[method_id]['fractions']
    # TFA MW 114.02 g/mol, density 1.49 g/mL; only use this conversion when
    # the operator explicitly supplied equivalents and the actual peptide scale.
    if volume is None and equivalents is not None:
        tfa_ml = (float(scale_mmol) * equivalents * 114.02 / 1000.0) / 1.49
        volume = tfa_ml / tfa_fraction
    if volume is not None and equivalents is not None:
        required_tfa_ml = (float(scale_mmol) * equivalents * 114.02 / 1000.0) / 1.49
        if abs(volume * tfa_fraction - required_tfa_ml) > max(0.02, required_tfa_ml * 0.02):
            raise ReactionPlanError('Global cleavage volume and TFA equivalents disagree (>2%).')
    return {
        'schema':'V9-global-cleavage-review-1', 'system_id':method_id,
        'system_label':GLOBAL_CLEAVAGE_SYSTEMS[method_id]['label'],
        'total_volume_ml':volume, 'tfa_equivalents':equivalents,
        'tfa_volume_ml':round(volume*tfa_fraction,6) if volume is not None else None,
        'tis_volume_ml':round(volume*tis_fraction,6) if volume is not None else None,
        'water_volume_ml':round(volume*water_fraction,6) if volume is not None else None,
        'status':'DRAFT_NOT_APPROVED',
        'warning':'Composition and amounts are operator drafts, not a verified cleavage SOP. Check resin and thiol protecting-group compatibility.'
    }


def prepare_branch_boc_review(*, boc2o_equivalents='3', diea_equivalents='3'):
    return {
        'schema':'V9-branch-nterm-boc-review-1', 'system_label':'N-terminal Boc2O / DIEA',
        'reagents':[
            {'name':'Boc2O', 'role':'N-terminal protection',
             'equivalents':_positive_number(boc2o_equivalents,'Boc2O equivalents')},
            {'name':'DIEA', 'role':'base',
             'equivalents':_positive_number(diea_equivalents,'DIEA equivalents')},
        ], 'status':'DRAFT_NOT_APPROVED',
        'warning':'Block the main-chain N-terminus before orthogonal Lys side-chain deprotection and branch coupling; confirm reaction completion.'
    }

# Bottle labels may use the typographic middle dot or a hyphen. Keep one
# chemistry identity in review records while preserving existing projects.
_REAGENT_ALIASES = {'EDC-HCl': 'EDC·HCl', 'EDC HCl': 'EDC·HCl',
                    'EDC.HCl': 'EDC·HCl', 'EDC hydrochloride': 'EDC·HCl'}

def _canonical_equivalents(equivalents):
    if equivalents is None:
        return {}
    if not isinstance(equivalents, dict):
        raise ReactionPlanError('Equivalents must be a mapping keyed by reagent name.')
    normalized = {}
    for name, amount in equivalents.items():
        if not isinstance(name, str):
            raise ReactionPlanError('Reagent identities must be text.')
        canonical = _REAGENT_ALIASES.get(name.strip(), name.strip())
        if canonical in normalized:
            raise ReactionPlanError('Duplicate reagent aliases; enter only one value per reagent.')
        normalized[canonical] = amount
    return normalized


def prepare_branch_coupling_review(method_id='HBTU_NMM', *, equivalents=None, solvent=''):
    if method_id not in REACTION_METHODS:
        raise ReactionPlanError('Unknown branch coupling system.')
    spec=REACTION_METHODS[method_id]
    if not isinstance(solvent,str) or len(solvent)>200:
        raise ReactionPlanError('Branch solvent must be text no longer than 200 characters.')
    supplied=_canonical_equivalents(equivalents)
    expected={name for name,_ in spec['reagents']}
    if set(supplied)-expected:
        raise ReactionPlanError('Branch reagent equivalents do not match the selected system.')
    reagents=[{'name':name,'role':role,
              'equivalents':_positive_number(supplied.get(name),name+' equivalents',required=False)}
              for name,role in spec['reagents']]
    return {'schema':'V9.0.0-branch-coupling-review-1', 'system_id':method_id,
            'system_label':spec['label'],
            'reagents':reagents,'solvent':solvent.strip(),
            'status':'DRAFT_NOT_APPROVED',
            'warning':'Choose conditions and confirm side-chain deprotection/chemoselectivity before experimental use; no equivalents or durations inferred.'}


SUPPORTED_REACTIONS = {'head_to_tail'}
REVIEW_ONLY_REACTIONS = {
    'side_chain_lactam', 'disulfide', 'thioether', 'cuaac', 'spaac', 'rcm',
}


def _positive_number(value: Any, name: str, *, required: bool = True):
    if value is None or str(value).strip() == '':
        if required:
            raise ReactionPlanError(f'{name} must be supplied by the operator; no automatic value is assumed.')
        return None
    if isinstance(value,bool):
        raise ReactionPlanError(f'{name} must be numeric, not boolean.')
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise ReactionPlanError(f'{name} must be numeric.') from exc
    if not math.isfinite(number) or number <= 0:
        raise ReactionPlanError(f'{name} must be a positive finite number.')
    return number


def method_choices():
    return [(key, spec['label']) for key, spec in REACTION_METHODS.items()]


def _finite_quantity(number: float, label: str) -> float:
    """Keep small positive mmol values and reject overflow instead of emitting JSON Infinity."""
    if not math.isfinite(number) or number <= 0:
        raise ReactionPlanError(f'Calculated {label} is not a finite positive value; verify scale, concentration and equivalents.')
    return float(f'{number:.12g}')


def prepare_reaction_review(sequence: str, resin: str, *, reaction_type='head_to_tail',
                            method_id='DIC_HOBT', phase='solution',
                            scale_mmol=None, copies=1, concentration_mm=None,
                            equivalents=None, solvent='', reaction_time_h=None,
                            temperature_c=None, side_chain_mode='catalog') -> dict:
    """Validate an operator-specified reaction and compute *review* quantities.

    This never produces an approved synthesis method, experimental yield, or
    safety claim. Unsupported topology/bond chemistry refuses to provide MW.
    Reagent mass/volume is deliberately NOT inferred without exact bottle MW.
    """
    if not isinstance(reaction_type,str):
        raise ReactionPlanError('Reaction type must be a recognized string.')
    if reaction_type not in SUPPORTED_REACTIONS:
        if reaction_type in REVIEW_ONLY_REACTIONS:
            raise ReactionPlanError(f'{reaction_type}: atom-specific bond sites and chemistry are not yet implemented. No automatic plan or MW is allowed.')
        raise ReactionPlanError(f'Unknown reaction type: {reaction_type!r}')
    if phase not in ('solution', 'on_resin'):
        raise ReactionPlanError('Phase must be solution or on_resin.')
    if phase == 'on_resin':
        raise ReactionPlanError('Head-to-tail on-resin ring closure requires an explicitly validated free-acid/linker strategy. This build only supports solution review after selective cleavage.')
    if not isinstance(method_id,str) or method_id not in REACTION_METHODS:
        raise ReactionPlanError('Choose a registered reaction system; unsupported chemistry must not be guessed.')
    if not isinstance(solvent,str) or len(solvent)>200:
        raise ReactionPlanError('Solvent must be text no longer than 200 characters.')
    if isinstance(scale_mmol, bool):
        raise ReactionPlanError('Scale (mmol) must be a positive numeric value.')
    scale = _positive_number(scale_mmol,'Scale (mmol)')
    try:
        count = checked_integer(copies, 'copies')
    except ValueError as exc:
        raise ReactionPlanError(str(exc)) from exc
    mass = calculate_mass_states(sequence, resin, side_chain_mode=side_chain_mode)
    if not mass['head_to_tail_allowed'] or mass['head_to_tail_protected_mw'] is None:
        raise ReactionPlanError('Head-to-tail blocked: free α-amine and C-terminal COOH are required; verify sequence, resin, and terminal groups.')
    if mass.get('nterm','H') != 'H':
        raise ReactionPlanError('N-terminal end cap blocks head-to-tail chemistry.')
    if mass.get('cterm') != 'OH':
        raise ReactionPlanError('C-terminal amide cannot close to a head-to-tail amide bond.')
    concentration = _positive_number(concentration_mm,'Reaction concentration (mM)',required=False)
    if concentration is None:
        volume_per_copy_ml = None
    else:
        volume_per_copy_ml = _finite_quantity(scale * 1000.0 / concentration,
                                              'solution volume per copy')
    time = _positive_number(reaction_time_h, 'Reaction time (h)', required=False)
    temp = None
    if temperature_c is not None and str(temperature_c).strip()!='':
        if isinstance(temperature_c,bool):
            raise ReactionPlanError('Temperature must be numeric, not boolean.')
        try:
            temp = float(temperature_c)
        except (ValueError,TypeError) as exc:
            raise ReactionPlanError('Temperature must be numeric in Celsius.') from exc
        if not math.isfinite(temp) or not -100. <= temp <= 300.:
            raise ReactionPlanError('Temperature outside supported input bounds (-100 to 300 °C).')
    spec = REACTION_METHODS[method_id]
    supplied = _canonical_equivalents(equivalents)
    expected={name for name,role in spec['reagents']}
    if set(supplied)-expected:
        raise ReactionPlanError('Unexpected reagents for the selected system; select an appropriate method instead.')
    reagents=[]
    for name,role in spec['reagents']:
        eq=_positive_number(supplied.get(name),f'{name} equivalents',required=False)
        reagents.append({'name':name,'role':role,'equivalents':eq,
                         'mmol_per_copy':_finite_quantity(eq*scale, f'{name} mmol per copy') if eq is not None else None,
                         'mmol_total':_finite_quantity(eq*scale*count, f'{name} total mmol') if eq is not None else None})
    conditions_ready = bool(concentration and str(solvent).strip() and time and all(r['equivalents'] is not None for r in reagents))
    warnings=[
        'UNAPPROVED DRAFT: no reagent or cleavage conditions are automatically optimized.',
        'Selective cleavage must generate a protected linear peptide with free N-terminus and free C-terminal COOH.',
        'Retained side-chain protecting groups are theoretical; verify by analysis, especially acid-sensitive protections.',
        'Reagent amounts are in mmol only; masses and volumes require verified bottle composition, purity and density.',
        'Dilution, solubility and intramolecular vs intermolecular reactions require laboratory review.',
    ]
    if method_id == 'EDC_NHS':
        warnings.append('EDC/NHS activates a carboxyl group through NHS ester chemistry; hydrolysis, N-acylurea byproducts and oligomerization require independent review. No head-to-tail cyclization efficiency is inferred.')
    warnings.extend(mass['warnings'])
    # Literature is attached as contextual provenance and warnings only.
    # This never supplies reaction conditions or upgrades a draft to an SOP.
    evidence=review_reaction_evidence(method_id=method_id, solvent=solvent,
                                      resin=resin, mass_states=mass)
    # Stoichiometric analytical *candidates*, not predictions of formed species.
    # These are average neutral molecule MW, not LC-MS m/z values or yields.
    # A linear dimer has one interchain amide closure; a cyclic dimer has
    # two. They must not be confused with a cyclized monomer in MS review.
    linear=mass['selective_cleavage_mw']
    water=mass['water_loss_mw']
    possible_oligomers=[
        {'species':'linear_dimer_one_link','molecule_count':2,'amide_bonds_formed':1,
         'average_neutral_mw_g_mol':round(2*linear-water,3)},
        {'species':'cyclic_dimer_two_links','molecule_count':2,'amide_bonds_formed':2,
         'average_neutral_mw_g_mol':round(2*linear-2*water,3)},
    ]
    warnings.extend(flag['message'] for flag in evidence['risk_flags'])
    if not conditions_ready:
        warnings.append('INCOMPLETE METHOD: missing eq, concentration, solvent or time. Do not treat as executable protocol.')
    # No off-path source mutation; JSON-safe primitives only.
    return {
        'schema':'V9.0.0-reaction-review-1', 'approval':'DRAFT_NOT_APPROVED',
        'method_status':'OPERATOR_SUPPLIED_REVIEW_REQUIRED' if conditions_ready else 'INCOMPLETE_REVIEW_ONLY',
        'reaction_type':reaction_type, 'phase':phase, 'system_id':method_id,
        'sequence':str(sequence).strip(), 'resin':str(resin).strip(),
        'side_chain_mode':side_chain_mode,
        'system_label':spec['label'], 'scale_mmol_per_copy':scale,'copies':count,
        'reactive_sites': ['N-terminal α-amine','C-terminal carboxylic acid'],
        'bond':'head_to_tail_amide', 'mass_type':mass['mass_type'],
        'protected_linear_mw':mass['selective_cleavage_mw'],
        'protected_cyclic_mw':mass['head_to_tail_protected_mw'],
        'loss_mw':mass['water_loss_mw'],
        'reagents':reagents, 'solvent':str(solvent).strip(),
        'reaction_time_h':time,'temperature_c':temp,
        'concentration_mm':concentration,
        'volume_per_copy_ml':volume_per_copy_ml,
        'volume_total_ml':_finite_quantity(volume_per_copy_ml*count, 'total solution volume') if volume_per_copy_ml is not None else None,
        'warnings':warnings, 'literature_evidence':evidence,
        'possible_oligomers':possible_oligomers,
        'basis':'Operator-specified reaction setup; molecule MW from mass_balance_v9. Not a validated SOP.',
    }


def validate_stored_reaction_review(review, *, sequence, resin, scale_mmol,
                                    copies, side_chain_mode='catalog') -> dict:
    """Recompute all derived fields instead of trusting project/imported JSON.

    Old, incomplete or edited review records fail closed and require new operator
    review. This deliberately does not grant any experimental approval.
    """
    if not isinstance(review, dict):
        raise ReactionPlanError('Stored reaction review must be an object.')
    if review.get('schema') != 'V9.0.0-reaction-review-1' or review.get('approval') != 'DRAFT_NOT_APPROVED':
        raise ReactionPlanError('Unknown or approved review schema; reopen method editor.')
    if (review.get('sequence') != str(sequence).strip()
            or review.get('resin') != str(resin).strip()
            or review.get('side_chain_mode') != side_chain_mode):
        raise ReactionPlanError('Reaction review no longer matches the selected sequence, resin or protection policy.')
    try:
        expected_count = checked_integer(copies, 'copies')
        stored_count = checked_integer(review.get('copies'), 'copies')
        expected_scale = _positive_number(scale_mmol, 'Scale (mmol)')
        stored_scale = _positive_number(review.get('scale_mmol_per_copy'), 'Stored scale (mmol)')
    except (ValueError, TypeError) as exc:
        raise ReactionPlanError(str(exc)) from exc
    if expected_count != stored_count or expected_scale != stored_scale:
        raise ReactionPlanError('Reaction review scale or copies changed; re-review required.')
    reagents = review.get('reagents')
    if not isinstance(reagents, list) or not all(isinstance(r, dict) for r in reagents):
        raise ReactionPlanError('Reaction reagent records are invalid.')
    if len(reagents) > 16:
        raise ReactionPlanError('Unreasonable number of reaction reagent records.')
    if any(not isinstance(r.get('name'),str) for r in reagents):
        raise ReactionPlanError('Stored reagent name must be text.')
    if len({r['name'] for r in reagents}) != len(reagents):
        raise ReactionPlanError('Stored reagent names must not repeat.')
    eqs = {r['name']:r.get('equivalents') for r in reagents}
    try:
        canonical = prepare_reaction_review(
            sequence, resin, reaction_type=review.get('reaction_type'),
            method_id=review.get('system_id'), phase=review.get('phase'),
            scale_mmol=expected_scale, copies=expected_count,
            concentration_mm=review.get('concentration_mm'), equivalents=eqs,
            solvent=review.get('solvent'), reaction_time_h=review.get('reaction_time_h'),
            temperature_c=review.get('temperature_c'), side_chain_mode=side_chain_mode,
        )
    except (ValueError, TypeError, KeyError) as exc:
        raise ReactionPlanError(f'Cannot validate reaction review: {exc}') from exc
    # Strict comparison intentionally invalidates a draft if scientific mass
    # rules or stored calculated quantities have changed since it was created.
    if review != canonical:
        raise ReactionPlanError('Saved reaction review differs from freshly calculated chemistry; re-review required.')
    return canonical
