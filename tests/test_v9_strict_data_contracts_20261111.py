"""Actual V9 source contract: no ambiguous scientific input is silently accepted."""
import csv
import json
import pytest

from spps_planner.strict_json_v9 import loads_scientific_json, ScientificJSONError
from spps_planner.atomic_topology_v9 import calculate_atomic_topology, load_atomic_topology_json, TopologyError
from spps_planner.monomer_catalog_v9 import import_monomer_catalog, resolve_catalog_tokens
from spps_planner.grounded_literature_ai_v9 import request_grounded_literature_review, LiteratureReviewError

ALA='[NH2:1][C@@H](C)[C:2](=O)[OH:3]'
AIB='[NH2:1]C(C)(C)[C:2](=O)[OH:3]'

@pytest.mark.parametrize('text', [
    '{"head_to_tail":true,"head_to_tail":false}',
    '{"monomers":[{"smiles":"x","smiles":"y"}]}',
    '{"monomers":NaN}',
    '{"monomers":Infinity}',
])
def test_strict_json_blocks_silent_settings_or_invalid_numbers(text):
    with pytest.raises(ScientificJSONError):
        loads_scientific_json(text)


def test_good_scientific_json_is_parsed_without_code_execution():
    assert loads_scientific_json('{"head_to_tail":true,"monomers":[]}')['head_to_tail'] is True


def test_topology_file_rejects_duplicate_reaction_key(tmp_path):
    file=tmp_path/'structure.json'
    file.write_text('{"monomers":[{"smiles":"'+ALA+'"}],"head_to_tail":true,"head_to_tail":false}')
    with pytest.raises(ScientificJSONError):
        load_atomic_topology_json(file)


def test_catalog_rejects_duplicate_headers(tmp_path):
    file=tmp_path/'catalog.csv'
    file.write_text('token,smiles,TOKEN\nAib,"'+AIB+'",Ala\n')
    with pytest.raises(TopologyError,match='unique'):
        import_monomer_catalog(file)


def test_catalog_rejects_wrong_reported_mw_and_accepts_correct(tmp_path):
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    right=Descriptors.MolWt(Chem.MolFromSmiles(AIB))
    file=tmp_path/'catalog.csv'
    with file.open('w', newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['token','smiles','reported_mw','source'])
        writer.writeheader()
        writer.writerow({'token':'Aib','smiles':AIB,'reported_mw':right,'source':'checked'})
        writer.writerow({'token':'Wrong','smiles':ALA,'reported_mw':right+150,'source':'different chemistry'})
    result=import_monomer_catalog(file)
    assert result['accepted_count']==1 and result['rejected_count']==1
    assert result['accepted'][0]['reported_mw']==pytest.approx(right)
    assert result['accepted'][0]['reported_mw_delta']==pytest.approx(0,abs=1e-6)


def test_catalog_rejects_both_mw_columns_if_inconsistent(tmp_path):
    file=tmp_path/'catalog.json'
    file.write_text(json.dumps({'monomers':[{'token':'Aib','smiles':AIB,'reported_mw':100.,'mw':200.}]}))
    result=import_monomer_catalog(file)
    assert result['accepted_count']==0 and result['rejected_count']==1


def test_token_and_explicit_structure_must_match():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        path=Path(d)/'monomers.json'
        path.write_text(json.dumps([{'token':'Aib','smiles':AIB}]))
        registry={m['token']:m for m in import_monomer_catalog(path)['accepted']}
    assert calculate_atomic_topology(resolve_catalog_tokens({'monomers':[{'token':'Aib'}]},registry))['status']=='ATOM_MAPPED_GRAPH_PASS'
    with pytest.raises(TopologyError,match='disagrees'):
        resolve_catalog_tokens({'monomers':[{'token':'Aib','smiles':ALA}]},registry)
    assert calculate_atomic_topology(resolve_catalog_tokens({'monomers':[{'token':'Aib','smiles':AIB}]},registry))['status']=='ATOM_MAPPED_GRAPH_PASS'


def test_untrusted_catalog_token_must_not_impersonate_registry_key():
    registry={'Wrong':{'token':'Aib','smiles':AIB,'validation':'ATOM_MAPPED_ONLY_OPERATOR_REVIEW_REQUIRED'}}
    with pytest.raises(TopologyError,match='registry key'):
        resolve_catalog_tokens({'monomers':[{'token':'Wrong'}]},registry)


def _packet():
    return {'schema':'spps-v9-cited-excerpts-1','question':'What is cited?',
            'excerpts':[{'id':'E1','page':1,'source_sha256':'a'*64,'excerpt':'This peptide cyclization yielded a protected cyclic product.'}]}


def _reply(findings):
    return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text',
        'text':json.dumps({'summary':'Result','caveats':'Review required','findings':findings})}]}]}


def test_ai_review_rejects_unanchored_summary_with_no_findings():
    with pytest.raises(LiteratureReviewError,match='malformed'):
        request_grounded_literature_review(_packet(),explicit_consent=True,model='demo',api_key='dummy',
                                          transport=lambda *_:_reply([]))


