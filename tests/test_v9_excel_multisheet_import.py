"""Multi-sheet Excel batch import uses explicit per-worksheet review and source provenance."""
from __future__ import annotations

import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from suite_gui.ai_excel_core_v9 import (
    discover_import_sources, preview_file, normalize_preview, combine_reviewed_tables,
    verify_preview_source, save_reviewed_dataset, load_reviewed_dataset,
)


def make_workbook(path: Path):
    from openpyxl import Workbook
    wb = Workbook()
    intro = wb.active
    intro.title = 'GUIDE'
    intro.append(['Instruction', 'Do not import'])
    intro.append(['Sequence','not a measured outcome'])
    for name, seq, result in [('2026 October','AAAAAA',81.0),('2026 November','GGEP',71.0)]:
        sheet = wb.create_sheet(name)
        sheet.append(['SPPS experiment data'])
        sheet.append(['Run ID', 'Sequence', 'Actual yield %', 'Purity (%)', 'Product path'])
        sheet.append([name, seq, result, 97.5, 'linear_deprotected'])
    hidden = wb.create_sheet('Internal staging')
    hidden.append(['Sequence','Actual yield %'])
    hidden.append(['CCCC',45])
    hidden.sheet_state='hidden'
    wb.save(path)


def test_autodetect_multiple_data_sheets_and_ignore_guide_and_hidden(tmp_path):
    path=tmp_path/'measurements.xlsx'
    make_workbook(path)
    sources,notes=discover_import_sources([path])
    assert sources == [(str(path),'2026 October'),(str(path),'2026 November')]
    assert any('hidden' in note for note in notes)
    assert any('2 of 4 sheets' in note for note in notes)
    approved=[]
    for source, sheet in sources:
        preview=preview_file(source,sheet=sheet)
        records, report=normalize_preview(preview)
        assert report['source_sheet']==sheet
        assert report['source_file']=='measurements.xlsx'
        verify_preview_source(preview)
        assert report['accepted_rows']==1
        approved.append(records)
    combined, audit=combine_reviewed_tables(*approved)
    assert len(combined)==2
    saved=save_reviewed_dataset(combined,{'sheets':[s for _,s in sources]},'reviewed',tmp_path/'profile')
    restored,_=load_reviewed_dataset(tmp_path/'profile')
    assert saved['rows']==len(restored)==2
    assert set(restored['sequence'])=={'AAAAAA','GGEP'}


def test_single_sheet_legacy_mode_and_fallback_manual_mapping(tmp_path):
    excel=tmp_path/'only_guide.xlsx'
    from openpyxl import Workbook
    wb=Workbook();wb.active.title='GUIDE';wb.active.append(['Note','Instructions'])
    ws=wb.create_sheet('Runs');ws.append(['Peptide','Observed mg']);ws.append(['AAAA',123])
    wb.save(excel)
    queued,notices=discover_import_sources([excel])
    assert queued==[(str(excel),'Runs')]
    assert any('manual mapping' in x for x in notices)
    queued,_=discover_import_sources([excel],all_data_sheets=False)
    assert queued==[(str(excel),'Runs')]


def test_mixed_csv_excel_and_duplicate_selection(tmp_path):
    excel=tmp_path/'measured.xlsx';make_workbook(excel)
    csv=tmp_path/'other.csv';csv.write_text('Sequence,Actual yield %\nRRGH,68\n',encoding='utf-8')
    result,notes=discover_import_sources([excel,csv,excel])
    assert len(result)==3 and result[-1]==(str(csv),None)
    assert any('duplicate file' in n for n in notes)
    with pytest.raises(ValueError,match='between 1 and'):
        discover_import_sources([])
    with pytest.raises(ValueError,match='between 1 and'):
        discover_import_sources([csv]*33)


