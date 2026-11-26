from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path


def test_cli_audits_csv_without_changing_source_or_saving_data(tmp_path):
    file=tmp_path/'runs.csv'
    file.write_text('Sequence,Actual yield %,Run ID\nAAAAAA,75,TEST\n',encoding='utf-8')
    before=file.read_bytes()
    root=Path(__file__).resolve().parents[1]
    proc=subprocess.run([sys.executable,str(root/'tools/excel_intake_audit_v9.py'),str(file)],
                        text=True,capture_output=True,timeout=20,cwd=tmp_path)
    assert proc.returncode==0,proc.stderr
    result=json.loads(proc.stdout)
    assert result['queued_worksheets']==1
    assert result['worksheets'][0]['valid_sequence_rows']==1
    assert result['worksheets'][0]['status']=='REVIEW_REQUIRED'
    assert 'AAAAAA' not in proc.stdout  # no raw experiment data on stdout
    assert file.read_bytes()==before
    assert not list(tmp_path.glob('ai_excel_reviewed*'))


def test_cli_failed_input_is_explicit(tmp_path):
    root=Path(__file__).resolve().parents[1]
    proc=subprocess.run([sys.executable,str(root/'tools/excel_intake_audit_v9.py'),str(tmp_path/'missing.xlsx')],
                        text=True,capture_output=True,timeout=20,cwd=tmp_path)
    assert proc.returncode==2
    assert json.loads(proc.stderr)['status']=='FAILED'
