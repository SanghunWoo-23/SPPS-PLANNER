"""Excel-to-ML workflow is opt-in, local and never modifies chemistry defaults."""
from __future__ import annotations
from pathlib import Path
import json
from types import SimpleNamespace
import pandas as pd
import pytest

from suite_gui.ai_excel_core_v9 import (
    preview_file, normalize_preview, save_reviewed_dataset,
    load_reviewed_dataset, train_local_advisor, advise_from_local_data,
    similar_runs, _seq_features,
)


def test_korean_csv_import_and_header_detection(tmp_path):
    path=tmp_path/'runs.csv'
    path.write_text('실험기록,,\n펩타이드서열,수득률(%),순도(%)\ndS-dV-dS,43%,91%\nGGEP,55,98\n,66,99\n',encoding='utf-8-sig')
    p=preview_file(path)
    assert p.header_row==1
    assert p.mapping['sequence']=='펩타이드서열'
    frame,report=normalize_preview(p)
    assert len(frame)==2
    assert frame['actual_yield_percent'].tolist()==[43.0,55.0]
    assert report['excluded_missing_sequence']==1


def test_excel_header_offset_percent_style_conversion(tmp_path):
    from openpyxl import Workbook
    path=tmp_path/'runs.xlsx'
    wb=Workbook();ws=wb.active;ws.title='Data'
    ws.append(['Experiment outcomes']);ws.append(['시퀀스','Yield (%)','Scale (mmol)','Loading (mmol/g)','Resin','Coupling'])
    ws.append(['AAAAA',0.75,0.1,0.734,'2-CTC','DIC/HOBt']);ws['B3'].number_format='0%'
    ws.append(['AAAAAA',0.82,0.2,0.734,'2-CTC','DIC/HOBt']);ws['B4'].number_format='0.0%'
    wb.save(path)
    p=preview_file(path)
    assert p.header_row==1
    assert 'Yield (%)' in p.excel_percent_columns
    frame,report=normalize_preview(p)
    assert frame['actual_yield_percent'].tolist()==[75.0,82.0]
    raw,_=normalize_preview(p,convert_excel_percent=False)
    assert raw['actual_yield_percent'].tolist()==[.75,.82]


def test_override_mapping_invalid_headers(tmp_path):
    path=tmp_path/'unknown.tsv'
    path.write_text('Peptide\tObserved\nAAAA\t90\n',encoding='utf-8')
    p=preview_file(path)
    assert 'sequence' not in p.mapping
    with pytest.raises(ValueError,match='Sequence'):normalize_preview(p)
    frame,report=normalize_preview(p,{'sequence':'Peptide','actual_yield_percent':'Observed'})
    assert frame['actual_yield_percent'].iloc[0]==90.0
    with pytest.raises(ValueError,match='multiple'):normalize_preview(p,{'sequence':'Peptide','run_id':'Peptide'})


def test_protect_formula_and_invalid_outcomes(tmp_path):
    path=tmp_path/'data.csv'
    path.write_text('Sequence,Actual yield %,Resin\n=HYPERLINK("url"),90,CTC\nAAA,102,CTC\nAAAA,-3,CTC\nAAAAA,75%,CTC\n',encoding='utf-8')
    # Never execute spreadsheet-like payloads even when a CSV reader accepts the line.
    initial=preview_file(path)
    clean,_=normalize_preview(initial)
    assert '=HYPERLINK' not in ''.join(clean['sequence'])
    path.write_text('Sequence,Actual yield %,Resin\n"=HYPERLINK(1)",90,CTC\nAAA,102,CTC\nAAAA,-3,CTC\nAAAAA,75%,CTC\n',encoding='utf-8')
    p=preview_file(path);frame,_=normalize_preview(p)
    assert frame['sequence'].tolist()==['AAA','AAAA','AAAAA']
    assert frame['actual_yield_percent'].isna().sum()==2


