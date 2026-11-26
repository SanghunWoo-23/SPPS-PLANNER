"""Synthetic, repeatable 10k-row Excel/CSV import benchmark; no private data."""
from __future__ import annotations
import csv
import json
import tempfile
import time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'apps/spps_planner_app')]
from suite_gui.ai_excel_core_v9 import preview_file,normalize_preview


def main():
    with tempfile.TemporaryDirectory(prefix='spps_v9_benchmark_') as folder:
        source=Path(folder)/'synthetic_10000.csv'
        with source.open('w',newline='',encoding='utf-8-sig') as stream:
            write=csv.writer(stream)
            write.writerow(['Sequence','Run ID','Product path','Reaction step','Scale (mmol)',
                            'Loading (mmol/g)','Resin','Coupling','Actual yield %'])
            for i in range(10_000):
                write.writerow(['ASGV'+('A'*(i%15)),f'SYNTHETIC-{i}',
                               'linear_deprotected','crude',0.1,0.75,'2-CTC','DIC/HOBt',65.0])
        started=time.perf_counter()
        preview=preview_file(source)
        frame,report=normalize_preview(preview)
        elapsed=time.perf_counter()-started
        result={'schema':'spps-v9-benchmark-v1','environment':'current Python process, not Windows EXE',
                'synthetic_rows':10_000,'accepted_rows':len(frame),'seconds':round(elapsed,3),
                'status':'PASS' if len(frame)==10_000 else 'FAIL',
                'note':'CSV parse/normalize only; not proof of GUI frame rate, training accuracy or memory leak absence.'}
        print(json.dumps(result,indent=2))
        return 0 if result['status']=='PASS' else 1
if __name__=='__main__':
    raise SystemExit(main())
