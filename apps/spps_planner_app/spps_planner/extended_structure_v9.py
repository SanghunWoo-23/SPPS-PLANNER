"""V9.0.0: independent, strictly bounded RDKit graph checks for peptides.

This is *not* a reaction predictor, conformational model, or validated protocol.
It deliberately refuses unmodelled functional groups and ambiguous links rather
than falling back to legacy group mass differences. Optional RDKit dependency.
"""
from __future__ import annotations

import math
from typing import Any

_SUPPORTED_PG = {
    ('S', 'tBu'): ('OG', 'C(C)(C)C', 0),
    ('T', 'tBu'): ('OG1', 'C(C)(C)C', 0),
    ('Y', 'tBu'): ('OH', 'C(C)(C)C', 0),
    ('D', 'OtBu'): ('OD2', 'C(C)(C)C', 0),
    ('E', 'OtBu'): ('OE2', 'C(C)(C)C', 0),
    ('K', 'Boc'): ('NZ', 'C(=O)OC(C)(C)C', 0),
    ('C', 'Acm'): ('SG', 'CNC(C)=O', 0),
    ('C', 'StBu'): ('SG', 'SC(C)(C)C', 0),
    ('C', 'Trt'): ('SG', 'C(c1ccccc1)(c1ccccc1)c1ccccc1', 0),
}
_ALLOWED = {'linear', 'head_to_tail', 'lysine_branch', 'lysine_branch_head_to_tail', 'disulfide', 'sidechain_lactam'}


def _atom(mol, residue: int, name: str, *, offset: int = 0) -> int:
    found = []
    for atom in mol.GetAtoms():
        info = atom.GetPDBResidueInfo()
        if info and info.GetResidueNumber() == residue and info.GetName().strip() == name:
            found.append(atom.GetIdx() + offset)
    if len(found) != 1:
        raise ValueError(f'Ambiguous or missing atom {residue}:{name}')
    return found[0]


def _add_group(mol, target: int, fragment: str, attachment: int = 0):
    from rdkit import Chem
    group = Chem.MolFromSmiles(fragment)
    if group is None:
        raise ValueError('Unsupported chemical fragment')
    combination = Chem.CombineMols(mol, group)
    edit = Chem.RWMol(combination)
    edit.AddBond(target, mol.GetNumAtoms() + attachment, Chem.BondType.SINGLE)
    result = edit.GetMol()
    Chem.SanitizeMol(result)
    return result


def _remove_and_bond(mol, start: int, end: int, removed: int):
    from rdkit import Chem
    if len({start, end, removed}) != 3:
        raise ValueError('Invalid reaction-site mapping')
    edit = Chem.RWMol(mol)
    edit.AddBond(start, end, Chem.BondType.SINGLE)
    edit.RemoveAtom(removed)
    result = edit.GetMol()
    Chem.SanitizeMol(result)
    return result


def _build_linear(molstring: str, residue_records: list[dict], *, nterm: str, cterm: str):
    from rdkit import Chem
    mol = Chem.MolFromSequence(molstring)
    if mol is None:
        raise ValueError('Unable to build peptide molecular graph')
    for row in residue_records:
        pos = row['position']
        aa = str(row['residue'])
        if aa.startswith('d') and len(aa) == 2 and aa[1] != 'G':
            ca = mol.GetAtomWithIdx(_atom(mol, pos, 'CA'))
            if ca.GetChiralTag() == Chem.ChiralType.CHI_UNSPECIFIED:
                raise ValueError('Unassigned alpha stereochemistry')
            ca.InvertChirality()
    Chem.AssignStereochemistry(mol, cleanIt=True, force=True)
    for row in residue_records:
        pg = row.get('protecting_group')
        if pg:
            aa = str(row['residue'])[-1]
            choice = _SUPPORTED_PG.get((aa, pg))
            if choice is None:
                raise ValueError(f'Graph structure unavailable for {aa}({pg})')
            name, fragment, atom_idx = choice
            mol = _add_group(mol, _atom(mol, int(row['position']), name), fragment, atom_idx)
    if nterm.lower() == 'ac':
        mol = _add_group(mol, _atom(mol, 1, 'N'), 'CC=O', 1)
    elif nterm.lower() == 'boc':
        mol = _add_group(mol, _atom(mol, 1, 'N'), 'C(=O)OC(C)(C)C')
    elif nterm.lower() not in ('h', ''):
        raise ValueError(f'Unsupported N-terminal group {nterm}')
    if cterm == 'NH2':
        edit = Chem.RWMol(mol)
        oxygen = _atom(mol, len(residue_records), 'OXT')
        neighbor = edit.GetAtomWithIdx(oxygen).GetNeighbors()
        if len(neighbor) != 1 or neighbor[0].GetSymbol() != 'C':
            raise ValueError('Unsupported C-terminal acid topology')
        parent = neighbor[0].GetIdx()
        nitrogen = edit.AddAtom(Chem.Atom('N'))
        edit.AddBond(parent, nitrogen, Chem.BondType.SINGLE)
        edit.RemoveAtom(oxygen)
        mol = edit.GetMol()
        Chem.SanitizeMol(mol)
    elif cterm != 'OH':
        raise ValueError('Unsupported C-terminal group')
    return mol