def test_ai_review_rejects_reused_excerpt_ids():
    packet=_packet()
    packet['excerpts'].append(dict(packet['excerpts'][0],excerpt='Conflicting excerpt.'))
    with pytest.raises(LiteratureReviewError,match='Duplicate'):
        request_grounded_literature_review(packet,explicit_consent=True,model='demo',api_key='dummy',
                                          transport=lambda *_: (_ for _ in ()).throw(AssertionError('Must not send')))


def test_ai_review_rejects_malformed_model_output():
    with pytest.raises(LiteratureReviewError,match='malformed'):
        request_grounded_literature_review(_packet(),explicit_consent=True,model='demo',api_key='dummy',
                                          transport=lambda *_:{'status':'completed','output':None})


def test_assembly_stage_mass_ledger_tracks_each_condensation():
    from rdkit import Chem
    from rdkit.Chem import Descriptors
    result=calculate_atomic_topology({'monomers':[{'smiles':ALA},{'smiles':AIB}], 'head_to_tail':True})
    assert result['status']=='ATOM_MAPPED_GRAPH_PASS'
    first,second=result['assembly_stages']
    assert first['average_mw']==pytest.approx(Descriptors.MolWt(Chem.MolFromSmiles(ALA)),abs=0.0001)
    assert second['average_mw']==pytest.approx(first['average_mw']+Descriptors.MolWt(Chem.MolFromSmiles(AIB))-18.01528,abs=0.002)
    assert second['average_mw']-result['average_mw']==pytest.approx(18.01528,abs=.002)
    assert second['connected_components']==1
    assert result['reaction_steps'][-1]['reaction']=='head_to_tail'


@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'),reason='Requires graphical Tk display')
def test_actual_editor_withholds_duplicate_json_keys():
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    from suite_gui.structure_review_panel_v9 import open_atomic_topology_editor
    root=tk.Tk();root.withdraw();added=[]
    try:
        win=open_atomic_topology_editor(root,sequence='A',resin='2-CTC',on_attach=added.append)
        def widgets(node):
            for child in node.winfo_children():
                yield child
                yield from widgets(child)
        editor=next(w for w in widgets(win) if isinstance(w,ScrolledText))
        editor.delete('1.0','end')
        editor.insert('1.0','{"monomers":[{"smiles":"'+ALA+'"}],"head_to_tail":true,"head_to_tail":false}')
        buttons={w.cget('text'):w for w in widgets(win) if isinstance(w,ttk.Button)}
        buttons['Compute atomic graph'].invoke()
        root.update_idletasks()
        status=[w.cget('text') for w in widgets(win) if isinstance(w,ttk.Label)]
        assert any('Withheld' in x for x in status)
        buttons['Attach review to Auto Plan'].invoke()
        assert added==[]
    finally:
        for w in root.winfo_children():w.destroy()
        root.destroy()


def test_cli_replays_custom_monomer_and_outputs_stage_masses(tmp_path):
    from tools.review_custom_topology_v9 import validate_files, main
    catalog=tmp_path/'monomers.csv'
    catalog.write_text('token,smiles\nAib,"'+AIB+'"\n')
    topology=tmp_path/'topology.json'
    topology.write_text(json.dumps({'monomers':[{'token':'Aib'},{'smiles':ALA}], 'head_to_tail':True}))
    review=validate_files(topology,catalog)
    assert review['status']=='ATOM_MAPPED_GRAPH_PASS',review
    assert review['assembly_stages'][0]['average_mw']>0
    assert review['assembly_stages'][1]['average_mw']>review['assembly_stages'][0]['average_mw']
    assert review['review_scope']=='THEORETICAL_STRUCTURE_ONLY_NOT_AN_APPROVED_SYNTHESIS'
    assert len(review['catalog_sha256'])==64
    assert main([str(topology),'--catalog',str(catalog)])==0
    topology.write_text('{"monomers":[],"monomers":[]}')
    assert main([str(topology),'--catalog',str(catalog)])==2


def test_cli_rejects_partial_catalog_without_silent_application(tmp_path):
    from tools.review_custom_topology_v9 import validate_files
    catalog=tmp_path/'monomers.csv'
    catalog.write_text('token,smiles\nAib,"'+AIB+'"\nWrong,invalid\n')
    topology=tmp_path/'topology.json'
    topology.write_text(json.dumps({'monomers':[{'token':'Aib'}]}))
    review=validate_files(topology,catalog)
    assert review['status']=='WITHHELD_CATALOG_REVIEW_REQUIRED'
    assert 'average_mw' not in review


def test_preexisting_atomic_acceptance_matrix_is_preserved(capsys):
    """Custom import CLI must not replace the original seven-case matrix."""
    from tools.validate_atomic_topology_v9 import main as original_matrix
    assert original_matrix([])==0
    report=json.loads(capsys.readouterr().out)
    assert report['version']=='V9.0.0'
    assert report['status']=='PASS' and report['total']>=7
    assert all(case['pass'] for case in report['cases'])
