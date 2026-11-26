"""V9 atomic operator-specified graph tests; chemistry assertions, not reaction feasibility."""
import pytest
from rdkit import Chem
from rdkit.Chem import Descriptors
from spps_planner.atomic_topology_v9 import calculate_atomic_topology as calc

ALA='[NH2:1][C@@H](C)[C:2](=O)[OH:3]'
NLE='[NH2:1][C@@H](CCCC)[C:2](=O)[OH:3]'
AIB='[NH2:1]C(C)(C)[C:2](=O)[OH:3]'
CYS='[NH2:1][C@@H](C[SH:10])[C:2](=O)[OH:3]'
LYS='[NH2:1][C@@H](CCCC[NH2:10])[C:2](=O)[OH:3]'
HALO='[NH2:1][C@@H](C[CH2:11][Br:12])[C:2](=O)[OH:3]'
AZIDE='[NH2:1][C@@H](C[N:10]=[N+:11]=[N-:12])[C:2](=O)[OH:3]'
ALKYNE='[NH2:1][C@@H](C[C:14]#[CH:13])[C:2](=O)[OH:3]'
VINYL='[NH2:1][C@@H](C[CH:10]=[CH2:11])[C:2](=O)[OH:3]'
MICHAEL='[NH2:1][C@@H](C[CH:11]=[CH:12]C(=O)N)[C:2](=O)[OH:3]'

def doc(*seq, steps=(), chains=False, ring=False):
    if chains:
        return {'chains':[{'monomers':[{'smiles':s} for s in chain]} for chain in seq],
                'steps':list(steps),'head_to_tail':ring}
    return {'monomers':[{'smiles':s} for s in seq], 'steps':list(steps),'head_to_tail':ring}

def ok(payload):
    result=calc(payload)
    assert result['status']=='ATOM_MAPPED_GRAPH_PASS',result
    assert Chem.MolFromSmiles(result['product_smiles']) is not None
    assert result['theoretical_ms_ions']['positive_ion_candidates']
    return result

@pytest.mark.parametrize('monomer',[ALA,NLE,AIB])
def test_noncanonical_uses_actual_smiles_not_guessed_delta(monomer):
    result=ok(doc(monomer))
    assert result['average_mw']==pytest.approx(Descriptors.MolWt(Chem.MolFromSmiles(monomer)),abs=0.001)


def test_mixed_nle_aib_linear_and_headtail_mass():
    linear=ok(doc(ALA,NLE,AIB))
    cyclic=ok(doc(ALA,NLE,AIB,ring=True))
    assert linear['average_mw']-cyclic['average_mw']==pytest.approx(18.0153,abs=0.002)


def test_multi_chain_one_branch_one_macrocycle():
    mol=ok(doc([ALA,LYS,ALA],[ALA],chains=True,steps=[
        {'type':'amide','amine':'2:10','carboxyl':'4:2','leaving_oxygen':'4:3'},
        {'type':'amide','amine':'1:1','carboxyl':'3:2','leaving_oxygen':'3:3'}]))
    assert mol['chain_count']==2
    assert len(mol['reaction_steps'])==2


def test_cuaac_explicit_triazole_conserves_all_atoms():
    payload=doc(AZIDE,ALKYNE,steps=[{'type':'cuaac_1_4','azide_alpha':'1:10','azide_central':'1:11',
         'azide_terminal':'1:12','alkyne_terminal':'2:13','alkyne_inner':'2:14'}])
    original=ok(doc(AZIDE,ALKYNE));closed=ok(payload)
    assert original['formula']==closed['formula']
    assert 'nn' in closed['product_smiles']


def test_disulfide_loses_two_hydrogens():
    a=ok(doc(CYS,CYS))
    b=ok(doc(CYS,CYS,steps=[{'type':'disulfide','a':'1:10','b':'2:10'}]))
    assert a['average_mw']-b['average_mw']==pytest.approx(2.01588,abs=0.002)


def test_alkyl_halide_thioether_releases_hbr():
    a=ok(doc(CYS,HALO))
    b=ok(doc(CYS,HALO,steps=[{'type':'thioether_substitution','sulfur':'1:10',
                         'carbon':'2:11','leaving':'2:12'}]))
    assert a['average_mw']-b['average_mw']==pytest.approx(80.912,abs=0.02)


def test_rcm_two_alkenes_release_ethylene():
    a=ok(doc(VINYL,VINYL))
    b=ok(doc(VINYL,VINYL,steps=[{'type':'rcm','alkene_1':'1:10','terminal_1':'1:11',
                         'alkene_2':'2:10','terminal_2':'2:11'}]))
    assert a['average_mw']-b['average_mw']==pytest.approx(28.054,abs=0.005)


def test_thiol_michael_explicit_acceptor_conserves_formula():
    a=ok(doc(CYS,MICHAEL))
    b=ok(doc(CYS,MICHAEL,steps=[{'type':'thiol_michael','sulfur':'1:10',
                            'alkene_attacked':'2:11','alkene_other':'2:12'}]))
    assert a['formula']==b['formula']


@pytest.mark.parametrize('payload',[
 {'monomers':[{'smiles':'NCC(=O)O'}]},
 {'monomers':[{'smiles':'[NH2:1][C@@H](C)[C:2](=O)[OH:3]'}], 'steps':[{'type':'not_supported'}]},
 doc(ALA,ALA,steps=[{'type':'disulfide','a':'1:1','b':'2:1'}]),
 doc(ALA,ALA,steps=[{'type':'amide','amine':'1:1','carboxyl':'2:2','leaving_oxygen':'2:3'},
                   {'type':'amide','amine':'1:1','carboxyl':'2:2','leaving_oxygen':'2:3'}]),
 doc([ALA],[ALA],chains=True),
 doc(ALA,ALA,steps=[{'type':'rcm','alkene_1':'1:1','alkene_2':'2:1','terminal_1':'1:2','terminal_2':'2:2'}]),
])
def test_invalid_or_disconnected_chemistry_is_withheld(payload):
    result=calc(payload)
    assert result['status']=='WITHHELD_INVALID_ATOMIC_TOPOLOGY',result
    assert 'average_mw' not in result