def test_changed_workbook_after_review_is_rejected(tmp_path):
    path=tmp_path/'data.xlsx';make_workbook(path)
    preview=preview_file(path,sheet='2026 October')
    from openpyxl import load_workbook
    wb=load_workbook(path);wb['2026 October']['C3']=99;wb.save(path)
    with pytest.raises(ValueError,match='changed after preview'):
        verify_preview_source(preview)


def test_formula_requires_recalculation_warning(tmp_path):
    from openpyxl import Workbook
    book=Workbook();sheet=book.active
    sheet.append(['Sequence','Actual yield %']);sheet.append(['AAAA','=30+40'])
    path=tmp_path/'formula.xlsx';book.save(path)
    p=preview_file(path)
    assert any('formula cell' in msg for msg in p.warnings)
    frame,report=normalize_preview(p)
    assert len(frame)==1
    assert frame['actual_yield_percent'].isna().all()
    assert report['usable_targets']['actual_yield_percent']==0


@pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Tk requires display')
def test_multisheet_gui_smoke(tmp_path):
    import tkinter as tk
    from suite_gui.ai_excel_dialog_v9 import open_excel_ai_dialog
    parent=tk.Tk();parent.withdraw()
    try:
        dialog=open_excel_ai_dialog(SimpleNamespace(ai_excel_data_dir=tmp_path/'data',ai_excel_models_dir=tmp_path/'models'),parent=parent)
        parent.update_idletasks()
        controls=[]
        def visit(widget):
            for c in widget.winfo_children():
                controls.append(c)
                visit(c)
        visit(dialog)
        from tkinter import ttk
        texts=[c.cget('text') for c in controls if isinstance(c,ttk.Button)]
        assert 'Skip worksheet' in texts
        assert 'Stage reviewed file / Next' in texts
        assert dialog.winfo_exists()
        dialog.destroy()
    finally:
        parent.destroy()


def test_macro_enabled_workbook_is_read_as_data_not_executed(tmp_path):
    from openpyxl import Workbook
    wb=Workbook();ws=wb.active;ws.title='Results'
    ws.append(['Sequence','Actual yield %','Run ID']);ws.append(['AAAAA',73,'R1'])
    path=tmp_path/'results.xlsm';wb.save(path)
    sources,_=discover_import_sources([path])
    assert sources==[(str(path),'Results')]
    preview=preview_file(path,sheet='Results')
    frame,_=normalize_preview(preview)
    assert frame['actual_yield_percent'].tolist()==[73.0]


def test_header_on_twelfth_row_is_detected_in_scan_and_preview(tmp_path):
    from openpyxl import Workbook
    wb=Workbook();ws=wb.active
    for _ in range(11):ws.append(['', ''])
    ws.append(['Sequence','Actual yield %']);ws.append(['AAAA',53])
    path=tmp_path/'late.xlsx';wb.save(path)
    sources,_=discover_import_sources([path])
    assert sources==[(str(path),'Sheet')]
    p=preview_file(path)
    assert p.header_row==11
    frame,_=normalize_preview(p)
    assert frame['actual_yield_percent'].tolist()==[53.0]

@pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Tk requires display')
def test_real_gui_reviews_two_sheets_before_combined_save(tmp_path, monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    from suite_gui.ai_excel_dialog_v9 import open_excel_ai_dialog
    from suite_gui.ai_excel_core_v9 import load_reviewed_dataset

    path=tmp_path/'measurements.xlsx'
    make_workbook(path)
    from suite_gui import ai_excel_dialog_v9 as dialog_api
    monkeypatch.setattr(dialog_api.filedialog,'askopenfilenames',lambda **_: (str(path),))
    monkeypatch.setattr(dialog_api.messagebox,'askyesno',lambda *_,**__: True)

    root=tk.Tk();root.withdraw()
    try:
        win=open_excel_ai_dialog(
            SimpleNamespace(ai_excel_data_dir=tmp_path/'reviewed',
                            ai_excel_models_dir=tmp_path/'models'),parent=root)
        def children():
            result=[]
            def visit(w):
                for c in w.winfo_children():
                    result.append(c)
                    visit(c)
            visit(win)
            return result
        def button(name):
            return next(w for w in children() if isinstance(w,ttk.Button) and w.cget('text')==name)
        def wait_ready(check,timeout=8):
            deadline=time.monotonic()+timeout
            while time.monotonic()<deadline:
                root.update();time.sleep(.01)
                if check():return
            raise AssertionError('GUI operation timed out: '+str([(w.cget('text'),w.cget('state')) for w in children() if isinstance(w,ttk.Button)])+str([w.cget('textvariable') for w in children() if isinstance(w,ttk.Label) and w.cget('textvariable')]))
        def sheet_text():
            return [w.get() for w in children() if isinstance(w,ttk.Combobox) and w.cget('width')==20]
        def check_approved():
            w=next(w for w in children() if isinstance(w,ttk.Checkbutton)
                   and str(w.cget('text')).startswith('I reviewed the column mapping'))
            w.invoke()
        button('1. Choose Excel(s) / CSV(s)').invoke()
        wait_ready(lambda:'2026 October' in sheet_text())
        button('2. Check & clean').invoke()
        wait_ready(lambda:str(button('3. Save combined data').cget('state'))=='normal')
        time.sleep(.05);root.update()
        check_approved()
        button('Stage reviewed file / Next').invoke()
        wait_ready(lambda:'2026 November' in sheet_text())
        button('2. Check & clean').invoke()
        wait_ready(lambda:str(button('3. Save combined data').cget('state'))=='normal')
        time.sleep(.05);root.update()
        check_approved()
        button('Stage reviewed file / Next').invoke()
        button('3. Save combined data').invoke()
        wait_ready(lambda:(tmp_path/'reviewed'/'ai_excel_reviewed_v9.json').exists())
        data,report=load_reviewed_dataset(tmp_path/'reviewed')
        assert len(data)==2
        assert set(data['sequence'])=={'AAAAAA','GGEP'}
        assert [source['sheet'] for source in report['import_report']['sources']] == ['2026 October','2026 November']
        win.destroy()
    finally:
        root.destroy()


def test_decimal_comma_is_not_thousands_separator_for_lab_units(tmp_path):
    path=tmp_path/'decimal.csv'
    path.write_text('Sequence,Actual yield %,Scale (mmol),Loading (mmol/g)\n'
                    'AAAA,"78,5%","0,2","0,734"\n'
                    'GGGG,85,"1,234","0.80"\n', encoding='utf-8')
    frame,report=normalize_preview(preview_file(path))
    assert frame['actual_yield_percent'].tolist()==[78.5,85]
    assert frame['scale_mmol'].iloc[0] == .2
    assert frame['loading_mmol_g'].iloc[0] == .734
    assert frame['scale_mmol'].isna().sum()==1
    assert any('ambiguous decimal separators' in m for m in report['warnings'])


def test_duplicate_excel_headers_warn_for_operator_review(tmp_path):
    from openpyxl import Workbook
    wb=Workbook();ws=wb.active
    ws.append(['Sequence','Actual yield %','Actual yield %'])
    ws.append(['AAAA',75,15])
    path=tmp_path/'duplicates.xlsx';wb.save(path)
    preview=preview_file(path)
    assert any('Duplicate source headers' in m for m in preview.warnings)


def test_bundled_blank_excel_template_is_discoverable_even_without_dimensions():
    root=Path(__file__).resolve().parents[1]
    path=root/'docs/templates/SPPS_Planner_V9_EXCEL_MULTI_SHEET_TEMPLATE.xlsx'
    assert path.is_file()
    worklist,_=discover_import_sources([path])
    assert [sheet for _,sheet in worklist] == ['Final Outcomes','Process Steps','HPLC-MS']
    for workbook, sheet in worklist:
        preview=preview_file(workbook,sheet=sheet)
        assert preview.mapping['sequence'] == 'Sequence'
        assert preview.raw.empty
