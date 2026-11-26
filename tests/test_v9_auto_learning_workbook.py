"""Whole-workbook automatic learning and conservative gating."""
from openpyxl import Workbook
from suite_gui.ai_auto_import_v9 import analyze_workbooks, plan_training_targets


def make_workbook(path, *, with_path=True, duplicate=False):
    wb=Workbook()
    wb.active.title='GUIDE'
    wb.active.append(['Documentation'])
    ws=wb.create_sheet('Measurements')
    columns=['Sequence','Actual yield %','Purity %','Scale (mmol)','Loading (mmol/g)','Run ID']
    if with_path:columns.append('Product path')
    ws.append(columns)
    for i in range(32):
        sequence=f'ACD{"A"*(i%5)}{"G"*(i//5+1)}'
        row=[sequence,45+i,75+(i%20),0.1,0.6, 'run-0' if duplicate else f'run-{i}']
        if with_path:row.append('linear_deprotected')
        ws.append(row)
    wb.save(path)


def test_auto_scans_workbook_not_guide_and_detects_targets(tmp_path):
    file=tmp_path/'measured.xlsx';make_workbook(file)
    found=analyze_workbooks([file])
    assert found['ready']
    assert len(found['sources'])==1
    assert found['sources'][0]['sheet']=='Measurements'
    assert len(found['records'])==32
    assert set(found['targets'])=={'actual_yield_percent','actual_purity_percent'}
    assert set(plan_training_targets(found['records']))==set(found['targets'])


def test_auto_keeps_data_but_withholds_unknown_topology(tmp_path):
    file=tmp_path/'unknown.xlsx';make_workbook(file,with_path=False)
    found=analyze_workbooks([file])
    assert found['ready']
    assert found['targets']==[]
    assert plan_training_targets(found['records'])==[]


def test_duplicate_ids_block_unattended_import(tmp_path):
    file=tmp_path/'duplicate.xlsx';make_workbook(file,duplicate=True)
    found=analyze_workbooks([file])
    assert not found['ready']
    assert found['quality']['training_blocked']


def test_no_targets_requires_advanced_mapping(tmp_path):
    file=tmp_path/'unlabeled.xlsx'
    wb=Workbook();ws=wb.active;ws.title='Raw'
    ws.append(['Sequence','Mass (mg)'])
    ws.append(['ACD',99]);wb.save(file)
    found=analyze_workbooks([file])
    assert not found['ready']
    assert any('measured outcome' in x for x in found['blockers'])


def test_ai_import_is_visible_in_history_without_modifying_lab_db(tmp_path):
    """Auto Plan reviewed workbook and Recommendations must resolve one AI store."""
    from types import SimpleNamespace
    import pandas as pd
    from suite_gui.ai_excel_core_v9 import save_reviewed_dataset
    from suite_gui.experimental_workflow import ai_reviewed_outcome_rows

    profile_dir = tmp_path / 'reviewed'
    gui = SimpleNamespace(ai_excel_data_dir=profile_dir)
    assert ai_reviewed_outcome_rows(gui) == []
    measurements = pd.DataFrame([
        {'sequence': 'ACDE', 'actual_yield_percent': 45.0, 'run_id': 'LAB-1', 'reaction_step': 'crude'},
        {'sequence': 'FGHI', 'actual_purity_percent': 98.2, 'run_id': 'LAB-2', 'reaction_step': 'purification'},
    ])
    save_reviewed_dataset(measurements, {'reviewed_by_user': True}, 'test_digest', profile_dir)
    visible = ai_reviewed_outcome_rows(gui)
    assert len(visible) == 2
    assert visible[0]['sequence'] == 'ACDE'
    assert visible[0]['yield_percent'] == 45.0
    assert visible[1]['purity_percent'] == 98.2
    assert all(row['record_id'] == '' for row in visible)
    assert all('read-only' in row['record_state'] for row in visible)
    assert not (tmp_path / 'experiment.db').exists()
