"""Conservative whole-workbook auto-learning orchestrator for SPPS Planner V9.

Import is local, read-only until user approves. Only recognized measured targets
are eligible for training; no unverified values or model outcomes become truth.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path

from suite_gui.ai_excel_core_v9 import (
    discover_import_sources, preview_file, normalize_preview, verify_preview_source,
    combine_reviewed_tables, ml_readiness_report, load_reviewed_dataset,
    audit_reviewed_data, MIN_TRAIN,
)
from suite_gui.process_ai_v9 import STAGE_TARGETS


def analyze_workbooks(paths):
    """Analyze every recognized data sheet, never guess unrecognized columns."""
    queued, notices = discover_import_sources(paths, all_data_sheets=True)
    sources=[]
    tables=[]
    blockers=[]
    digests=[]
    for path,sheet in queued:
        preview=preview_file(path,sheet=sheet)
        mapping=preview.mapping
        name=f'{Path(path).name} / {preview.sheet}'
        if 'sequence' not in mapping:
            blockers.append(f'{name}: peptide sequence column not identified; use Advanced.')
            continue
        targets=set(mapping).intersection({'actual_yield_percent','actual_purity_percent',*STAGE_TARGETS})
        if not targets:
            blockers.append(f'{name}: measured outcome column not identified; use Advanced.')
            continue
        # Excel percentage-formatted cells are detected per source by the existing engine.
        normalized, report=normalize_preview(preview, mapping, convert_excel_percent=True)
        verify_preview_source(preview)
        if not len(normalized):
            blockers.append(f'{name}: no valid peptide sequence rows.')
            continue
        if report['warnings']:
            notices.extend(f'{name}: {w}' for w in report['warnings'])
        tables.append(normalized)
        digests.append(preview.file_sha256 + ':' + str(preview.sheet))
        sources.append({'file':Path(path).name,'sheet':preview.sheet,
                        'rows':len(normalized),'mapping':dict(mapping),
                        'sha256':preview.file_sha256,
                        'targets':report['usable_targets'], 'warnings':report['warnings']})
    if blockers:
        return {'ready':False,'blockers':blockers,'notices':notices,
                'sources':sources,'records':None,'quality':None,'targets':[]}
    if not tables:
        return {'ready':False,'blockers':['No eligible measured experiment records found.'],
                'notices':notices,'sources':sources,'records':None,'quality':None,'targets':[]}
    combined, quality=combine_reviewed_tables(*tables)
    if quality['training_blocked']:
        blockers.append('Duplicate run IDs, repeated rows or invalid sequences need Advanced review before importing or learning.')
    if len({src['file'] for src in sources}) != len({str(Path(x[0]).resolve()) for x in queued}):
        blockers.append('Some selected files had no eligible data. Open Advanced to resolve mappings.')
    readiness=ml_readiness_report(combined)
    # Unknown topology cannot safely be presumed linear for unattended learning.
    have_path = ('product_path' in combined and combined['product_path'].astype(str).str.strip().isin(('linear_deprotected',)).all())
    eligible=[t for t,details in readiness['targets'].items() if details['ready'] and have_path]
    if not have_path:
        notices.append('Automatic linear ML withheld: Product path must explicitly identify linear_deprotected for all training rows.')
    # Stage readiness can be decided only after measuring stage-specific evidence.
    for target,step in STAGE_TARGETS.items():
        if target not in combined or 'reaction_step' not in combined or 'product_path' not in combined:
            continue
        selected=combined[combined['reaction_step'].astype(str).str.strip().str.casefold()==step]
        if target in selected:
            valid=int(selected[target].notna().sum())
            if valid >= MIN_TRAIN:
                eligible.append(target)  # engine still verifies per-topology sample and method scope
    return {'ready':not blockers,'blockers':blockers,'notices':notices,
            'sources':sources,'records':combined,'quality':quality,
            'targets':eligible,'readiness':readiness,
            'source_digest':sha256('|'.join(digests).encode('utf-8')).hexdigest()}


def plan_training_targets(records):
    """Calculate readiness on the complete saved dataset, not just new sources."""
    quality=audit_reviewed_data(records)
    if quality['training_blocked']:
        return []
    readiness=ml_readiness_report(records)
    have_path = ('product_path' in records and records['product_path'].astype(str).str.strip().isin(('linear_deprotected',)).all())
    targets=[t for t,v in readiness['targets'].items() if v['ready'] and have_path]
    for target,stage in STAGE_TARGETS.items():
        if target not in records or 'reaction_step' not in records or 'product_path' not in records:
            continue
        sub=records[records['reaction_step'].astype(str).str.strip().str.casefold()==stage]
        if len(sub)>=MIN_TRAIN and sub[target].notna().sum()>=MIN_TRAIN:
            targets.append(target)
    return targets
