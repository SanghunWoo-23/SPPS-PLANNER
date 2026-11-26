"""V9.0.0 protected-peptide mass accounting and non-empirical yield scenarios.

Molecular weights are average neutral masses in g/mol (not monoisotopic MS m/z).
Assumptions are explicit and unsupported chemistry fails closed. Does not change
legacy engine.py mass contribution conventions or experimental SOPs.
"""
from __future__ import annotations
import math
import re
from decimal import Decimal, InvalidOperation

from .database import load_compounds, compound_lookup
from .parser import parse_sequence

WATER_MW = 18.01528
FMOC_MASS_ADD = 222.24
# Average MASS ADDED by protective substitution on a residue (not whole reagent).
# Values rounded to laboratory g/mol precision; catalog precursor MW takes
# precedence for protected amino acid entries. Do not assume Dde == ivDde.
# Cys(StBu) is a DISULFIDE S-S-tBu: sidechain mass increment C4H8S
# ≈ 88.17 g/mol, NOT 90.16 (verified against Fmoc-Cys(StBu)-OH formula).
PROTECTING_DELTA = {
    'tBu': 56.11, 'OtBu': 56.11, 'Boc': 100.12, 'Trt': 242.32,
    'Pbf': 252.33, 'Acm': 71.08, 'StBu': 88.17,
    'Dde': 164.20, 'ivDde': 206.28, 'Mtt': 256.34,
    'Fmoc': 222.24, 'Alloc': 84.07,
}
GROUP_CANON = {re.sub('[^A-Za-z0-9]','',k).upper(): k for k in PROTECTING_DELTA}
AA3 = { 'A':'Ala', 'R':'Arg','N':'Asn','D':'Asp','C':'Cys','Q':'Gln','E':'Glu','G':'Gly','H':'His','I':'Ile','L':'Leu','K':'Lys','M':'Met','F':'Phe','P':'Pro','S':'Ser','T':'Thr','W':'Trp','Y':'Tyr','V':'Val'}
AA1 = {v.upper():k for k,v in AA3.items()}
PROTECTED_EXPLICIT = re.compile(r'(?P<aa>d?[ARNDCQEGHILKMFPSTWYV]|(?:D-)?(?:' + '|'.join(AA3.values()) + r'))\((?P<group>[^)]+)\)',re.I)
FULL_H = re.compile(r'^H-(?P<res>(?:D-)?[A-Za-z]{3}|d?[A-Z])(?:\((?P<pg>[^()]+)\))?-OH$',re.I)

class MassBalanceError(ValueError):
    pass


def checked_integer(value, name: str, *, minimum: int = 1, maximum: int = 1_000_000) -> int:
    """Reject silent truncation, NaN, booleans and non-integral counts.

    1, 1.0 and "1" all denote one unit. "1.5", infinity and booleans do not.
    Not an arbitrary hard cap on legitimate large batch sizes.
    """
    if isinstance(value, bool) or value is None:
        raise ValueError(f'{name} must be an integer >= {minimum}.')
    try:
        numeric = Decimal(str(value).strip())
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f'{name} must be an integer >= {minimum}.') from exc
    if (not numeric.is_finite() or numeric != numeric.to_integral_value()
            or numeric < minimum or numeric > maximum):
        raise ValueError(f'{name} must be an integer from {minimum} to {maximum}.')
    return int(numeric)

def _canon_pg(pg):
    return GROUP_CANON.get(re.sub('[^A-Za-z0-9]','',str(pg)).upper())

def _as_aa(token):
    t = str(token).strip()
    if t.startswith('d') and len(t)==2 and t[1].upper() in AA3:
        return t[1].upper()
    if t.upper().startswith('D-'):
        t=t[2:]
    if len(t)==1 and t.upper() in AA3:
        return t.upper()
    return AA1.get(t.upper())

def _catalog(compounds=None):
    rows = (load_compounds() if compounds is None else compounds).to_dict('records')
    return {str(r.get('Token','')).strip():r for r in rows if str(r.get('Token','')).strip() not in ('','nan','NaN')}

