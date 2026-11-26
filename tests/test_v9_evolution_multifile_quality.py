"""V9 evolution: reviewed multi-file import, audit, rollback, guarded training."""
from __future__ import annotations
from types import SimpleNamespace
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from suite_gui.ai_excel_core_v9 import (
    preview_file, normalize_preview, combine_reviewed_tables,
    append_reviewed_dataset, audit_reviewed_data,
    save_reviewed_dataset, load_reviewed_dataset, restore_last_good_dataset,
    train_local_advisor,
)


def test_batch_union_provenance_and_operator_review(tmp_path):
    first=tmp_path/'a.csv'; second=tmp_path/'b.csv'
    first.write_text('Sequence,Yield %,Run ID\nACD,61,A-1\n',encoding='utf-8')
    second.write_text('서열,순도(%),실험번호\nGGEP,98,B-1\n',encoding='utf-8-sig')
    a,ra=normalize_preview(preview_file(first)); b,rb=normalize_preview(preview_file(second))
    joined,audit=combine_reviewed_tables(a,b)
    assert len(joined)==2
    assert audit['duplicate_run_ids']==0
    assert joined['actual_yield_percent'].notna().sum()==1
    assert joined['actual_purity_percent'].notna().sum()==1
    saved=save_reviewed_dataset(a,ra,'digest_a',tmp_path/'profile')
    appended=append_reviewed_dataset(b,rb,'digest_b',tmp_path/'profile')
    rows,meta=load_reviewed_dataset(tmp_path/'profile')
    assert len(rows)==2
    assert meta['import_report']['prior_rows']==1
    assert meta['import_report']['quality_audit']['total_rows']==2
    assert (tmp_path/'profile'/'ai_excel_reviewed_v9.json.bak').exists()
    assert appended['sha256']!=saved['sha256']


def test_append_keeps_replicates_but_blocks_training_on_repeated_run_ids(tmp_path):
    a=pd.DataFrame([{'sequence':'ACD','actual_yield_percent':61.,'run_id':'RUN-9'}])
    b=pd.DataFrame([{'sequence':'ACD','actual_yield_percent':62.,'run_id':'run-9'}])
    joined,audit=combine_reviewed_tables(a,b)
    assert len(joined)==2
    assert audit['duplicate_run_ids']==1
    assert audit['conflicting_run_ids']==1
    assert audit['training_blocked'] is True
    with pytest.raises(ValueError,match='Data quality'):
        train_local_advisor(joined,'actual_yield_percent',tmp_path/'models','test_sha')


def test_identical_replicates_flagged_not_dropped():
    a=pd.DataFrame([{'sequence':'AAAA','actual_yield_percent':75.0}])
    merged,audit=combine_reviewed_tables(a,a)
    assert len(merged)==2
    assert audit['exact_duplicate_rows']==1
    assert audit['training_blocked']


def test_rollback_and_corruption_guard(tmp_path):
    root=tmp_path/'local'
    first=pd.DataFrame([{'sequence':'ACD','actual_yield_percent':75.0}])
    second=pd.DataFrame([{'sequence':'GGEP','actual_yield_percent':78.0}])
    save_reviewed_dataset(first,{},'one',root)
    save_reviewed_dataset(second,{},'two',root)
    result=restore_last_good_dataset(root)
    restored,_=load_reviewed_dataset(root)
    assert result['restored_rows']==1
    assert restored['sequence'].tolist()==['ACD']
    bak=root/'ai_excel_reviewed_v9.json.bak'
    payload=json.loads(bak.read_text(encoding='utf-8'))
    payload['records'][0]['sequence']='TAMPERED'
    bak.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(ValueError,match='integrity'):
        restore_last_good_dataset(root)


def test_append_corrupt_old_dataset_does_not_overwrite(tmp_path):
    root=tmp_path/'local'
    save_reviewed_dataset(pd.DataFrame([{'sequence':'AAA'}]),{},'x',root)
    original=root/'ai_excel_reviewed_v9.json'
    original.write_text('{invalid',encoding='utf-8')
    with pytest.raises(ValueError,match='read'):
        append_reviewed_dataset(pd.DataFrame([{'sequence':'GGG'}]),{},'x',root)
    assert original.read_text()=='{invalid'


def test_no_silent_topology_inference_from_external_data():
    rows=pd.DataFrame([{'sequence':'dS-dV-dS','actual_yield_percent':65.0}])
    _,report=combine_reviewed_tables(rows)
    assert 'product_path' not in rows.columns
    assert report['training_blocked'] is False
    assert report['target_quality']['actual_yield_percent']['minimum_rows_met'] is False