def _branch_attach(mol, arm_sequence: str, anchor: int):
    """Join the unmodified arm C terminus to main-chain Lys NZ by an amide."""
    from rdkit import Chem
    arm = Chem.MolFromSequence(arm_sequence)
    if arm is None:
        raise ValueError('Unsupported branch arm')
    if not arm_sequence or len(arm_sequence) > 128:
        raise ValueError('Branch length out of range')
    n = mol.GetNumAtoms()
    main_n = _atom(mol, anchor, 'NZ')
    arm_carbon = _atom(arm, len(arm_sequence), 'C') + n
    arm_oh = _atom(arm, len(arm_sequence), 'OXT') + n
    return _remove_and_bond(Chem.CombineMols(mol, arm), main_n, arm_carbon, arm_oh)


def graph_crosscheck(sequence: str, resin: str, *, topology: str = 'linear',
                     side_chain_mode: str = 'explicit', sites: tuple[int, int] | None = None,
                     tolerance_g_mol: float = 0.35) -> dict[str, Any]:
    """Build a *supported* graph and compare average mass to independent rules.

    Supports natural L/D residues; S/T/Y(tBu), D/E(OtBu), K(Boc),
    C(Acm/StBu/Trt);
    one explicitly named Lys epsilon amide branch (natural L arm);
    head-to-tail amide (also main-chain ring with one Lys epsilon branch),
    Cys-Cys disulfide, or Lys-to-Asp/Glu lactam.
    Requires explicit 1-based sites for side-chain rings. Disallows caps or
    protection that block closure. All unsupported cases return WITHHELD.
    """
    if topology not in _ALLOWED:
        return {'status': 'WITHHELD_UNSUPPORTED_REACTION', 'reason': 'Unrecognized topology.'}
    if not isinstance(sequence, str) or not sequence.strip() or len(sequence) > 512:
        return {'status': 'WITHHELD_INVALID_INPUT', 'reason': 'Invalid peptide sequence length.'}
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors
    except ImportError:
        return {'status':'OPTIONAL_RDKIT_NOT_INSTALLED','reason':'Install optional RDKit.'}
    try:
        from .mass_balance_v9 import calculate_mass_states
        status = calculate_mass_states(sequence, resin, side_chain_mode=side_chain_mode)
        records = status['residues']
        main = [r for r in records if isinstance(r['position'], int)]
        if len(main) < 1 or len(main) > 128:
            raise ValueError('Main-chain length unsupported')
        letters = []
        for row in main:
            token = str(row['residue'])
            aa = token[-1]
            if aa not in 'ACDEFGHIKLMNPQRSTVWY' or token not in (aa, 'd' + aa):
                raise ValueError('Noncanonical residue requires explicit atom definitions')
            letters.append(aa)
        mol = _build_linear(''.join(letters), main, nterm=status['nterm'], cterm=status['cterm'])
        branch = status['topology'] == 'lysine_branch'
        backbone_sites = None
        if branch:
            # Capture main-chain atoms BEFORE CombineMols: the branch has its
            # own residue 1 N and PDB labels can no longer uniquely identify
            # the main chain. Main indices stay stable when arm OXT is removed.
            backbone_sites = (_atom(mol, 1, 'N'),
                              _atom(mol, len(main), 'C'),
                              _atom(mol, len(main), 'OXT'))
            if topology not in ('lysine_branch', 'lysine_branch_head_to_tail'):
                raise ValueError('Branch topology requires explicit branch graph mode')
            arm = status.get('branch_arm_residues') or []
            if any(r.get('protecting_group') for r in arm):
                raise ValueError('Protected branch arm requires explicit atom modelling')
            mol = _branch_attach(mol, ''.join(str(r['residue']) for r in arm), status['branch_anchor_position'])
        elif topology in ('lysine_branch','lysine_branch_head_to_tail'):
            raise ValueError('No branch arm/anchor in sequence')
        initial_mw = Descriptors.MolWt(mol)
        expected_initial = status['linear_protected_mw']
        if abs(initial_mw - expected_initial) > tolerance_g_mol:
            return {'status':'CROSSCHECK_DISCREPANCY','difference_g_mol':round(initial_mw-expected_initial,4),
                    'reason':'Graph differs from existing protected mass rules; product graph withheld.'}
        if topology in ('head_to_tail','lysine_branch_head_to_tail'):
            if branch and topology!='lysine_branch_head_to_tail':
                raise ValueError('Branched macrocycles require explicit branch head-to-tail mode')
            if not branch and not status['head_to_tail_allowed']:
                raise ValueError('Free N/C termini required for head-to-tail closure')
            if branch and (status['cterm']!='OH' or status['nterm']!='H' or len(main)<2):
                raise ValueError('Branch main-chain cyclization requires two or more residues and free N/C termini')
            from .structure_crosscheck_v9 import _cyclize_linear
            mol = _cyclize_linear(mol,main_sites=backbone_sites)
        elif topology in ('disulfide','sidechain_lactam'):
            if not isinstance(sites, (tuple,list)) or len(sites) != 2 or any(type(p) is not int for p in sites):
                raise ValueError('Two explicit 1-based integer residue positions are required')
            a, b = sites
            if a == b or a < 1 or b < 1 or a > len(main) or b > len(main):
                raise ValueError('Two distinct valid reaction sites are required')
            names = {a: letters[a-1], b: letters[b-1]}
            if topology == 'disulfide':
                if any(x != 'C' for x in names.values()):
                    raise ValueError('Disulfide sites must both be cysteine residues')
                if main[a-1].get('protecting_group') or main[b-1].get('protecting_group'):
                    raise ValueError('Cysteine thiols are protected')
                edit = Chem.RWMol(mol)
                edit.AddBond(_atom(mol,a,'SG'), _atom(mol,b,'SG'), Chem.BondType.SINGLE)
                mol = edit.GetMol()
                Chem.SanitizeMol(mol)
            else:
                if set(names.values()) not in ({'K','D'},{'K','E'}):
                    raise ValueError('Lactam requires one Lys and one Asp/Glu')
                k = a if names[a] == 'K' else b
                acid = b if k == a else a
                if main[k-1].get('protecting_group') or main[acid-1].get('protecting_group'):
                    raise ValueError('Lactam reactive side chains remain protected')
                kind = letters[acid-1]
                side_carbon = _atom(mol, acid, 'CG' if kind == 'D' else 'CD')
                oh = _atom(mol, acid, 'OD2' if kind == 'D' else 'OE2')
                mol = _remove_and_bond(mol, _atom(mol, k, 'NZ'), side_carbon, oh)
        result = {'status':'CROSSCHECK_PASS', 'topology':topology,'mass_type':'average_neutral_mw_g_mol',
                  'linear_graph_mw':round(initial_mw,4),
                  'product_graph_mw':round(Descriptors.MolWt(mol),4),
                  'product_exact_mass':round(rdMolDescriptors.CalcExactMolWt(mol),5),
                  'product_formula':rdMolDescriptors.CalcMolFormula(mol),
                  'product_smiles':Chem.MolToSmiles(mol, isomericSmiles=True),
                  'residue_count':len(records),'verified_scope':'Explicit, bounded RDKit graph and neutral masses only',
                  'warnings':['No evidence of reaction feasibility, stereochemical integrity after synthesis, or experimentally observed product.']}
        if topology in ('head_to_tail','lysine_branch_head_to_tail'):
            # Existing mass engine correctly WITHHOLDS branch cyclization as a
            # general prediction. For this narrowly explicit topology only,
            # cross-check conservation of mass (one H2O for one amide bond).
            expected = (status['linear_protected_mw'] - 18.01528
                        if branch else status['head_to_tail_protected_mw'])
            result['difference_g_mol']=round(result['product_graph_mw'] - expected,4)
            if abs(result['difference_g_mol']) > tolerance_g_mol:
                result['status']='CROSSCHECK_DISCREPANCY'
        if topology == 'disulfide' and abs((initial_mw - result['product_graph_mw'])-2.01588)>0.005:
            result['status']='CROSSCHECK_DISCREPANCY'
        if topology == 'sidechain_lactam' and abs((initial_mw - result['product_graph_mw'])-18.01528)>0.005:
            result['status']='CROSSCHECK_DISCREPANCY'
        if result['status']=='CROSSCHECK_PASS':
            from .ms_ions_v9 import theoretical_ms_ions
            result['theoretical_ms_ions'] = theoretical_ms_ions(result['product_exact_mass'])
        return result
    except (ValueError, TypeError, KeyError, IndexError, RuntimeError) as exc:
        return {'status':'WITHHELD_UNSUPPORTED_CHEMISTRY','reason':str(exc), 'topology':topology,
                'note':'No MW or structural identity inferred for unsupported sites or protections.'}