def _float_mw(row, key):
    try:
        v=float(row.get(key,0))
        return v if math.isfinite(v) and v>0 else None
    except (ValueError, TypeError):
        return None

def _sequence_and_annotations(sequence):
    parsed = parse_sequence(sequence)
    tokens=list(parsed.core_tokens)
    # Exact free-alpha-amine building block: "H-Ser(tBu)-OH" is a SINGLE
    # reagent, not the peptide H + Ser + OH. The parser also supports the
    # bracketed equivalent within peptide sequences.
    from .parser import _canonical_free_alpha_protected_v9
    match=FULL_H.fullmatch(_canonical_free_alpha_protected_v9(str(sequence).strip()))
    if match:
        aa=_as_aa(match.group('res'))
        if not aa:
            raise MassBalanceError('Unrecognized amino-acid name')
        return [aa], {0: _canon_pg(match.group('pg'))} if match.group('pg') else {}, '', 'OH', [], []
    annotations={}
    for i,token in enumerate(tokens):
        m=FULL_H.fullmatch(token)
        if m:
            aa=_as_aa(m.group('res'))
            if not aa:
                raise MassBalanceError(f'Unknown building block {token}')
            tokens[i]=aa
            if m.group('pg'):
                annotations[i]=_canon_pg(m.group('pg')) or 'UNKNOWN:'+m.group('pg')
    # Explicit X(Group) annotations; positional index from prefix is robust
    # for ordinary one-letter and explicitly dashed D-residue sequences.
    from .parser import _normalize_three_letter_protected_aa_v9
    original=_normalize_three_letter_protected_aa_v9(str(sequence).strip())
    for m in PROTECTED_EXPLICIT.finditer(original):
        aa=_as_aa(m.group('aa'))
        if aa is None:
            continue
        group=_canon_pg(m.group('group')) or 'UNKNOWN:'+m.group('group')
        preceding=original[:m.start()]
        # Map the matched residue to a raw one-letter core position in a
        # compact sequence. For complex branch/multi-token cases do not guess.
        if len(m.group('aa'))==1 and all(len(str(t)) in (1,2) for t in tokens):
            chars=re.sub(r'\([^)]*\)','',preceding)
            chars=re.sub(r'\[[^]]*\]','',chars)
            # discard known N-terminal markers
            chars=re.sub(r'^(?:Ac|Fmoc|Boc|H)-','',chars,flags=re.I)
            chars=re.sub(r'[^ARNDCQEGHILKMFPSTWYV]','',chars,flags=re.I)
            pos=len(chars)
            if pos<len(tokens) and _as_aa(tokens[pos])==aa:
                annotations[pos]=group
    return tokens,annotations,parsed.nterm,parsed.cterm_text,list(parsed.branch_tokens),list(parsed.warnings)

def _default_protection(token, catalog):
    row=catalog.get(str(token))
    if row is None:
        row=catalog.get(_as_aa(token) or '')
    form=str(row.get('Reagent/protected form','')) if row else ''
    m=re.search(r'Fmoc-(?:D-)?[A-Za-z]+\(([^()]+)\)-OH',form,re.I)
    if m:
        return _canon_pg(m.group(1))
    return None

