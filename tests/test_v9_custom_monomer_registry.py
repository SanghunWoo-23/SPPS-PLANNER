"""Bounded Excel/CSV/JSON monomer review and non-executable topology replay."""
import csv
import json
from pathlib import Path
import pytest
from spps_planner.monomer_catalog_v9 import import_monomer_catalog, resolve_catalog_tokens
from spps_planner.atomic_topology_v9 import calculate_atomic_topology

ALA='[NH2:1][C@@H](C)[C:2](=O)[OH:3]'
AIB='[NH2:1]C(C)(C)[C:2](=O)[OH:3]'


def test_local_json_review_and_explicit_token_resolution(tmp_path):
    p=tmp_path/'library.json';p.write_text(json.dumps({'monomers':[{'token':'Aib','smiles':AIB}]}))
    results=import_monomer_catalog(p)
    assert results['accepted_count']==1 and results['rejected_count']==0
    resolved=resolve_catalog_tokens({'monomers':[{'token':'Aib'},{'smiles':ALA}]},
                                    {item['token']:item for item in results['accepted']})
    assert calculate_atomic_topology(resolved)['status']=='ATOM_MAPPED_GRAPH_PASS'


def test_duplicate_tokens_rejected_without_silent_merge(tmp_path):
    p=tmp_path/'library.csv'
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['token','smiles']);writer.writeheader()
        writer.writerows([{'token':'Aib','smiles':AIB},{'token':'aib','smiles':ALA}])
    result=import_monomer_catalog(p)
    assert result['accepted_count']==1 and result['rejected_count']==1


def test_xlsx_monomers(tmp_path):
    from openpyxl import Workbook
    w=Workbook();s=w.active;s.append(['Token','SMILES','Source'])
    s.append(['Aib',AIB,'example']);p=tmp_path/'input.xlsx';w.save(p)
    result=import_monomer_catalog(p)
    assert result['accepted_count']==1
    assert result['accepted'][0]['source']=='example'


def test_invalid_smiles_rejected(tmp_path):
    p=tmp_path/'bad.json'
    p.write_text(json.dumps([{'token':'Bad','smiles':'whatever'},{'token':'Missing','smiles':ALA[:-4]}]))
    result=import_monomer_catalog(p)
    assert result['accepted_count']==0


def test_checklist_recomputes_custom_graph_and_blocks_stale_or_tampered():
    from suite_gui.checklist_mass_v9 import append_crosslink_structure_review
    from spps_planner.atomic_topology_v9 import calculate_atomic_topology
    schema={'monomers':[{'smiles':ALA},{'smiles':AIB}], 'head_to_tail':True}
    found=calculate_atomic_topology(schema)
    review={'status':'UNAPPROVED_REVIEW_ONLY','sequence':'AAib','resin':'2-CTC',
            'topology':'atom_mapped_custom','schema':schema,'graph':found}
    table=[];append_crosslink_structure_review(table,'AAib','2-CTC',review)
    assert float(table[0]['peptide_mw'])>0
    assert 'NOT an observed' in table[0]['note']
    review['graph']=dict(found,average_mw=found['average_mw']+100)
    table=[];append_crosslink_structure_review(table,'AAib','2-CTC',review)
    assert table[0]['peptide_mw']==''
    table=[];append_crosslink_structure_review(table,'AAA','2-CTC',review)
    assert table[0]['peptide_mw']==''


@pytest.mark.skipif(not __import__('os').environ.get('DISPLAY'),reason='Requires graphical Tk display')
def test_gui_custom_editor_can_compute_and_attach_review():
    import tkinter as tk
    from tkinter import ttk
    from tkinter.scrolledtext import ScrolledText
    from suite_gui.structure_review_panel_v9 import open_atomic_topology_editor
    root=tk.Tk();root.withdraw();records=[]
    try:
        window=open_atomic_topology_editor(root,sequence='AAib',resin='2-CTC',on_attach=records.append)
        def descendants(widget):
            for c in widget.winfo_children():
                yield c
                yield from descendants(c)
        buttons={b.cget('text'):b for b in descendants(window) if isinstance(b,ttk.Button)}
        buttons['Compute atomic graph'].invoke();root.update_idletasks()
        result=[x for x in descendants(window) if isinstance(x,ScrolledText)][1].get('1.0','end')
        assert 'ATOM_MAPPED_GRAPH_PASS' in result
        buttons['Attach review to Auto Plan'].invoke()
        assert not records
        check=next(x for x in descendants(window) if isinstance(x,ttk.Checkbutton))
        check.invoke();buttons['Attach review to Auto Plan'].invoke()
        assert records[0]['topology']=='atom_mapped_custom'
    finally:
        for c in root.winfo_children():c.destroy()
        root.destroy()
