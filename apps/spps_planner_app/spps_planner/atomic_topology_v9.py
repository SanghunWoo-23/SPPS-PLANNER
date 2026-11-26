"""V9.0.0 operator-defined peptide atom topology, independent of the SPPS engine.

Every monomer supplies *explicit* RDKit atom-mapped SMILES. Atom maps are
1 = free alpha amine N, 2 = alpha carboxyl carbon, 3 = acidic OH oxygen;
10+ mark optional reaction sites. This schema admits noncanonical amino acids,
protected groups, many branches/rings, without pretending to know their names.

Bond steps are deliberately narrow chemically typed transformations, NOT SOPs.
SMILES and graph mass are theoretical, not evidence of feasibility or yield.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

MAX_MONOMERS = 128
MAX_STEPS = 32
MAX_ATOMS = 4096
_ALLOWED = {'amide', 'disulfide', 'thioether_substitution', 'thiol_michael', 'rcm', 'cuaac_1_4'}
_REF = re.compile(r'^(\d{1,3}):(\d{1,3})$')
_STEP_FIELDS = {
    'amide': {'amine', 'carboxyl', 'leaving_oxygen'},
    'disulfide': {'a', 'b'},
    'thioether_substitution': {'sulfur', 'carbon', 'leaving'},
    'thiol_michael': {'sulfur', 'alkene_attacked', 'alkene_other'},
    'rcm': {'alkene_1', 'alkene_2', 'terminal_1', 'terminal_2'},
    'cuaac_1_4': {'azide_alpha', 'azide_central', 'azide_terminal', 'alkyne_terminal', 'alkyne_inner'},
}


def _strict_keys(value, allowed, context):
    if not isinstance(value, dict):
        raise TopologyError(f'{context} must be a JSON object.')
    unknown = set(value) - allowed
    if unknown:
        raise TopologyError(f'{context}: unrecognized fields: {sorted(map(str, unknown))!r}.')


class TopologyError(ValueError):
    pass


def _ref(text: str) -> str:
    if not isinstance(text, str) or not _REF.fullmatch(text):
        raise TopologyError('An explicit residue:atom-map reference is required (e.g., 2:10).')
    return text


def _read_monomer(spec: dict, position: int):
    from rdkit import Chem
    if not isinstance(spec, dict) or not isinstance(spec.get('smiles'), str):
        raise TopologyError('Each monomer requires mapped SMILES.')
    _strict_keys(spec, {'name', 'smiles', 'token', 'source'}, 'Monomer')
    s = spec['smiles'].strip()
    if not s or len(s) > 800 or '.' in s:
        raise TopologyError('SMILES must describe one connected, bounded monomer.')
    molecule = Chem.MolFromSmiles(s)
    if molecule is None or molecule.GetNumAtoms() > 128:
        raise TopologyError('Invalid or oversized monomer structure.')
    seen = {}
    for a in molecule.GetAtoms():
        m=a.GetAtomMapNum()
        if m:
            if m in seen:
                raise TopologyError('Duplicate atom map in monomer.')
            seen[m] = a.GetIdx()
            a.SetProp('_spps_ref', f'{position}:{m}')
            a.SetAtomMapNum(0)
    if not all(i in seen for i in (1,2,3)):
        raise TopologyError('Each monomer must map the amine N(1), carboxyl C(2), and OH O(3).')
    if any(atom.GetNumRadicalElectrons() for atom in molecule.GetAtoms()):
        raise TopologyError('Radical/unsaturated valence monomers must be represented with fully specified neutral SMILES.')
    from rdkit.Chem import FindMolChiralCenters
    if any(stereochemistry=='?' for _,stereochemistry in FindMolChiralCenters(molecule,includeUnassigned=True)):
        raise TopologyError('Unspecified stereocenter: provide explicit @/@@ in monomer SMILES.')
    n, carbon, oxygen = (molecule.GetAtomWithIdx(seen[i]) for i in (1,2,3))
    if n.GetSymbol() != 'N' or n.GetTotalNumHs() < 1 or n.GetFormalCharge() != 0:
        raise TopologyError('Mapped alpha-amine must be neutral and have an available hydrogen.')
    if carbon.GetSymbol() != 'C' or oxygen.GetSymbol() != 'O' or oxygen.GetTotalNumHs() != 1:
        raise TopologyError('Mapped carboxyl requires carbonyl C and free OH.')
    b=molecule.GetBondBetweenAtoms(carbon.GetIdx(),oxygen.GetIdx())
    if b is None or b.GetBondType() != Chem.BondType.SINGLE or oxygen.GetDegree()!=1:
        raise TopologyError('Mapped OH must be directly attached to carboxyl carbon.')
    if not any(x.GetSymbol()=='O' and molecule.GetBondBetweenAtoms(carbon.GetIdx(),x.GetIdx()).GetBondType()==Chem.BondType.DOUBLE
               for x in carbon.GetNeighbors()):
        raise TopologyError('Mapped C must be a carboxylic acid carbonyl carbon.')
    return molecule


def _idx(mol, ref):
    requested=_ref(ref)
    matched=[a.GetIdx() for a in mol.GetAtoms() if a.HasProp('_spps_ref') and a.GetProp('_spps_ref')==requested]
    if len(matched)!=1:
        raise TopologyError(f'Unknown or consumed atom reference: {requested}.')
    return matched[0]


def _validate_amine(mol, atom):
    if atom.GetSymbol() != 'N' or atom.GetFormalCharge()!=0 or atom.GetTotalNumHs()<1:
        raise TopologyError('Amide bond requires a neutral free N with H.')


def _validate_acid(mol, cidx, oidx):
    from rdkit import Chem
    c=mol.GetAtomWithIdx(cidx);o=mol.GetAtomWithIdx(oidx)
    bond=mol.GetBondBetweenAtoms(cidx,oidx)
    if c.GetSymbol()!='C' or o.GetSymbol()!='O' or o.GetDegree()!=1 or o.GetTotalNumHs()!=1 or bond is None or bond.GetBondType()!=Chem.BondType.SINGLE:
        raise TopologyError('Amide bond requires a free carboxylic acid OH.')
    if not any(b.GetBondType()==Chem.BondType.DOUBLE and b.GetOtherAtom(c).GetSymbol()=='O' for b in c.GetBonds()):
        raise TopologyError('Amide carbonyl mapping is invalid.')


def _apply_step(mol, operation):
    from rdkit import Chem
    if not isinstance(operation,dict) or operation.get('type') not in _ALLOWED:
        raise TopologyError('Reaction type unsupported: provide explicit, validated chemistry.')
    kind=operation['type']
    required = _STEP_FIELDS[kind]
    _strict_keys(operation, required | {'type'}, f'Reaction {kind}')
    missing = required - set(operation)
    if missing:
        raise TopologyError(f'Reaction {kind}: missing atom-map references: {sorted(missing)}.')
    def index(name):return _idx(mol,operation.get(name))
    edit=Chem.RWMol(mol)
    removed=[]; byproduct=''
    reagent_halogen=None
    if kind=='amide':
        n,c,o=index('amine'),index('carboxyl'),index('leaving_oxygen')
        if len({n,c,o})!=3:raise TopologyError('Amide sites must be distinct.')
        _validate_amine(mol,mol.GetAtomWithIdx(n));_validate_acid(mol,c,o)
        edit.AddBond(n,c,Chem.BondType.SINGLE);removed=[o];byproduct='H2O'
        n_atom=edit.GetAtomWithIdx(n)
        if n_atom.GetNumExplicitHs():n_atom.SetNumExplicitHs(n_atom.GetNumExplicitHs()-1)
    elif kind=='disulfide':
        a,b=index('a'),index('b')
        if a==b:raise TopologyError('Distinct thiols required.')
        if any(mol.GetAtomWithIdx(i).GetSymbol()!='S' or mol.GetAtomWithIdx(i).GetTotalNumHs()!=1 or mol.GetAtomWithIdx(i).GetFormalCharge()!=0
               for i in (a,b)):
            raise TopologyError('Disulfide requires two unprotected, neutral thiol-SH atoms.')
        edit.AddBond(a,b,Chem.BondType.SINGLE);byproduct='2H'
        for site in (a,b):
            atom=edit.GetAtomWithIdx(site)
            if atom.GetNumExplicitHs():atom.SetNumExplicitHs(atom.GetNumExplicitHs()-1)
    elif kind=='thioether_substitution':
        s,c,leaving=index('sulfur'),index('carbon'),index('leaving')
        sulfur=mol.GetAtomWithIdx(s);halogen=mol.GetAtomWithIdx(leaving)
        if len({s,c,leaving})!=3 or sulfur.GetSymbol()!='S' or sulfur.GetTotalNumHs()!=1:
            raise TopologyError('Substitution requires a free thiol.')
        if halogen.GetSymbol() not in ('Cl','Br','I') or halogen.GetDegree()!=1 or not mol.GetBondBetweenAtoms(c,leaving):
            raise TopologyError('Substitution requires explicitly mapped alkyl halide leaving group.')
        carbon=mol.GetAtomWithIdx(c)
        if carbon.GetSymbol()!='C' or carbon.GetIsAromatic() or carbon.GetHybridization()!=Chem.HybridizationType.SP3:
            raise TopologyError('Substitution accepts only an aliphatic sp3 carbon; no aromatic/SNAr inference.')
        reagent_halogen=halogen.GetSymbol()
        edit.AddBond(s,c,Chem.BondType.SINGLE);removed=[leaving];byproduct='HX'
        atom=edit.GetAtomWithIdx(s)
        if atom.GetNumExplicitHs():atom.SetNumExplicitHs(atom.GetNumExplicitHs()-1)
    elif kind=='thiol_michael':
        s,c1,c2=index('sulfur'),index('alkene_attacked'),index('alkene_other')
        if len({s,c1,c2})!=3:raise TopologyError('Distinct thiol-ene sites are needed.')
        sulfur=mol.GetAtomWithIdx(s)
        bond=mol.GetBondBetweenAtoms(c1,c2)
        if sulfur.GetSymbol()!='S' or sulfur.GetTotalNumHs()!=1 or bond is None or bond.GetBondType()!=Chem.BondType.DOUBLE:
            raise TopologyError('Thiol-Michael requires explicit SH and carbon-carbon double bond.')
        if any(mol.GetAtomWithIdx(i).GetSymbol()!='C' or mol.GetAtomWithIdx(i).GetIsAromatic() for i in (c1,c2)):
            raise TopologyError('Michael addition must target an aliphatic alkene.')
        # Require a conjugated acceptor; no arbitrary alkene additions.
        activated = any(
            neigh.GetSymbol() == 'C' and any(
                b.GetBondType()==Chem.BondType.DOUBLE and b.GetOtherAtom(neigh).GetSymbol()=='O'
                for b in neigh.GetBonds())
            for site in (c1,c2) for neigh in mol.GetAtomWithIdx(site).GetNeighbors()
            if neigh.GetIdx() not in (c1,c2))
        if not activated:
            raise TopologyError('Thiol-Michael requires conjugation to a carbonyl acceptor; ordinary alkene withheld.')
        edit.RemoveBond(c1,c2);edit.AddBond(c1,c2,Chem.BondType.SINGLE);edit.AddBond(s,c1,Chem.BondType.SINGLE)
        atom=edit.GetAtomWithIdx(s)
        if atom.GetNumExplicitHs():atom.SetNumExplicitHs(atom.GetNumExplicitHs()-1)
        other=edit.GetAtomWithIdx(c2)
        if other.GetNumExplicitHs():other.SetNumExplicitHs(other.GetNumExplicitHs()+1)
    elif kind=='cuaac_1_4':
        # Explicit 1,4-regioisomer; N(alpha azide)-N(beta)-N(terminal) and
        # C(terminal)-C(inner) form 1,2,3-triazole; NO catalyst prediction.
        na,nb,nc,ct,ci=(index(name) for name in
            ('azide_alpha','azide_central','azide_terminal','alkyne_terminal','alkyne_inner'))
        if len({na,nb,nc,ct,ci})!=5:
            raise TopologyError('CuAAC must map five unique atoms.')
        if (any(mol.GetAtomWithIdx(x).GetSymbol()!='N' for x in (na,nb,nc)) or
            any(mol.GetAtomWithIdx(x).GetSymbol()!='C' for x in (ct,ci))):
            raise TopologyError('CuAAC expects three azide nitrogen atoms and two alkyne carbons.')
        x=mol.GetBondBetweenAtoms(na,nb);y=mol.GetBondBetweenAtoms(nb,nc);z=mol.GetBondBetweenAtoms(ct,ci)
        if not (x and y and z and x.GetBondType()==Chem.BondType.DOUBLE and
                y.GetBondType()==Chem.BondType.DOUBLE and z.GetBondType()==Chem.BondType.TRIPLE):
            raise TopologyError('CuAAC requires R-N=N+=N- and terminal C#C.')
        if (mol.GetAtomWithIdx(nb).GetFormalCharge()!=1 or mol.GetAtomWithIdx(nc).GetFormalCharge()!=-1
                or mol.GetAtomWithIdx(ct).GetTotalNumHs()!=1
                or mol.GetAtomWithIdx(ci).GetTotalNumHs()!=0):
            raise TopologyError('CuAAC requires mapped organic azide and terminal alkyne with validated charges.')
        edit.GetBondBetweenAtoms(na,nb).SetBondType(Chem.BondType.SINGLE)
        edit.GetBondBetweenAtoms(nb,nc).SetBondType(Chem.BondType.DOUBLE)
        edit.GetBondBetweenAtoms(ct,ci).SetBondType(Chem.BondType.DOUBLE)
        edit.AddBond(nc,ct,Chem.BondType.SINGLE)
        edit.AddBond(ci,na,Chem.BondType.SINGLE)
        edit.GetAtomWithIdx(nb).SetFormalCharge(0)
        edit.GetAtomWithIdx(nc).SetFormalCharge(0)
        byproduct='none'
    else: # rcm, two terminal carbon-carbon double bonds -> internal double bond + ethylene
        a,b,ta,tb=index('alkene_1'),index('alkene_2'),index('terminal_1'),index('terminal_2')
        if len({a,b,ta,tb})!=4:raise TopologyError('RCM requires four distinct alkene atoms.')
        for inner,terminal in ((a,ta),(b,tb)):
            x=mol.GetAtomWithIdx(inner);t=mol.GetAtomWithIdx(terminal)
            bond=mol.GetBondBetweenAtoms(inner,terminal)
            if x.GetSymbol()!='C' or t.GetSymbol()!='C' or t.GetDegree()!=1 or t.GetTotalNumHs()!=2 or bond is None or bond.GetBondType()!=Chem.BondType.DOUBLE:
                raise TopologyError('RCM requires explicit terminal CH2=CH– vinyl sites.')
        edit.AddBond(a,b,Chem.BondType.DOUBLE);removed=[ta,tb];byproduct='C2H4'
    for i in sorted(removed,reverse=True):edit.RemoveAtom(i)
    product=edit.GetMol()
    Chem.SanitizeMol(product)
    if product.GetNumAtoms()>MAX_ATOMS:raise TopologyError('Excessively large molecular graph.')
    # Verify each reaction's molecular mass balance independently of the SMILES edit.
    # A model that sanitizes is not automatically a chemically correct transformation.
    from rdkit.Chem import rdMolDescriptors
    loss = rdMolDescriptors.CalcExactMolWt(mol) - rdMolDescriptors.CalcExactMolWt(product)
    expected_formula = {'H2O': 'O', '2H': '[H][H]', 'C2H4': 'C=C',
                        'HX': '[H]' + reagent_halogen if reagent_halogen else None,
                        'none': None}.get(byproduct)
    expected_loss = (rdMolDescriptors.CalcExactMolWt(Chem.MolFromSmiles(expected_formula))
                     if expected_formula else 0.0)
    if abs(loss-expected_loss) > 0.003:
        raise TopologyError(f'Reaction {kind}: atom/mass balance mismatch; product withheld.')
    return product,byproduct


def calculate_atomic_topology(document: dict[str,Any]) -> dict[str,Any]:
    """Fail closed. Every structural inference requires explicit monomers and mapped sites.

    Expected: {"monomers":[{"name":"...","smiles":"..."}, ...],
               "steps":[{"type":"amide",...}, ...], "head_to_tail":bool}.
    The backbone is joined from the carboxyl of monomer i to N of monomer i+1.
    A step can add a branch/crosslink or other defined connection after assembly.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors,rdMolDescriptors
    except ImportError:
        return {'status':'OPTIONAL_RDKIT_NOT_INSTALLED','reason':'RDKit required.'}
    try:
        _strict_keys(document, {'monomers', 'chains', 'steps', 'head_to_tail'}, 'Topology')
        if 'monomers' in document and 'chains' in document:
            raise TopologyError('Use either monomers or chains, not both.')
        if 'head_to_tail' in document and type(document['head_to_tail']) is not bool:
            raise TopologyError('head_to_tail must be a JSON boolean.')
        single_chain = document.get('chains') is None
        if single_chain:
            raw_chains = [{'monomers':document.get('monomers')}]
        else:
            raw_chains = document.get('chains')
        steps=document.get('steps',[])
        if (not isinstance(raw_chains,list) or not 1<=len(raw_chains)<=16
                or any(not isinstance(c,dict) or not isinstance(c.get('monomers'),list) or
                       not c['monomers'] for c in raw_chains)):
            raise TopologyError('1–16 explicit monomer chains are required.')
        for chain in raw_chains:
            _strict_keys(chain, {'monomers'}, 'Chain')
        total=sum(len(c['monomers']) for c in raw_chains)
        if total>MAX_MONOMERS:
            raise TopologyError('Maximum 128 total monomers.')
        if not isinstance(steps,list) or len(steps)>MAX_STEPS:
            raise TopologyError('Maximum 32 explicit bond edits.')
        # Build chains separately; no accidental peptide bond across arm boundaries.
        mol=None;stage=[];position=0;chain_endpoints=[]
        for chain in raw_chains:
            first=position+1
            for j,row in enumerate(chain['monomers']):
                position+=1
                monomer=_read_monomer(row,position)
                mol=monomer if mol is None else Chem.CombineMols(mol,monomer)
                if mol.GetNumAtoms()>MAX_ATOMS:
                    raise TopologyError('Excessively large molecular graph.')
                if j:
                    mol,_=_apply_step(mol,{'type':'amide','amine':f'{position}:1',
                              'carboxyl':f'{position-1}:2','leaving_oxygen':f'{position-1}:3'})
                stage.append({'stage':f'chain_{len(chain_endpoints)+1}_monomer_{j+1}',
                              'formula':rdMolDescriptors.CalcMolFormula(mol),
                              'average_mw':round(Descriptors.MolWt(mol),5),
                              'exact_mass':round(rdMolDescriptors.CalcExactMolWt(mol),6),
                              'connected_components':len(Chem.GetMolFrags(mol)),
                              'mass_basis':'total assembled monomer(s), no resin'})
            chain_endpoints.append((first,position))
        if document.get('head_to_tail') and len(chain_endpoints)!=1:
            raise TopologyError('Multi-chain head-to-tail requires explicitly mapped amide steps.')
        prior=Descriptors.MolWt(mol)
        exact_before=rdMolDescriptors.CalcExactMolWt(mol)
        applied=[]
        for index,operation in enumerate(steps,1):
            mol,byproduct=_apply_step(mol,operation)
            applied.append({'step':index,'reaction':operation['type'],'byproduct_class':byproduct,
                            'formula':rdMolDescriptors.CalcMolFormula(mol),'average_mw':round(Descriptors.MolWt(mol),5),
                            'exact_mass':round(rdMolDescriptors.CalcExactMolWt(mol),6)})
        if document.get('head_to_tail'):
            mol,byproduct=_apply_step(mol,{'type':'amide','amine':'1:1','carboxyl':f'{position}:2',
                                             'leaving_oxygen':f'{position}:3'})
            applied.append({'step':len(applied)+1,'reaction':'head_to_tail','byproduct_class':byproduct,
                            'formula':rdMolDescriptors.CalcMolFormula(mol),'average_mw':round(Descriptors.MolWt(mol),5),
                            'exact_mass':round(rdMolDescriptors.CalcExactMolWt(mol),6)})
        if len(Chem.GetMolFrags(mol))!=1:
            raise TopologyError('Final product graph is disconnected: reactants must be linked explicitly.')
        from .ms_ions_v9 import theoretical_ms_ions
        exact=rdMolDescriptors.CalcExactMolWt(mol)
        review_id=hashlib.sha256(json.dumps(document,sort_keys=True,ensure_ascii=False,
                       separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
        return {'status':'ATOM_MAPPED_GRAPH_PASS','structure_review_sha256':review_id,'mass_type':'neutral_molecule','input_monomers':total,'chain_count':len(chain_endpoints),
                'initial_backbone_average_mw':round(prior,5),'initial_backbone_exact_mass':round(exact_before,6),
                'formula':rdMolDescriptors.CalcMolFormula(mol),
                'average_mw':round(Descriptors.MolWt(mol),5),'exact_mass':round(exact,6),
                'product_smiles':Chem.MolToSmiles(mol,isomericSmiles=True),
                'reaction_steps':applied,'assembly_stages':stage,
                'theoretical_ms_ions':theoretical_ms_ions(exact),
                'warnings':['Input is operator-supplied molecular structure, NOT proof of chemical identity or experimental feasibility.',
                            'No automated reaction selection or validation of stereo retention, yields, kinetics or safety.']}
    except (ValueError,TypeError,KeyError,IndexError,RuntimeError) as error:
        return {'status':'WITHHELD_INVALID_ATOMIC_TOPOLOGY','reason':str(error),
                'note':'No mass is released if mapped chemistry fails validation.'}


def load_atomic_topology_json(path, *, max_bytes=200_000):
    """Read only local bounded JSON, no arbitrary code execution."""
    from pathlib import Path
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size > max_bytes:
        raise TopologyError('Topology file is missing, a symlink, or exceeds the size limit.')
    from .strict_json_v9 import loads_scientific_json
    data=loads_scientific_json(p.read_text(encoding='utf-8'), max_bytes=max_bytes)
    if not isinstance(data,dict):raise TopologyError('Expected a JSON object.')
    return data