def calculate_mass_states(sequence, resin='2-CTC', *, compounds=None,
                          side_chain_mode='catalog', cterm_override=None):
    """Return mass stages for ONE molecule; no yield estimate included.

    side_chain_mode: catalog (retained groups from specified Fmoc precursors),
                     explicit (only groups written in user sequence), or none.
    Group loss during mild cleavage is not automatically assumed complete.
    """
    if side_chain_mode not in ('catalog','explicit','none'):
        raise MassBalanceError('Unknown protecting-group policy')
    catalog=_catalog(compounds)
    tokens,explicit,nterm,cterm,branches,warnings=_sequence_and_annotations(sequence)
    # Ac-X(PG)-OH preceding a peptide is a terminal amino-acid building block
    # carrying its OWN N-acetyl group. Its catalog residue contribution already
    # contains the Ac cap, so it must never be added a second time.
    ac_aa_in_catalog = bool(str(nterm).startswith('Ac-') and str(nterm).endswith('-OH'))
    if ac_aa_in_catalog:
        tokens=[nterm]+tokens
        explicit={int(i)+1:g for i,g in explicit.items()}
        match_pg=re.search(r'\(([^()]+)\)',nterm)
        if match_pg:
            explicit[0]=_canon_pg(match_pg.group(1)) or 'UNKNOWN:'+match_pg.group(1)
    if not tokens:
        raise MassBalanceError('Sequence is empty')
    parsed_branches=list(parse_sequence(sequence).branch_sites)
    if branches and not parsed_branches:
        raise MassBalanceError('Ambiguous branch topology. Exact molecular MW cannot be computed.')
    # V9 limited structural mass support: natural L-amino-acid arms bonded
    # through a free Lys ε-amine. All other branch topologies fail closed.
    if len(parsed_branches)>1:
        raise MassBalanceError('Multiple branch arms need explicit atomic graph; MW not calculated.')
    branch_site=parsed_branches[0] if parsed_branches else None
    if branch_site:
        idx=branch_site.get('anchor_index')
        raw_arm=str(branch_site.get('branch_text',''))
        if not isinstance(idx,int) or not 0<=idx<len(tokens) or tokens[idx]!='K':
            raise MassBalanceError('Only a single Lys ε-amine branch is currently supported.')
        if not re.fullmatch(r'[ARNDCQEGHILKMFPSTWYV]+',raw_arm):
            raise MassBalanceError('Branch arm must be unambiguous one-letter L-amino-acid sequence; protected/D/modified arms need an explicit chemical graph.')
        if raw_arm!= ''.join(branch_site.get('branch_tokens') or []):
            raise MassBalanceError('Branch tokenization differs from literal arm sequence; MW blocked.')
        if not raw_arm or str(sequence).count('(')!=str(sequence).count(')'):
            raise MassBalanceError('Unbalanced or empty branch notation; MW blocked.')
        # In K(Dde)(GGEP), Dde is an assembly handle to be REMOVED before
        # the Lys epsilon amide forms; do not retain its mass in the product.
        # Direct K(GGEP) likewise consumes the Lys side-chain amine.
        if idx in explicit and explicit[idx] not in ('Dde','ivDde','Mtt','Fmoc','Alloc') and not str(explicit[idx]).startswith('UNKNOWN:'):
            raise MassBalanceError('Lys branch anchor has an incompatible retained protection; manual structure review required.')
        explicit.pop(idx,None)
    notes=list(warnings)
    total=0.0
    protected_add=0.0
    records=[]
    for i,tok in enumerate(tokens):
        aa=_as_aa(tok)
        candidate=catalog.get(str(tok)) or (catalog.get(aa) if aa else None)
        if candidate is None:
            raise MassBalanceError(f'Unrecognized residue: {tok!r}; register exact chemistry before MW calculations')
        base=_float_mw(candidate,'Product MW contribution (g/mol)')
        if base is None:
            raise MassBalanceError(f'Missing neutral residue mass: {tok!r}')
        if i in explicit:
            group=explicit[i]
        elif side_chain_mode=='catalog':
            group=_default_protection(tok,catalog)
            if group:
                notes.append(f'{i+1}:{tok} side-chain {group} assumed from catalog Fmoc precursor; verify actual bottle and retention')
        else:
            group=None
        if branch_site and i==branch_site['anchor_index']:
            group=None
        if side_chain_mode=='none':
            group=None
        if group and group not in PROTECTING_DELTA:
            raise MassBalanceError(f'Unrecognized protecting group on position {i+1}: {group}')
        total+=base
        add=PROTECTING_DELTA.get(group,0.0)
        protected_add+=add
        records.append({'position':i+1,'residue':tok,'base_residue_mw':base,
                        'protecting_group':group,'protection_delta':add})
    branch_info=[]
    if branch_site:
        # Attachment: Lys-NH2 + H2N-(AA)n-COOH -> Lys-NHCO-(AA)n + H2O.
        # The branch arm's standalone linear mass is sum(residue MW) + H2O.
        # Condensation loses the same H2O: net branch contribution is exactly
        # sum(residue MW), provided the topology and terminal groups above hold.
        notes.append('Lys ε-amide branch: branch residue masses added, with one H2O lost on attachment; branch N-terminus presumed free.')
        notes.append('Lys branch anchor deprotected before attachment; catalog Lys(Boc) or temporary Dde/ivDde/Mtt not retained at branch site.')
        for j,arm_tok in enumerate(branch_site['branch_tokens'],1):
            row=catalog.get(arm_tok)
            if row is None:
                raise MassBalanceError(f'Unknown branch arm residue: {arm_tok}')
            aa_mass=_float_mw(row,'Product MW contribution (g/mol)')
            if aa_mass is None:
                raise MassBalanceError(f'Missing branch residue MW: {arm_tok}')
            pg=_default_protection(arm_tok,catalog) if side_chain_mode=='catalog' else None
            if pg and pg not in PROTECTING_DELTA:
                raise MassBalanceError(f'Unknown protecting group on branch residue {j}')
            pg_mass=PROTECTING_DELTA.get(pg,0.0)
            total+=aa_mass
            protected_add+=pg_mass
            records.append({'position':f'branch1:{j}','chain':'branch1',
                            'residue':arm_tok,'base_residue_mw':aa_mass,
                            'protecting_group':pg,'protection_delta':pg_mass})
            branch_info.append({'branch_position':j,'residue':arm_tok,'protecting_group':pg})
    from .engine import resin_family
    family=resin_family(resin)
    expected_cterm='NH2' if family=='Amide' else 'OH'
    cterm_marker=str(cterm_override or cterm or expected_cterm).upper()
    if cterm_marker in ('CONH2','AMIDE'): cterm_marker='NH2'
    if cterm_marker in ('COOH','CO2H','ACID'): cterm_marker='OH'
    if cterm_marker not in ('NH2','OH'):
        raise MassBalanceError(f'Unsupported C-terminal chemistry {cterm_marker}')
    if cterm and cterm_marker != expected_cterm:
        notes.append(f'Explicit C-terminal {cterm_marker} conflicts with inferred resin {expected_cterm}. Confirm actual linker and terminal chemistry.')
    # Neutral linear acid = sum of neutral residues + H2O; neutral amide
    # replaces terminal OH by NH2 (O -> NH, -0.984 Da).
    terminal=18.01528 if cterm_marker=='OH' else 17.03052
    nterm_key='ac-building-block' if ac_aa_in_catalog else str(nterm).strip().lower()
    nterm_add={'':0.,'ac':42.04,'boc':100.12,'fmoc':222.24,
               'ac-building-block':0.0}.get(nterm_key)
    if nterm_add is None:
        raise MassBalanceError(f'N-terminal group {nterm!r} requires an exact molecular formula; no MW guessed')
    free_mw=total+terminal+nterm_add
    protected_mw=free_mw+protected_add
    allow_cyclization=not branch_site and cterm_marker=='OH' and not nterm_key and len(records)>=2
    if branch_site:
        notes.append('Cyclization of a branched peptide requires explicit connection sites; head-to-tail MW intentionally blocked.')
        notes.append('Intermediate Checklist MW is disabled for branch planning until branch reaction order and handle deprotection are tracked.')
    if len(records)<2:
        notes.append('Head-to-tail MW unavailable for one residue; no ordinary cyclic peptide macrocycle specified.')
    if cterm_marker != 'OH':
        notes.append('Head-to-tail blocked: free C-terminal COOH is required; amide is incompatible')
    if nterm_key:
        notes.append(f'Head-to-tail blocked: N-terminal {nterm} is capped; selective deprotection required')
    # A disagreement between resin and explicit C-terminus must be resolved
    # before a cyclization mass is released.
    if expected_cterm != cterm_marker:
        allow_cyclization=False
    if any(g=='Trt' for g in (r['protecting_group'] for r in records)):
        notes.append('Trt may be acid-labile under mild cleavage. Retained-group MW is conditional, not proof of actual product composition.')
    if any(g=='Fmoc' for g in (r['protecting_group'] for r in records)):
        notes.append('Side-chain Fmoc can be affected by piperidine cycles; confirm orthogonal protection strategy and retained groups.')
    if len(records)==2 and allow_cyclization:
        notes.append('Two-residue head-to-tail product is a diketopiperazine; review ring closure pathway separately.')
    return {
        'sequence':sequence, 'resin':resin, 'residue_count':len(records),
        'topology':'lysine_branch' if branch_site else 'linear',
        'branch_anchor_position':branch_site['anchor_index']+1 if branch_site else None,
        'branch_arm_residues':branch_info,
        'residues':records, 'cterm':cterm_marker, 'nterm':nterm or 'H',
        'mass_type':'average_neutral_mw_g_mol',
        'linear_deprotected_mw':round(free_mw,3),
        'linear_protected_mw':round(protected_mw,3),
        'selective_cleavage_mw':round(protected_mw,3),
        'head_to_tail_protected_mw':round(protected_mw-WATER_MW,3) if allow_cyclization else None,
        'head_to_tail_deprotected_mw':round(free_mw-WATER_MW,3) if allow_cyclization else None,
        'head_to_tail_allowed':allow_cyclization,
        'protecting_group_delta':round(protected_add,3),
        'water_loss_mw':WATER_MW,
        'warnings':notes,
        'conditions':'Purely theoretical. No salts, counterions, solvate, side reactions or partial deprotection included.'
    }