@pytest.mark.skipif(not os.environ.get('DISPLAY') and os.name!='nt',reason='Tk requires a display')
def test_multifile_dialog_actual_button_workflow(tmp_path,monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    from suite_gui.ai_excel_dialog_v9 import open_excel_ai_dialog
    from tkinter import filedialog, messagebox
    first=tmp_path/'first.csv';second=tmp_path/'second.csv'
    first.write_text('Sequence,Yield %,Run ID\nAAAAA,55.0,A-1\n',encoding='utf-8')
    second.write_text('서열,수득률(%),실험번호\nGGGGG,60.0,B-1\n',encoding='utf-8-sig')
    monkeypatch.setattr(filedialog,'askopenfilenames',lambda **kw:(str(first),str(second)))
    monkeypatch.setattr(messagebox,'askyesno',lambda *args,**kw:True)
    errors=[]
    monkeypatch.setattr(messagebox,'showerror',lambda title,detail,**kw:errors.append((title,detail)))
    root=tk.Tk();root.withdraw()
    try:
        gui=SimpleNamespace(ai_excel_data_dir=tmp_path/'profile',ai_excel_models_dir=tmp_path/'models')
        dialog=open_excel_ai_dialog(gui,parent=root)
        def widgets(widget):
            for child in widget.winfo_children():
                yield child
                yield from widgets(child)
        def click(contains):
            for w in widgets(dialog):
                if isinstance(w,ttk.Button) and contains in w.cget('text'):
                    w.invoke();root.update_idletasks();return
            raise AssertionError(f'Button not found: {contains}')
        def agree():
            for w in widgets(dialog):
                if isinstance(w,ttk.Checkbutton) and 'I reviewed the column' in w.cget('text'):
                    w.invoke();return
            raise AssertionError('Consent checkbox not found')
        # Workbook reads and atomic save run off the Tk thread in V9.
        # Pump the actual Tk event loop until each single-flight job completes.
        import time
        def await_ready(timeout=8):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                root.update()
                buttons=[w for w in widgets(dialog) if isinstance(w,ttk.Button)
                         and '2. Check & clean' in w.cget('text')]
                if buttons and 'disabled' not in buttons[0].state():return
                time.sleep(.01)
            raise AssertionError('Background Excel import stayed busy.')
        click('Choose Excel(s)');await_ready()
        click('Check & clean');await_ready();agree();click('Stage reviewed file');await_ready()
        click('Check & clean');await_ready();agree();click('Stage reviewed file')
        click('Save combined data')
        await_ready()
        assert not errors,errors
        frame,meta=load_reviewed_dataset(tmp_path/'profile')
        assert len(frame)==2
        assert meta['import_report']['source_count']==2
        assert set(frame['sequence'])=={'AAAAA','GGGGG'}
        dialog.destroy()
    finally:
        root.destroy()


def test_similar_runs_uses_residue_order_not_only_aa_counts():
    from suite_gui.ai_excel_core_v9 import similar_runs
    frame=pd.DataFrame([
        {'sequence':'VVVVV','actual_yield_percent':71.,'resin':'CTC','chemistry':'DIC/HOBt'},
        {'sequence':'AAAAT','actual_yield_percent':69.,'resin':'CTC','chemistry':'DIC/HOBt'},
    ])
    found=similar_runs(frame,{'sequence':'AAAAA','resin':'CTC','chemistry':'DIC/HOBt'})
    assert found[0]['sequence']=='AAAAT'
    assert found[0]['residue_edits']==1
    assert found[1]['residue_edits']==5
    assert not found[0]['exact_residue_identity']
    assert found[0]['conditions_match']['resin']


@pytest.mark.skipif(not os.environ.get('DISPLAY') and os.name!='nt',reason='Tk requires a display')
def test_dialog_actions_remain_visible_when_resized_narrow_and_short(tmp_path):
    import tkinter as tk
    from tkinter import ttk
    from suite_gui.ai_excel_dialog_v9 import open_excel_ai_dialog
    root=tk.Tk()
    try:
        dialog=open_excel_ai_dialog(SimpleNamespace(ai_excel_data_dir=tmp_path),parent=root)
        dialog.geometry('830x620')
        root.update()
        def widgets(widget):
            for child in widget.winfo_children():
                yield child;yield from widgets(child)
        # V9 intentionally keeps manual training actions inside the collapsed
        # Advanced section; old tests requiring them visible at startup are
        # incompatible with the operator-approved UI.  Test reachability.
        advanced={'3. Save combined data','4. Train local AI','Audit data quality',
                  'Restore previous dataset','Stage reviewed file / Next'}
        controls={w.cget('text'):w for w in widgets(dialog) if isinstance(w,ttk.Button)}
        assert advanced.issubset(controls)
        assert 'Close' in controls and controls['Close'].winfo_viewable()
        assert all(not controls[text].winfo_viewable() for text in advanced)
        toggles=[w for w in widgets(dialog) if isinstance(w,ttk.Checkbutton)
                 and 'Advanced' in w.cget('text')]
        assert toggles
        toggles[0].invoke();root.update()
        assert all(controls[text].winfo_viewable() for text in advanced)
        canvases=[w for w in widgets(dialog) if isinstance(w,tk.Canvas)]
        assert canvases and canvases[0].yview()[1] < 1.0
        # The footer remains inside the resized window while Advanced content
        # is scrollable, not forced into the fixed action bar.
        close=controls['Close']
        assert close.winfo_rootx()-dialog.winfo_rootx()>=0
        assert close.winfo_rooty()-dialog.winfo_rooty()+close.winfo_height()<=620
        dialog.destroy()
    finally:
        root.destroy()
