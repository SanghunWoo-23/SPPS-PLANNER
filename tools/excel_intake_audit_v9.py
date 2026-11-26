"""Read-only V9 Excel intake preflight; prints no raw experiment sequences.

Examples:
  python tools/excel_intake_audit_v9.py "runs.xlsx" "other.csv"
  python tools/excel_intake_audit_v9.py --first-sheet "runs.xlsx"

No source files, reviewed dataset, ML model or Auto Plan are changed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Support running directly from the source tree without pip installation.
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

from suite_gui.ai_excel_core_v9 import discover_import_sources, normalize_preview, preview_file


def audit_sources(paths: list[str], *, all_data_sheets: bool=True) -> dict:
    worklist, notices=discover_import_sources(paths,all_data_sheets=all_data_sheets)
    entries=[]
    for path,sheet in worklist:
        try:
            preview=preview_file(path,sheet=sheet)
            entry={'file':Path(path).name,'sheet':preview.sheet,
                   'header_row':preview.header_row+1,'source_rows':len(preview.raw),
                   'mapped_fields':sorted(preview.mapping),
                   'warnings':list(preview.warnings)}
            try:
                _,report=normalize_preview(preview)
                entry.update(status='REVIEW_REQUIRED',valid_sequence_rows=report['accepted_rows'],
                             measured_targets=report['usable_targets'])
                entry['warnings'].extend(report['warnings'][len(preview.warnings):])
            except ValueError as exc:
                entry.update(status='MANUAL_MAPPING_REQUIRED', reason=str(exc))
        except (ValueError, OSError) as exc:
            entry={'file':Path(path).name,'sheet':sheet,
                   'status':'REVIEW_FAILED','reason':str(exc)}
        entries.append(entry)
    return {'schema':'spps-v9-excel-intake-audit-v1',
            'imported':False,'model_trained':False,'review_required':True,
            'source_count':len(set(path for path,_ in worklist)),
            'queued_worksheets':len(worklist),'notices':notices,'worksheets':entries}


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sources',nargs='+',help='Excel/CSV/TSV inputs')
    parser.add_argument('--first-sheet',action='store_true',help='Queue only one worksheet per workbook')
    args=parser.parse_args(argv)
    try:
        result=audit_sources(args.sources,all_data_sheets=not args.first_sheet)
    except (ValueError, OSError) as exc:
        print(json.dumps({'status':'FAILED','reason':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    return 0 if not any(row['status']=='REVIEW_FAILED' for row in result['worksheets']) else 1


if __name__=='__main__':
    raise SystemExit(main())
