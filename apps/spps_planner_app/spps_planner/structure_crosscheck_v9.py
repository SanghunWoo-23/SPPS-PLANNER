"""Optional independent RDKit structure/mass cross-check for unmodified peptides.

Uses an actual molecular graph, with an explicitly constructed head-to-tail amide
ring. Unsupported labels or chemistry return WITHHELD, never an invented formula.
This module never changes the established SPPS quantity calculation engine.
"""
from __future__ import annotations
import re
from typing import Any

NATURAL = re.compile(r"[ACDEFGHIKLMNPQRSTVWY]{2,128}\Z")


def _cyclize_linear(molecule, *, main_sites=None):
    """Close the *backbone* amine and carboxyl, never a side-chain amine.

    `main_sites` are absolute atom indices (N, terminal C, terminal OXT)
    captured before attaching a branch. In non-branched molecules PDB atom
    identity is used to avoid treating a free Lys side-chain NZ as N-terminus.
    Every site must remain an available functional group; no guessed caps.
    """
    from rdkit import Chem
    edit = Chem.RWMol(molecule)
    if main_sites is None:
        nsites = []
        acids = []
        for atom in edit.GetAtoms():
            pdb = atom.GetPDBResidueInfo()
            if pdb is None:
                continue
            label = pdb.GetName().strip()
            if label == 'N' and pdb.GetResidueNumber() == 1:
                nsites.append(atom.GetIdx())
            if label == 'OXT':
                acids.append((pdb.GetResidueNumber(), atom.GetIdx()))
        if len(nsites) != 1 or len(acids) != 1:
            raise ValueError('Unambiguous alpha-terminal PDB atom mapping is required.')
        nidx = nsites[0]
        ohidx = acids[0][1]
        acid_neighbors = [a.GetIdx() for a in edit.GetAtomWithIdx(ohidx).GetNeighbors() if a.GetSymbol() == 'C']
        if len(acid_neighbors) != 1:
            raise ValueError('Unique terminal carboxyl carbon required.')
        cidx = acid_neighbors[0]
    else:
        if len(main_sites) != 3 or any(type(i) is not int for i in main_sites):
            raise ValueError('Explicit N, carbonyl C and OXT atom IDs are required.')
        nidx, cidx, ohidx = main_sites
    if len({nidx,cidx,ohidx}) != 3 or any(i < 0 or i >= edit.GetNumAtoms() for i in (nidx,cidx,ohidx)):
        raise ValueError('Reaction sites are invalid or duplicate.')
    n=edit.GetAtomWithIdx(nidx)
    c=edit.GetAtomWithIdx(cidx)
    hydroxyl=edit.GetAtomWithIdx(ohidx)
    if n.GetSymbol()!='N' or c.GetSymbol()!='C' or hydroxyl.GetSymbol()!='O':
        raise ValueError('Head-to-tail sites must be N, carbonyl C and hydroxyl O.')
    # Free alpha amines include a secondary Pro alpha-amine. Reject N-acylated
    # terminals by checking for carbonyl substituents.
    if n.GetTotalNumHs() not in (1,2) or n.GetDegree() not in (1,2):
        raise ValueError('Free primary/secondary N-terminal alpha-amine required.')
    for neighbor in n.GetNeighbors():
        if neighbor.GetSymbol() == 'C' and any(
            bond.GetBondType()==Chem.BondType.DOUBLE and bond.GetOtherAtom(neighbor).GetSymbol()=='O'
            for bond in neighbor.GetBonds()
        ):
            raise ValueError('N-terminal alpha-amine is acylated and unavailable.')
    bonds = {other.GetIdx(): edit.GetBondBetweenAtoms(cidx,other.GetIdx()) for other in c.GetNeighbors()}
    if ohidx not in bonds or bonds[ohidx].GetBondType()!=Chem.BondType.SINGLE or hydroxyl.GetDegree()!=1 or hydroxyl.GetTotalNumHs()!=1:
        raise ValueError('Unprotected terminal carboxylic acid OH required.')
    if not any(bond.GetBondType()==Chem.BondType.DOUBLE and bond.GetOtherAtom(c).GetSymbol()=='O'
               for bond in c.GetBonds()):
        raise ValueError('Free terminal carbonyl carboxylic acid required.')
    edit.RemoveAtom(ohidx)
    if nidx > ohidx: nidx-=1
    if cidx > ohidx: cidx-=1
    edit.AddBond(nidx,cidx,Chem.BondType.SINGLE)
    result=edit.GetMol()
    Chem.SanitizeMol(result)
    return result


def independent_mass_check(sequence: str, *, expected: dict[str,Any]|None=None,
                           tolerance_g_mol: float=0.35) -> dict[str,Any]:
    """Cross-check only natural L-aa peptides with free termini.

    Average neutral MW is compared with legacy mass calculation. This does
    not independently confirm protecting groups, salts, resin fragments,
    D-forms, modifications, branches, or synthesis feasibility.
    """
    if not isinstance(sequence,str) or not NATURAL.fullmatch(sequence):
        return {'status':'WITHHELD_UNSUPPORTED_TOPOLOGY', 'reason':
                'RDKit comparison requires simple natural L-residue sequence, free N/C termini.'}
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors, rdMolDescriptors
    except ImportError:
        return {'status':'OPTIONAL_RDKIT_NOT_INSTALLED','reason':'Install optional rdkit dependency to cross-check a structure.'}
    linear=Chem.MolFromSequence(sequence)
    if linear is None:
        return {'status':'WITHHELD_UNPARSABLE','reason':'RDKit could not generate the molecular structure.'}
    cycle=_cyclize_linear(linear)
    observed={'linear_mw':round(Descriptors.MolWt(linear),3),
              'cyclic_mw':round(Descriptors.MolWt(cycle),3),
              'linear_formula':rdMolDescriptors.CalcMolFormula(linear),
              'cyclic_formula':rdMolDescriptors.CalcMolFormula(cycle),
              'cyclic_smiles':Chem.MolToSmiles(cycle)}
    comparisons={}
    if expected:
        if expected.get('cterm')!='OH' or expected.get('nterm')!='H':
            return {'status':'WITHHELD_TERMINI_MISMATCH',**observed,
                    'reason':'Current expected product has capped/amidated termini.'}
        for key,out in (('linear_deprotected_mw','linear_mw'),
                        ('head_to_tail_deprotected_mw','cyclic_mw')):
            value=expected.get(key)
            if value is not None:
                comparisons[key]={'difference_g_mol':round(observed[out]-float(value),3),
                                   'within_tolerance':abs(observed[out]-float(value))<=tolerance_g_mol}
    status='CROSSCHECK_PASS' if all(x['within_tolerance'] for x in comparisons.values()) else 'CROSSCHECK_DISCREPANCY'
    return {'status':status,'source':'RDKit molecular graph; independent unprotected product check',
            'mass_type':'average_neutral_mw_g_mol',**observed,'comparisons':comparisons,
            'limitations':'No experimental confirmation; protecting-group mass and structure are not graph-validated.'}