def synthetic_experiments(n=50):
    return pd.DataFrame([{
        'sequence':'A'*(i+5),
        'actual_yield_percent':min(95.0,20+i*.9),
        'scale_mmol':0.1+(i%3)*.05,
        'loading_mmol_g':0.734,
        'resin':'2-CTC','chemistry':'DIC/HOBt',
    } for i in range(n)])


def test_training_guardrails_and_similarity(tmp_path):
    frame=synthetic_experiments(12)
    with pytest.raises(ValueError,match='24'):
        train_local_advisor(frame,'actual_yield_percent',tmp_path/'models','abc')
    similar=similar_runs(frame,dict(sequence='AAAAAA',resin='2-CTC',chemistry='DIC/HOBt'))
    assert similar and similar[0]['sequence']=='AAAAAA'
    assert _seq_features('dS-dV-dS')['asp_count']==0
    assert _seq_features('dS-dV-dS')['sequence_length']==3


def test_end_to_end_local_training_and_stale_dataset(tmp_path):
    root=tmp_path/'data';models=tmp_path/'models'
    frame=synthetic_experiments(64)
    report={'mapping':{'sequence':'Sequence'},'usable_targets':{'actual_yield_percent':64}}
    saved=save_reviewed_dataset(frame,report,'filedigest',root)
    loaded,meta=load_reviewed_dataset(root)
    assert len(loaded)==64
    output=train_local_advisor(loaded,'actual_yield_percent',models,meta['dataset_sha256'])
    assert output['status'] in ('EXPERIMENTAL_REVIEW_ONLY','WITHHELD_UNRELIABLE')
    context=dict(sequence='A'*25,scale_mmol=0.1,loading_mmol_g=.734,resin='2-CTC',chemistry='DIC/HOBt')
    estimate=advise_from_local_data(context,root,models)
    assert estimate['similar_runs']
    if output['status']=='EXPERIMENTAL_REVIEW_ONLY':
        assert estimate['status']=='EXPERIMENTAL_PREDICTION_REVIEW_ONLY'
        assert advise_from_local_data({**context,'scale_mmol':99},root,models)['status']=='OUT_OF_DISTRIBUTION'
        file=models/'ai_excel_yield_v9.forest.json'
        original=file.read_bytes()
        file.write_bytes(original+b'tampered')
        assert advise_from_local_data(context,root,models)['status']=='MODEL_INTEGRITY_MISMATCH'
        file.write_bytes(original)
        ood=advise_from_local_data({**context,'resin':'Unknown resin'},root,models)
        assert ood['status']=='OUT_OF_DISTRIBUTION'
    frame.loc[0,'actual_yield_percent']=21.1
    save_reviewed_dataset(frame,report,'filedigest',root)
    stale=advise_from_local_data(context,root,models)
    assert stale['status']=='SIMILAR_EXPERIMENTS_ONLY'


def test_no_data_no_implicit_access(tmp_path):
    result=advise_from_local_data({'sequence':'AAA'},tmp_path/'empty',tmp_path/'models')
    assert result['status']=='NO_REVIEWED_DATA'


def test_ai_import_dialog_smoke_if_display(tmp_path):
    import os
    if not os.environ.get('DISPLAY') and os.name!='nt':
        pytest.skip('Tk display unavailable')
    import tkinter as tk
    from suite_gui.ai_excel_dialog_v9 import open_excel_ai_dialog
    parent=tk.Tk()
    try:
        parent.withdraw()
        gui=SimpleNamespace(ai_excel_data_dir=tmp_path/'data',ai_excel_models_dir=tmp_path/'models')
        dialog=open_excel_ai_dialog(gui,parent=parent,current_context={
            'sequence':'dS-dV-dS','resin':'2-CTC','chemistry':'DIC/HOBt','scale_mmol':0.2,'loading_mmol_g':.734})
        parent.update_idletasks()
        assert dialog.winfo_exists()
        assert 'V9.0.0' in dialog.title()
        dialog.destroy()
    finally:parent.destroy()
