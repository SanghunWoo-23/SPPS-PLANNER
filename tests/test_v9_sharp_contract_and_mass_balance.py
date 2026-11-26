"""Strict chemistry contract and provenance protections for V9.0.0."""
from copy import deepcopy
import pytest
from spps_planner.atomic_topology_v9 import calculate_atomic_topology as calculate

ALA = '[NH2:1][C@@H](C)[C:2](=O)[OH:3]'
CYS = '[NH2:1][C@@H](C[SH:10])[C:2](=O)[OH:3]'


def linear(*monomers, **kwargs):
    return {'monomers':[{'name':'amino acid', 'smiles':a} for a in monomers], **kwargs}


@pytest.mark.parametrize('payload', [
    linear(ALA, head_to_tial=True),        # critical spelling typo must not silently become linear
    linear(ALA, head_to_tail='false'),     # no truthy strings or integer stand-ins
    linear(ALA, head_to_tail=1),
    {'monomers':[{'smiles':ALA}], 'chains':[{'monomers':[{'smiles':ALA}]}]},
    {'chains':[{'monomers':[{'smiles':ALA}], 'typo':1}]},
    {'monomers':[{'smiles':ALA, 'wrong_group':'Boc'}]},
    linear(ALA,ALA,steps=[{'type':'amide','amine':'1:1','carboxyl':'2:2','leaving_oxygen':'2:3','surprise':1}]),
    linear(ALA,ALA,steps=[{'type':'amide','amine':'1:1','carboxyl':'2:2'}]),
    linear(CYS,CYS,steps=[{'type':'disulfide','a':'1:10','b':'2:10','c':'2:1'}]),
])
def test_unknown_or_ambiguous_structure_fails_closed(payload):
    result=calculate(payload)
    assert result['status']=='WITHHELD_INVALID_ATOMIC_TOPOLOGY'
    assert 'average_mw' not in result


def test_structural_review_hash_reproducible_and_sensitive_to_change():
    input_doc=linear(ALA,ALA,head_to_tail=True)
    original=calculate(input_doc)
    assert original['status']=='ATOM_MAPPED_GRAPH_PASS',original
    assert calculate(deepcopy(input_doc))['structure_review_sha256']==original['structure_review_sha256']
    another=linear(ALA,ALA)
    assert calculate(another)['structure_review_sha256']!=original['structure_review_sha256']
    assert original['average_mw']<calculate(another)['average_mw']


def test_all_chemically_distinct_step_masses_report():
    from rdkit.Chem import rdMolDescriptors
    molecule=linear(CYS,CYS,steps=[{'type':'disulfide','a':'1:10','b':'2:10'}])
    result=calculate(molecule)
    assert result['status']=='ATOM_MAPPED_GRAPH_PASS',result
    assert result['reaction_steps'][0]['byproduct_class']=='2H'
    expected=rdMolDescriptors.CalcExactMolWt(__import__('rdkit').Chem.MolFromSmiles('[H][H]'))
    baseline=calculate(linear(CYS,CYS))
    assert baseline['exact_mass'] - result['exact_mass']==pytest.approx(expected, abs=0.00002)