def estimate_mass_yield(mw, scale_mmol, *, copies=1, coupling_steps=0,
                        per_step_conversion=None, cyclization_recovery=None,
                        isolation_recovery=None):
    """User-supplied deterministic scenario, never an empirical prediction.

    0..1 fractions mandatory for any used factor. Returns theoretical mass even
    when insufficient evidence prevents a scenario estimate.
    """
    try:
        mass = float(mw)
        scale = float(scale_mmol)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('MW and scale must be positive finite numbers') from exc
    count = checked_integer(copies, 'copies')
    steps = checked_integer(coupling_steps, 'coupling_steps', minimum=0)
    if not all(math.isfinite(x) and x > 0 for x in (mass, scale)):
        raise ValueError('MW and scale must be positive finite numbers')
    theoretical_g = mass * scale * count / 1000.
    if not math.isfinite(theoretical_g):
        raise ValueError('Calculated theoretical mass is not finite; review entered values.')
    required=[per_step_conversion,isolation_recovery]
    if any(v is None or v=='' for v in required):
        return {'theoretical_g':round(theoretical_g,6),'scenario_g':None,'scenario_percent':None,
                'status':'NO_ESTIMATE_MISSING_USER_FACTORS'}
    try:
        factors = [float(per_step_conversion), float(isolation_recovery)]
        if cyclization_recovery is not None and cyclization_recovery != '':
            factors.append(float(cyclization_recovery))
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('All conversion/recovery factors must be numeric percentages expressed as fractions') from exc
    if not all(math.isfinite(v) and 0<=v<=1 for v in factors):
        raise ValueError('All user-supplied conversion/recovery factors must be within 0–1')
    fraction=(factors[0]**steps)*math.prod(factors[1:])
    return {'theoretical_g':round(theoretical_g,6),'scenario_g':round(theoretical_g*fraction,6),
            'scenario_percent':round(fraction*100,3),'status':'OPERATOR_SCENARIO_NOT_VALIDATED',
            'model': 'mw(g/mol) × scale(mmol) / 1000 × copies × per_step_conversion^coupling_steps × recoveries'}
