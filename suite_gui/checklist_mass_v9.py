"""V9 checklist per-operation free-peptide-equivalent mass (not resin-bound mass).

This is a read-only overlay to the existing editable protocol. It never alters
reagent equivalents or coupling execution.
"""
from spps_planner.mass_balance_v9 import calculate_mass_states, MassBalanceError, FMOC_MASS_ADD

def add_process_stages(checklist, mass, options):
    """Append review-only product transformations requested in Auto Plan.

    Does NOT generate or validate an actual selective cleavage/cyclization method.
    """
    mode=str(options.get('product_path','linear_deprotected'))
    if mode not in {'linear_protected','head_to_tail_protected','head_to_tail_deprotected'}:
        return
    def add(op, mw, form, note):
        checklist.append({'line':len(checklist)+1,'done':'','checked_at':'',
                          'operation':op,'unit':'Product transformation',
                          'peptide_mw':f'{mw:.3f}' if mw is not None else '',
                          'mw_form':form,'next_step':'','note':note})
    acid=mass['cterm']=='OH'
    if mode in ('head_to_tail_protected','head_to_tail_deprotected') and not mass['head_to_tail_allowed']:
        add('Cyclization BLOCKED',None,'not calculable',
            'Free N-terminal amine AND C-terminal COOH required; check resin and end groups')
        return
    if not acid:
        add('Selective cleavage review', None,'blocked',
            'Protected selective cleavage needs a verified compatible free-acid resin/linker')
        return
    add('Selective cleavage — protected form',mass['selective_cleavage_mw'],
        'linear, side-chain-protected',
        'Requires verified orthogonal method; not the standard global-TFA Cleavage Cocktail. Retained groups are assumptions.')
    if mode.startswith('head_to_tail'):
        selected=options.get('reaction_review')
        method_note='NO METHOD SELECTED: only theoretical −H2O; actual reaction chemistry NOT validated'
        if isinstance(selected,dict) and selected.get('reaction_type')=='head_to_tail' and selected.get('bond')=='head_to_tail_amide':
            # Never imply the selected method is part of the existing chemical
            # Plan or calculated Materials; it is an unapproved review attachment.
            try:
                if (selected.get('sequence')==mass['sequence'] and selected.get('resin')==mass['resin']
                    and abs(float(selected.get('protected_cyclic_mw'))-float(mass['head_to_tail_protected_mw']))<0.002):
                    parts=[f"USER METHOD (NOT APPROVED): {selected.get('system_label','unspecified')}",
                           f"Status {selected.get('method_status','unknown')}"]
                    parts += [f"{r['name']} {r['equivalents']} eq" for r in selected.get('reagents',[])
                              if r.get('equivalents') is not None]
                    if selected.get('concentration_mm') is not None:
                        parts.append(f"{selected['concentration_mm']} mM")
                    if selected.get('reaction_time_h') is not None:
                        parts.append(f"{selected['reaction_time_h']} h")
                    method_note='; '.join(parts)+'; verify operator conditions, stereochemistry, MS/HPLC'
                else:
                    method_note='STALE METHOD: mass mismatch; reopen Auto Plan and re-review.'
            except (TypeError, ValueError):
                method_note='INVALID METHOD DATA: re-review required.'
        add('Head-to-tail cyclization — review',mass['head_to_tail_protected_mw'],
            'cyclic, side-chain-protected',method_note)
    if mode=='head_to_tail_deprotected':
        add('Global side-chain deprotection — review',mass['head_to_tail_deprotected_mw'],
            'cyclic, fully deprotected',
            'Assumes all side-chain protections removed; confirm MS/HPLC and approved workup')

def make_mass_tracker(sequence,resin,options=None):
    options=options or {}
    mass=calculate_mass_states(sequence,resin,
        side_chain_mode=str(options.get('side_chain_mode','catalog')))
    if mass.get('topology')=='lysine_branch':
        raise MassBalanceError('Branch total-product MW is available in Auto Plan, but stepwise Checklist MW requires validated branch assembly order and is intentionally unavailable.')
    recs=mass['residues']
    def mw(count,*,has_fmoc=False,cap=''):
        if count<=0:
            return None
        residues=recs[len(recs)-min(count,len(recs)):]
        terminal=18.01528 if mass['cterm']=='OH' else 17.03052
        extra=FMOC_MASS_ADD if has_fmoc else 0.
        if cap in ('Ac','Boc'):
            extra+=42.04 if cap=='Ac' else 100.12
        return sum(r['base_residue_mw']+r['protection_delta'] for r in residues)+terminal+extra
    return mass,mw


def append_crosslink_structure_review(checklist, sequence, resin, review):
    """Read-only Checklist annotation; no actual cyclization/coupling action.

    Rebuild the molecular graph rather than trusting a stored mass or status.
    Stale/corrupted/unsupported data show an empty MW and explicit warning.
    """
    if not isinstance(review, dict) or review.get('status') != 'UNAPPROVED_REVIEW_ONLY':
        return
    label = 'Independent cross-link molecular graph review (NO synthesis step)'
    reason = 'No approved reaction method, conversion, stereochemical integrity, or experimental structure demonstrated.'
    mw = None
    state = 'unverified'
    if review.get('sequence') != sequence or review.get('resin') != resin:
        state='stale: sequence/resin changed'
    else:
        try:
            from spps_planner.extended_structure_v9 import graph_crosscheck
            custom=review.get('topology')=='atom_mapped_custom'
            if custom:
                from spps_planner.atomic_topology_v9 import calculate_atomic_topology
                actual=calculate_atomic_topology(review.get('schema'))
                wanted_status='ATOM_MAPPED_GRAPH_PASS'
                actual_mass='average_mw'
            else:
                actual=graph_crosscheck(sequence,resin,
                    topology=review.get('topology'),sites=review.get('sites'),
                    side_chain_mode=review.get('side_chain_mode'))
                wanted_status='CROSSCHECK_PASS'
                actual_mass='product_graph_mw'
            stored=review.get('graph') or {}
            if (actual.get('status')==wanted_status and stored.get('status')==wanted_status
                and actual.get('formula' if custom else 'product_formula')==stored.get('formula' if custom else 'product_formula')
                and actual.get('product_smiles')==stored.get('product_smiles')
                and abs(actual[actual_mass]-float(stored[actual_mass]))<0.002):
                mw=actual[actual_mass]
                state=('operator-mapped graph, review pending' if custom else 'graph-computed, operator review pending')
                ions=actual.get('theoretical_ms_ions',{}).get('positive_ion_candidates',[])
                if ions:
                    first=ions[0]
                    reason += (f" Theoretical MS {first['label']} m/z {first['mz']:.5f}"
                               '; NOT an observed analytical peak.')
            else:
                state='graph stale/unresolved: reopen Auto Plan'
        except (ValueError, KeyError, TypeError, OverflowError, RuntimeError):
            state='invalid graph data; repeat independent verification'
    checklist.append({'line':len(checklist)+1,'done':'','checked_at':'',
                      'operation':label,'unit':'STRUCTURAL REVIEW ONLY',
                      'peptide_mw':f'{mw:.3f}' if mw is not None else '',
                      'mw_form':state,'next_step':'',
                      'note':reason})
