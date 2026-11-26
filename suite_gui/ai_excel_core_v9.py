"""Local, review-first Excel/CSV outcomes ingestion and conservative AI advisory.

No network calls. No changes to chemistry engine. No external model files accepted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from heapq import nsmallest
from functools import lru_cache
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import tempfile
import zipfile
from typing import Any

import pandas as pd

SCHEMA = 'spps-v9-excel-ai-v1'
MAX_BYTES = 12 * 1024 * 1024
MAX_ROWS = 20_000
MAX_COLS = 70
MAX_XLSX_UNCOMPRESSED = 128 * 1024 * 1024
MAX_XLSX_PARTS = 1500
MAX_BATCH_FILES = 32
MAX_BATCH_SHEETS = 96
MAX_SCAN_SHEETS_PER_FILE = 64
MAX_DATASET_BYTES = 64 * 1024 * 1024
MIN_TRAIN = 24
MIN_SEQUENCE_GROUPS = 6

# The aliases are deliberately conservative. No target is inferred from "weight" or "yield (mg)".
ALIASES: dict[str, tuple[str, ...]] = {
    'sequence': ('sequence','peptide sequence','peptide seq','seq','peptide_sequence','서열','펩타이드서열','아미노산서열','시퀀스'),
    'actual_yield_percent': ('actual_yield_percent','yield_perc','actual yield percent','actual yield %','yield (%)','yield(%)','yield %', 'yield(%)', 'yield_percent','isolated yield %','recovery %','수득률','수득률(%)','실측수득률','최종수득률','실제수득률'),
    'actual_purity_percent': ('actual_purity_percent','actual purity %','purity %','purity (%)','purity(%)','purity_percent','hplc purity %','순도','순도(%)','hplc순도'),
    'scale_mmol': ('scale_mmol','scale (mmol)','scale mmol','scale','synthesis scale','합성스케일','합성규모','스케일','스케일(mmol)'),
    'loading_mmol_g': ('loading_mmol_g','loading (mmol/g)','loading mmol/g','loading','resin loading','로딩','레진로딩','로딩(mmol/g)'),
    'resin': ('resin','resin type','resin_name','resin name','resin 종류','레진','레진종류'),
    'chemistry': ('chemistry','coupling system','coupling reagent','coupling_system','coupling','coupling chemistry','커플링','커플링시약','커플링시스템','반응시스템'),
    'run_id': ('run id','run_id','experiment id','experiment_id','실험번호','실험id','배치번호','batch id'),
    'product_path': ('product path','product_path','product type','topology','final product type','최종제품형태','제품형태','합성유형','토폴로지'),
    'reaction_step': ('reaction step','process step','stage','step','공정단계','반응단계','합성단계'),
    'reaction_method': ('reaction_method','cyclization method','reaction method','cyclization_system','반응법','고리화반응법','고리화시스템'),
    'cleavage_method': ('cleavage_method','cleavage cocktail','cleavage recipe','절단시약','절단법','클리비지방법'),
    'reaction_time_h': ('reaction_time_h','reaction time (h)','reaction time h','반응시간(h)','반응시간'),
    'reaction_concentration_mm': ('reaction_concentration_mm','reaction concentration (mm)','concentration mm','reaction concentration mm','반응농도(mm)','고리화농도'),
    'coupling_conversion_percent': ('coupling_conversion_percent','coupling conversion %','coupling conversion','커플링전환율','커플링전환율(%)'),
    'cyclization_yield_percent': ('cyclization_yield_percent','cyclization yield %','cyclic yield %','고리화수율','고리화수율(%)'),
    'purification_recovery_percent': ('purification_recovery_percent','purification recovery %','prep hplc recovery %','정제회수율','정제회수율(%)'),
    'crude_yield_percent': ('crude_yield_percent','crude yield %','crude recovery %','크루드수율','조수율(%)'),
    'cleavage_recovery_percent': ('cleavage_recovery_percent','cleavage recovery %','selective cleavage recovery %','절단회수율','클리비지수득률'),
    'protection_profile': ('protection_profile','protecting group profile','protecting groups','보호기구성','보호기정보'),
    'hplc_method': ('hplc_method','hplc method','hplc method id','hplc방법','hplc조건'),
    'observed_mz': ('observed_mz','observed m/z','observed mass to charge','ms m/z','측정m/z','관측mz'),
}
DISPLAY = {
    'sequence':'Sequence / 서열', 'actual_yield_percent':'Actual yield % / 실제 수득률',
    'actual_purity_percent':'Purity % / 순도', 'scale_mmol':'Scale (mmol)',
    'loading_mmol_g':'Loading (mmol/g)', 'resin':'Resin / 레진',
    'chemistry':'Coupling / 커플링', 'run_id':'Run ID / 실험번호',
    'product_path':'Product path / 최종 형태', 'reaction_step':'Reaction stage / 반응 단계',
    'reaction_method':'Reaction method / 고리화법', 'cleavage_method':'Cleavage method / 절단법',
    'reaction_time_h':'Reaction time (h)', 'reaction_concentration_mm':'Reaction conc. (mM)',
    'coupling_conversion_percent':'Coupling conversion %', 'cyclization_yield_percent':'Cyclization yield %',
    'purification_recovery_percent':'Purification recovery %', 'crude_yield_percent':'Crude yield %',
    'cleavage_recovery_percent':'Cleavage recovery %',
    'protection_profile':'Protecting groups / 보호기 구성',
    'hplc_method':'HPLC Method / 분석법', 'observed_mz':'Observed MS m/z',
}


def create_blank_excel_template(path: str | Path) -> Path:
    """Make a *blank* operator-fillable workbook, never synthetic lab results.

    Created on explicit click only, with no imported company/Private records.
    The sample guide documents formats, while the Runs sheet contains headers
    and no fake peptides, yields or approvals.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.worksheet.datavalidation import DataValidation
    path = Path(path)
    if path.suffix.lower() != '.xlsx':
        raise ValueError('Blank template must be saved as .xlsx.')
    if path.is_symlink():
        raise ValueError('Refusing to overwrite a symlink.')
    columns = ['Sequence','Actual yield %','Purity %','Scale (mmol)',
               'Loading (mmol/g)','Resin','Coupling','Run ID',
               'Product path','Reaction step']
    workbook = Workbook()
    ws=workbook.active
    ws.title='Runs'
    ws.append(columns)
    ws.freeze_panes='A2'
    ws.auto_filter.ref='A1:J1'
    for col in ws[1]:
        col.fill=PatternFill('solid',fgColor='17365D')
        col.font=Font(name='Aptos',color='FFFFFF',bold=True)
        col.alignment=Alignment(wrap_text=True)
    for letter,width in zip('ABCDEFGHIJ',[28,18,16,19,23,19,24,20,25,25]):
        ws.column_dimensions[letter].width=width
    validation=DataValidation(type='list',formula1='"'+','.join(PRODUCT_PATHS)+'"',allow_blank=True)
    validation.error='Use one of the listed path values. Do not guess an unknown pathway.'
    validation.showErrorMessage=True
    ws.add_data_validation(validation)
    validation.add('I2:I2000')
    guide=workbook.create_sheet('GUIDE')
    guide.append(['Field','How to fill','Safety / data meaning'])
    text=[
        ('Sequence','Amino-acid sequence, e.g. ACD','Use the exact chemical notation as recorded; do not invent missing modifications.'),
        ('Actual yield %','Measured isolation yield 0–100','Do not input planned or predicted yield as an actual measurement.'),
        ('Purity %','Measured HPLC purity 0–100','Specify a consistent and validated analytical method in the lab record.'),
        ('Scale (mmol)','Positive number','Example unit: mmol, not mg.'),
        ('Loading (mmol/g)','Positive number','Record true resin loading, not resin mass.'),
        ('Resin','Resin name','Use consistent reagent/resin naming.'),
        ('Coupling','Reaction chemistry','Use consistent system names for comparisons.'),
        ('Run ID','Unique real experiment identifier','One Run ID must not be reused for conflicting measurements.'),
        ('Product path','One of the dropdown values','Cyclic/protected data are not used for legacy linear/deprotected ML.'),
        ('Reaction step','Optional measured process step','Record distinct stages instead of confusing cyclization with final isolated yield.'),
    ]
    for row in text: guide.append(row)
    guide.freeze_panes='A2'
    for col in guide[1]:
        col.font=Font(bold=True,color='FFFFFF')
        col.fill=PatternFill('solid',fgColor='17365D')
    guide.column_dimensions['A'].width=24
    guide.column_dimensions['B'].width=45
    guide.column_dimensions['C'].width=90
    path.parent.mkdir(parents=True,exist_ok=True)
    workbook.save(path)
    return path


def _normalize_header(v: Any) -> str:
    return re.sub(r'[^a-z0-9가-힣%]', '', str(v or '').strip().casefold())


# Alias definitions are immutable during a running import; normalize them once.
# Keep the field-priority and first-unused-column rules of the reviewed mapper.
_NORMALIZED_ALIASES = {
    key: frozenset(_normalize_header(alias) for alias in aliases)
    for key, aliases in ALIASES.items()
}


def auto_mapping(columns: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    used: set[str] = set()
    normalized_columns = [(col, _normalize_header(col)) for col in columns]
    for key, normalized_aliases in _NORMALIZED_ALIASES.items():
        for col, normalized in normalized_columns:
            if col not in used and normalized in normalized_aliases:
                out[key] = col
                used.add(col)
                break
    return out


def _header_score(cells: list[Any]) -> int:
    strings = [str(c).strip() if c is not None and not pd.isna(c) else '' for c in cells]
    mapped = auto_mapping(strings)
    return sum(4 if k == 'sequence' else 3 if k in ('actual_yield_percent','actual_purity_percent') else 1 for k in mapped)



def _sha256_file(path: Path) -> str:
    """Hash local source/model files without retaining their bytes in RAM."""
    digest = sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_source_file(path: Path) -> None:
    """Bound local input size and reject oversized/invalid XLSX archives before parsing."""
    if not path.is_file() or not 0 < path.stat().st_size <= MAX_BYTES:
        raise ValueError('Choose a non-empty local file no larger than 12 MB.')
    if path.suffix.lower() in ('.xlsx', '.xlsm'):
        try:
            with zipfile.ZipFile(path) as archive:
                members = archive.infolist()
                if (len(members) > MAX_XLSX_PARTS
                    or sum(member.file_size for member in members) > MAX_XLSX_UNCOMPRESSED
                    or any(member.flag_bits & 0x1 for member in members)):
                    raise ValueError('XLSX archive is oversized or encrypted; convert to a smaller workbook.')
        except zipfile.BadZipFile as exc:
            raise ValueError('Invalid XLSX file.') from exc


def verify_preview_source(preview: 'Preview') -> None:
    """Do not accept a reviewed preview if the underlying workbook changed."""
    path = Path(preview.file_path)
    _verify_source_file(path)
    if _sha256_file(path) != preview.file_sha256:
        raise ValueError('Source Excel/CSV changed after preview. Reopen and review the file before saving.')


def _load_sheet(path: Path, sheet: str | None):
    suffix = path.suffix.lower()
    if suffix in ('.xlsx', '.xlsm'):
        # Pandas/openpyxl reads cached values, does not evaluate spreadsheet formulas.
        with pd.ExcelFile(path, engine='openpyxl') as book:
            names = list(book.sheet_names)
            if not names:
                raise ValueError('Excel workbook has no sheets.')
            sheet = sheet or names[0]
            if sheet not in names:
                raise ValueError(f'Worksheet not found: {sheet}')
            frame = pd.read_excel(book, sheet_name=sheet, header=None,
                                  dtype=object, nrows=MAX_ROWS + 14)
        return frame, names, sheet
    if suffix not in ('.csv', '.tsv', '.txt'):
        raise ValueError('Only .xlsx, .xlsm, .csv, .tsv and .txt are supported. Convert old .xls first.')
    errors = []
    for encoding in ('utf-8-sig', 'cp949', 'utf-16'):
        try:
            frame = pd.read_csv(path, encoding=encoding, sep='\t' if suffix == '.tsv' else None,
                                engine='python', header=None, dtype=object, nrows=MAX_ROWS + 14,
                                on_bad_lines='error')
            return frame, ['CSV'], 'CSV'
        except (UnicodeError, pd.errors.ParserError, ValueError) as exc:
            errors.append(str(exc))
    raise ValueError('Unable to read table encoding or delimiters. ' + '; '.join(errors)[:300])


def discover_import_sources(paths: list[str | Path], *, all_data_sheets: bool = True
                            ) -> tuple[list[tuple[str, str | None]], list[str]]:
    """Find plausible measured-outcome sheets without importing or approving records.

    A workbook can contain data, SOP, GUIDE, blank and graph sheets. A worksheet
    is queued automatically only when a Sequence column and at least one
    measured outcome column appear within the first 12 rows. Users must still
    review every queued worksheet separately before it is saved. Workbooks
    with no recognized data sheet are queued at their first sheet for *manual*
    mapping rather than being silently discarded.
    """
    if not isinstance(paths, (list, tuple)) or not paths or len(paths) > MAX_BATCH_FILES:
        raise ValueError(f'Select between 1 and {MAX_BATCH_FILES} source files.')
    queued: list[tuple[str, str | None]] = []
    notices: list[str] = []
    seen_files: set[str] = set()
    targets = {'actual_yield_percent', 'actual_purity_percent',
               'coupling_conversion_percent', 'cyclization_yield_percent',
               'purification_recovery_percent', 'crude_yield_percent',
               'cleavage_recovery_percent'}
    for source in paths:
        path = Path(source)
        _verify_source_file(path)
        resolved = str(path.resolve())
        if resolved in seen_files:
            notices.append(f'{path.name}: duplicate file selection ignored.')
            continue
        seen_files.add(resolved)
        suffix = path.suffix.lower()
        if suffix not in ('.xlsx', '.xlsm'):
            if suffix not in ('.csv', '.tsv', '.txt'):
                raise ValueError(f'{path.name}: unsupported format.')
            queued.append((str(path), None))
            continue
        from openpyxl import load_workbook
        workbook = load_workbook(path, read_only=True, data_only=True)
        try:
            if len(workbook.sheetnames) > MAX_SCAN_SHEETS_PER_FILE:
                raise ValueError(f'{path.name}: too many sheets; maximum {MAX_SCAN_SHEETS_PER_FILE}.')
            selected: list[str] = []
            sampled_rows: dict[str, list[tuple[Any, ...]]] = {}
            if all_data_sheets:
                for name in workbook.sheetnames:
                    ws = workbook[name]
                    if ws.sheet_state != 'visible':
                        notices.append(f'{path.name} / {name}: hidden worksheet not queued.')
                        continue
                    if ws.max_column is not None and ws.max_column > MAX_COLS:
                        notices.append(f'{path.name} / {name}: over {MAX_COLS} columns; review manually.')
                        continue
                    sample = list(ws.iter_rows(min_row=1, max_row=min(12, ws.max_row or 12),
                                               max_col=min(MAX_COLS, ws.max_column or MAX_COLS),
                                               values_only=True))
                    sampled_rows[name] = sample
                    header = max(sample, key=lambda row: _header_score(list(row)), default=())
                    mapping = auto_mapping([str(v).strip() if v is not None else '' for v in header])
                    guide = any(word in name.casefold() for word in
                                ('guide', 'instruction', 'readme', '설명', '가이드'))
                    has_measured = bool(targets.intersection(mapping))
                    has_metadata = bool({'run_id','scale_mmol','reaction_step','resin','chemistry'} & mapping.keys())
                    if 'sequence' in mapping and (has_measured or has_metadata) and not guide:
                        selected.append(name)
                if not selected:
                    notices.append(f'{path.name}: no measured-outcome sheet auto-detected. '
                                   'First worksheet queued for manual mapping; no sheet skipped silently.')
            if not selected:
                # No known outcome table: select the likeliest visible data tab
                # for *manual* column mapping instead of defaulting to GUIDE.
                def likely_sheet(name: str) -> tuple[int, int, int]:
                    sheet = workbook[name]
                    if sheet.sheet_state != 'visible':
                        return (-1, -1, -1)
                    guide = any(word in name.casefold() for word in
                                ('guide', 'instruction', 'readme', '설명', '가이드'))
                    cells = sampled_rows.get(name)
                    if cells is None:
                        cells = list(sheet.iter_rows(min_row=1,
                            max_row=min(12, sheet.max_row or 12),
                            max_col=min(MAX_COLS, sheet.max_column or MAX_COLS),
                            values_only=True))
                    header_score = max((_header_score(list(row)) for row in cells),default=0)
                    populated = sum(any(value is not None and str(value).strip() for value in row)
                                    for row in cells)
                    return (0 if guide else 1, header_score, populated)
                candidates = [name for name in workbook.sheetnames
                              if workbook[name].sheet_state == 'visible']
                selected = [max(candidates,key=likely_sheet)] if candidates else []
            if not selected:
                raise ValueError(f'{path.name}: workbook has no worksheets.')
            queued.extend((str(path), name) for name in selected)
            if all_data_sheets and len(selected) < len(workbook.sheetnames):
                notices.append(f'{path.name}: queued {len(selected)} of {len(workbook.sheetnames)} sheets; GUIDE/blank/other non-data sheets were not queued.')
        finally:
            workbook.close()
        if len(queued) > MAX_BATCH_SHEETS:
            raise ValueError(f'Too many worksheets in one batch (max {MAX_BATCH_SHEETS}).')
    if not queued:
        raise ValueError('No readable input files or worksheets selected.')
    return queued, notices


def sheet_names(path: str | Path) -> list[str]:
    path = Path(path)
    _verify_source_file(path)
    if path.suffix.lower() in ('.xlsx', '.xlsm'):
        with pd.ExcelFile(path, engine='openpyxl') as book:
            return list(book.sheet_names)
    if path.suffix.lower() in ('.csv', '.tsv', '.txt'):
        return ['CSV']
    raise ValueError('Unsupported file type. Use Excel .xlsx/.xlsm or CSV/TSV.')


@dataclass
class Preview:
    file_path: str
    sheet: str
    sheets: list[str]
    header_row: int
    raw: pd.DataFrame
    mapping: dict[str, str]
    columns: list[str]
    file_sha256: str
    excel_percent_columns: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        recognized = ', '.join(f'{k} <- {v}' for k,v in self.mapping.items()) or 'none'
        return f'{len(self.raw)} data rows | sheet {self.sheet} | header row {self.header_row + 1}\nDetected: {recognized}'


def preview_file(path: str | Path, *, sheet: str | None = None) -> Preview:
    path = Path(path)
    _verify_source_file(path)
    frame, names, selected = _load_sheet(path, sheet)
    if frame.empty:
        raise ValueError('The selected sheet is empty.')
    if len(frame.columns) > MAX_COLS or len(frame) > MAX_ROWS + 13:
        raise ValueError(f'Table too large (maximum {MAX_ROWS} data rows, {MAX_COLS} columns).')
    best = max(range(min(12, len(frame))), key=lambda i: _header_score(frame.iloc[i].tolist()))
    header = []
    for i, cell in enumerate(frame.iloc[best].tolist()):
        val = str(cell).strip() if pd.notna(cell) else ''
        header.append(val if val and val.lower() != 'nan' else f'Column {i + 1}')
    # Keep original display headers and avoid duplicate column labels.
    seen: dict[str,int] = {}
    unique = []
    for col in header:
        seen[col] = seen.get(col,0)+1
        unique.append(col if seen[col]==1 else f'{col} ({seen[col]})')
    duplicated_headers = [col for col, count in seen.items() if count > 1 and not col.startswith('Column ')]
    data = frame.iloc[best + 1:].copy()
    data.columns = unique
    data = data.dropna(how='all').reset_index(drop=True)
    warnings = []
    if duplicated_headers:
        warnings.append('Duplicate source headers detected: ' + ', '.join(duplicated_headers[:8]) + '. Confirm the selected column before approval.')
    if not len(data):
        warnings.append('No non-empty data rows detected.')
    if not auto_mapping(unique).get('sequence'):
        warnings.append('Sequence column not found; choose it in column mapping.')
    if not ({'actual_yield_percent','actual_purity_percent'} & auto_mapping(unique).keys()):
        warnings.append('No measured yield/purity target detected; choose a target column to train.')
    normalized_headers = [(col, _normalize_header(col)) for col in unique]
    for key, aliases in _NORMALIZED_ALIASES.items():
        matches = [col for col, normalized in normalized_headers if normalized in aliases]
        if len(matches) > 1:
            warnings.append(f'Ambiguous {key} columns: {", ".join(matches)}. Confirm the selected mapping before approval.')
    percent_columns=[]
    if path.suffix.lower() in ('.xlsx', '.xlsm'):
        # Read percentage number formats so an Excel cell displayed as 75% (raw 0.75)
        # is not silently interpreted as a 0.75% assay result.
        from openpyxl import load_workbook
        book=load_workbook(path,read_only=True,data_only=True)
        try:
            work=book[selected]
            matches={col:0 for col in unique};observed={col:0 for col in unique}
            for cells in work.iter_rows(min_row=best+2,max_row=best+13):
                for col,cell in zip(unique,cells):
                    if isinstance(cell.value,(int,float)) and not isinstance(cell.value,bool):
                        observed[col]+=1
                        if '%' in str(cell.number_format):matches[col]+=1
            percent_columns=[col for col in unique if observed[col] and matches[col]>=max(1,observed[col]*0.7)]
        finally:book.close()
        if percent_columns:
            warnings.append('Excel percentage-formatted columns detected: '+', '.join(percent_columns)+'. Numeric fractions will be converted to 0–100%.')
    if path.suffix.lower() in ('.xlsx', '.xlsm'):
        # Cached formula results are not guaranteed to exist. Warn, don't
        # compute Excel formulas or silently present an empty calculated assay.
        from openpyxl import load_workbook
        formulas = load_workbook(path, read_only=True, data_only=False)
        try:
            worksheet = formulas[selected]
            count = 0
            for cells in worksheet.iter_rows(min_row=best+2,
                       max_row=min(best+13, worksheet.max_row or best+13),
                       max_col=min(len(unique), MAX_COLS)):
                count += sum(cell.data_type == 'f' for cell in cells)
            if count:
                warnings.append(f'{count} formula cell(s) detected in sampled outcome rows. '
                                'Only cached results are read; open and recalculate the workbook '
                                'in Excel before importing if measurements appear blank.')
        finally:
            formulas.close()
    digest = _sha256_file(path)
    return Preview(str(path), selected, names, best, data, auto_mapping(unique), unique, digest, percent_columns, warnings)


def _decimal_number(value: Any) -> float | None:
    """Parse decimal comma explicitly, never mistake 0,734 for 734.

    The token ``1,234`` is ambiguous (decimal comma vs thousands) and is
    rejected. Operators must normalize ambiguous source data themselves.
    """
    if isinstance(value, bool):
        return None
    if pd.isna(value):
        return None
    text = str(value).strip().replace('\u00a0', ' ').replace(' ', '')
    if not text:
        return None
    if ',' in text and '.' in text:
        if re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3})+\.\d+', text):
            text = text.replace(',', '')
        elif re.fullmatch(r'[+-]?\d{1,3}(?:\.\d{3})+,\d+', text):
            text = text.replace('.', '').replace(',', '.')
        else:
            return None
    elif ',' in text:
        if re.fullmatch(r'[+-]?\d{1,3}(?:,\d{3}){2,}', text):
            text = text.replace(',', '')
        elif re.fullmatch(r'[+-]?\d+,\d+', text):
            left, right = text.split(',')
            if len(right) == 3 and int(left) >= 1:
                return None
            text = left+'.'+right
        else:
            return None
    try:
        number = float(text)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _percentage(value: Any) -> float | None:
    if pd.isna(value) or str(value).strip() in ('', '-', 'N/A', 'n/a'):
        return None
    if isinstance(value, bool):
        return None
    text = str(value).strip().replace('％','%')
    if text.endswith('%'):
        text = text[:-1].strip()
    out = _decimal_number(text)
    return out if out is not None and 0 <= out <= 100 else None


def _positive_number(value: Any, unit: str) -> float | None:
    if pd.isna(value) or str(value).strip() == '': return None
    text = str(value).strip()
    text = re.sub(r'\s*' + re.escape(unit) + r'\s*$', '',text,flags=re.I)
    out = _decimal_number(text)
    return out if out is not None and out > 0 else None


PRODUCT_PATHS = ('linear_deprotected','linear_protected','cyclic_protected','cyclic_deprotected',
                 'branched_deprotected','branched_protected')


def normalize_product_path(value: Any) -> str:
    """Do not invent protected/cyclic structure from vague spreadsheet labels."""
    if value is None or (isinstance(value,float) and math.isnan(value)):
        return ''
    text = str(value).strip().casefold().replace('-', '_').replace(' ', '_')
    if text in ('','nan','none'):
        return ''  # Legacy unlabeled data; only the linear reference task can use it.
    aliases={'linear':'linear_deprotected','linear_unprotected':'linear_deprotected',
             'cyclic_unprotected':'cyclic_deprotected','head_to_tail_deprotected':'cyclic_deprotected','head_to_tail_protected':'cyclic_protected',
             'protected_linear':'linear_protected','protected_cyclic':'cyclic_protected',
             'branch_unprotected':'branched_deprotected','branch_protected':'branched_protected'}
    return aliases.get(text,text) if aliases.get(text,text) in PRODUCT_PATHS else 'UNRECOGNIZED'


def normalize_preview(preview: Preview, mapping: dict[str,str] | None = None, *, convert_excel_percent: bool=True) -> tuple[pd.DataFrame, dict[str, Any]]:
    mapping = mapping if mapping is not None else preview.mapping
    if len(set(mapping.values())) != len(mapping):
        raise ValueError('A source column cannot be assigned to multiple fields.')
    if any(key not in ALIASES or col not in preview.columns for key, col in mapping.items()):
        raise ValueError('Invalid source column mapping.')
    if 'sequence' not in mapping:
        raise ValueError('Map the peptide Sequence column first.')
    records = pd.DataFrame(index=preview.raw.index)
    for key, name in mapping.items():
        records[key] = preview.raw[name]
    records['sequence'] = records['sequence'].fillna('').astype(str).str.strip()
    records['sequence'] = records['sequence'].where(records['sequence'].str.len().between(1,512) & ~records['sequence'].str.match(r'^[=+@]', na=False),'')
    for key in ('resin','chemistry','run_id','product_path','reaction_step','reaction_method','cleavage_method','protection_profile','hplc_method'):
        if key in records:
            records[key] = records[key].fillna('').astype(str).str.strip().str.slice(0,120)
            records[key] = records[key].where(~records[key].str.match(r'^[=+@]',na=False), '')
    invalid_outcomes: dict[str, int] = {}
    for key in ('actual_yield_percent','actual_purity_percent','coupling_conversion_percent','cyclization_yield_percent','purification_recovery_percent','crude_yield_percent','cleavage_recovery_percent'):
        if key in records:
            original=records[key]
            filled=original.notna() & original.astype(str).str.strip().ne('')
            styled = convert_excel_percent and mapping.get(key) in preview.excel_percent_columns
            if styled:
                converted=original.map(lambda v: _percentage(float(v)*100) if isinstance(v,(int,float)) and 0<=v<=1 else _percentage(v))
            else:
                converted=original.map(_percentage)
            invalid_outcomes[key]=int((filled & converted.isna()).sum())
            records[key]=converted
    invalid_numbers: dict[str, int] = {}
    for key,unit in (('scale_mmol','mmol'),('loading_mmol_g','mmol/g'),('reaction_time_h','h'),('reaction_concentration_mm','mM'),('observed_mz','')):
        if key in records:
            original = records[key]
            filled = original.notna() & original.astype(str).str.strip().ne('')
            converted = original.map(lambda x: _positive_number(x,unit))
            invalid_numbers[key] = int((filled & converted.isna()).sum())
            records[key] = converted
    if 'product_path' in records:
        records['product_path']=records['product_path'].map(normalize_product_path)
    records = records[records['sequence'].astype(bool)].reset_index(drop=True)
    duplicate_rows = int(records.duplicated(keep='first').sum())
    counts = {k:int(records[k].notna().sum()) for k in ('actual_yield_percent','actual_purity_percent','coupling_conversion_percent','cyclization_yield_percent','purification_recovery_percent','crude_yield_percent') if k in records}
    report = {'source_rows':len(preview.raw),'accepted_rows':len(records),
              'excel_percent_conversion':bool(convert_excel_percent),
              'excluded_missing_sequence':len(preview.raw)-len(records),
              'possible_exact_duplicate_rows':duplicate_rows,
              'usable_targets':counts,'mapping':dict(mapping),
              'source_file':Path(preview.file_path).name,'source_sheet':preview.sheet,
              'source_file_sha256':preview.file_sha256,
              'warnings':list(preview.warnings)}
    for column, count in invalid_numbers.items():
        if count:
            report['warnings'].append(f'{count} non-empty {column} value(s) were invalid or had ambiguous decimal separators; check units and column mapping.')
    for column, count in invalid_outcomes.items():
        if count:
            report['warnings'].append(f'{count} non-empty {column} value(s) could not be interpreted as measured percentages (0–100); inspect invalid cells before training.')
    if duplicate_rows:
        report['warnings'].append(f'{duplicate_rows} exact duplicate row(s) detected. Confirm whether these are true replicate runs before training.')
    if 'product_path' not in records:
        report['warnings'].append('Product topology not mapped. ML is limited to legacy linear/deprotected outcomes; verify input types.')
    elif (records['product_path']=='UNRECOGNIZED').any():
        report['warnings'].append('Unrecognized product paths detected. These rows are excluded from linear ML training.')
    if not counts:
        report['warnings'].append('No outcome target mapped: cannot train supervised ML.')
    if counts and max(counts.values()) < MIN_TRAIN:
        report['warnings'].append(f'Fewer than {MIN_TRAIN} labeled rows: model training withheld; similar-run review remains available.')
    return records, report


def _atomic_json(path: Path, data: dict[str,Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.spps_ai_',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
            f.flush(); os.fsync(f.fileno())
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary): os.remove(temporary)


def _records_digest(records: list[dict[str, Any]]) -> str:
    return sha256(json.dumps(records,sort_keys=True,ensure_ascii=False,allow_nan=False).encode('utf-8')).hexdigest()


def save_reviewed_dataset(records: pd.DataFrame, report: dict[str,Any], source_digest: str, user_dir: str | Path) -> dict[str,Any]:
    """Explicitly approved only; copies normalized observations into a private local profile."""
    if records.empty: raise ValueError('No valid rows to store.')
    normalized_records=json.loads(records.where(pd.notna(records),None).to_json(orient='records',force_ascii=False))
    normalized_sha256=_records_digest(normalized_records)
    payload = {'schema':SCHEMA,'review_status':'IMPORTED_OPERATOR_REVIEWED_NOT_SOP',
               'source_sha256':source_digest,'dataset_sha256':normalized_sha256,
               'import_report':report,'records':normalized_records}
    root=Path(user_dir)
    active=root/'ai_excel_reviewed_v9.json'
    if active.is_symlink() or (root/'ai_excel_reviewed_v9.json.bak').is_symlink():
        raise ValueError('Dataset path cannot be a symlink.')
    if active.exists():
        # Validate prior bytes before rotating the last-good backup.
        _, old_payload=load_reviewed_dataset(root)
        _atomic_json(root/'ai_excel_reviewed_v9.json.bak',old_payload)
    _atomic_json(active,payload)
    return {'rows':len(records),'path':str(root/'ai_excel_reviewed_v9.json'),
            'sha256':_sha256_file(root/'ai_excel_reviewed_v9.json')}


def load_reviewed_dataset(user_dir: str | Path) -> tuple[pd.DataFrame, dict[str,Any]]:
    path=Path(user_dir)/'ai_excel_reviewed_v9.json'
    if not path.exists():
        raise ValueError('No reviewed Excel/CSV dataset. Import one first.')
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_DATASET_BYTES:
        raise ValueError('Reviewed dataset file is unsafe or oversized.')
    try:
        raw=json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Reviewed dataset cannot be read. Restore a backup or reimport.') from exc
    if not isinstance(raw, dict) or raw.get('schema') != SCHEMA or raw.get('review_status')!='IMPORTED_OPERATOR_REVIEWED_NOT_SOP':
        raise ValueError('Unsupported dataset schema or review status.')
    records=raw.get('records')
    if (not isinstance(records,list) or len(records)>MAX_ROWS
        or any(not isinstance(row,dict) for row in records)
        or _records_digest(records)!=raw.get('dataset_sha256')):
        raise ValueError('Reviewed dataset integrity mismatch. Reimport and review the source.')
    return pd.DataFrame(records),raw




def restore_last_good_dataset(user_dir: str | Path) -> dict[str, Any]:
    """Explicit rollback of the last validated reviewed dataset backup."""
    root=Path(user_dir)
    active=root/'ai_excel_reviewed_v9.json'
    backup=root/'ai_excel_reviewed_v9.json.bak'
    if active.is_symlink() or backup.is_symlink():
        raise ValueError('Dataset paths cannot be symlinks.')
    if not backup.is_file():
        raise ValueError('No last-good backup is available.')
    if backup.stat().st_size>MAX_DATASET_BYTES:
        raise ValueError('Reviewed dataset backup exceeds the safe size limit.')
    try:
        raw=json.loads(backup.read_text(encoding='utf-8'))
    except (OSError,UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError('Reviewed dataset backup is unreadable.') from exc
    records=raw.get('records') if isinstance(raw,dict) else None
    if (not isinstance(records,list) or len(records)>MAX_ROWS or
        not isinstance(raw,dict) or raw.get('schema')!=SCHEMA or
        raw.get('review_status')!='IMPORTED_OPERATOR_REVIEWED_NOT_SOP' or
        any(not isinstance(row,dict) for row in records) or
        _records_digest(records)!=raw.get('dataset_sha256')):
        raise ValueError('Reviewed dataset backup failed integrity checks.')
    _atomic_json(active,raw)
    return {'restored_rows':len(records),'dataset_sha256':raw['dataset_sha256']}


def audit_reviewed_data(records: pd.DataFrame) -> dict[str, Any]:
    """Read-only, machine-readable data quality report. Never modifies observations.

    A repeated Run ID can mean a duplicate import or contradictory measurements.
    Both cases require operator review; real replicate rows are *not* discarded.
    """
    if not isinstance(records, pd.DataFrame):
        raise ValueError('Expected a table of experiment records.')
    if len(records) > MAX_ROWS:
        raise ValueError(f'Combined dataset exceeds {MAX_ROWS} rows.')
    # Read-only audit: avoid copying up to 20,000 reviewed records.
    frame = records
    if 'sequence' not in frame.columns:
        raise ValueError('Sequence column is missing.')
    def blank(value):
        if value is None:
            return True
        try:
            if bool(pd.isna(value)):
                return True
        except (TypeError, ValueError):
            return False
        return str(value).strip() == ''
    invalid_sequence = []
    chemistry_annotated = []
    identities = []
    for index, seq in enumerate(frame['sequence']):
        if _requires_chemistry_aware_features(seq):
            chemistry_annotated.append(index + 1)
        try:
            if blank(seq):
                raise ValueError('Blank sequence')
            identities.append(_sequence_group(str(seq)))
        except (ValueError, TypeError, KeyError):
            invalid_sequence.append(index + 1)
    warnings=[]
    if invalid_sequence:
        warnings.append(f'{len(invalid_sequence)} sequence(s) cannot be parsed into validated ML features; training will be refused.')
    if chemistry_annotated:
        warnings.append(f'{len(chemistry_annotated)} protected/branched/terminally modified record(s) will not be used for linear ML; explicit chemistry features are required.')
    exact = int(frame.duplicated().sum())
    if exact:
        warnings.append(f'{exact} exactly repeated row(s) — do not treat as independent measurements without verifying replicates.')
    duplicate_ids=0; conflicts=0
    if 'run_id' in frame:
        seen={}
        cols=[key for key in ('sequence','actual_yield_percent','actual_purity_percent','scale_mmol','loading_mmol_g','resin','chemistry') if key in frame]
        # Match the old row.get() behavior without allocating a pandas Series
        # per experiment.  Retain the fallback for non-unique column labels.
        if frame.columns.is_unique:
            positions = {name: index for index, name in enumerate(frame.columns)}
            run_index = positions['run_id']
            stage_index = positions.get('reaction_step')
            signature_indices = [positions[key] for key in cols]
            for values in frame.itertuples(index=False, name=None):
                value = values[run_index]
                if blank(value):
                    continue
                stage_value = values[stage_index] if stage_index is not None else None
                stage = str(stage_value or '').strip().casefold()
                rid = (str(value).strip().casefold(), stage)
                signature = tuple(
                    None if blank(values[index]) else str(values[index]).strip().casefold()
                    for index in signature_indices
                )
                if rid in seen:
                    duplicate_ids += 1
                    if signature != seen[rid]:
                        conflicts += 1
                else:
                    seen[rid] = signature
        else:
            for _, row in frame.iterrows():
                value = row.get('run_id')
                if blank(value):
                    continue
                stage = str(row.get('reaction_step') or '').strip().casefold()
                rid = (str(value).strip().casefold(), stage)
                signature = tuple(None if blank(row.get(key)) else str(row.get(key)).strip().casefold() for key in cols)
                if rid in seen:
                    duplicate_ids += 1
                    if signature != seen[rid]:
                        conflicts += 1
                else:
                    seen[rid] = signature
        if duplicate_ids:
            warnings.append(f'{duplicate_ids} repeated experiment ID(s), including {conflicts} conflicting row(s). Verify before model training.')
    targets={}
    for key in ('actual_yield_percent','actual_purity_percent','coupling_conversion_percent','cyclization_yield_percent','purification_recovery_percent','crude_yield_percent','cleavage_recovery_percent'):
        if key in frame:
            good=sum(_percentage(v) is not None for v in frame[key])
            targets[key]={'valid_measured_rows':good,'missing_or_invalid_rows':len(frame)-good,
                'minimum_rows_met':good>=MIN_TRAIN}
    missing={key:int(sum(blank(v) for v in frame[key])) for key in ('scale_mmol','loading_mmol_g','resin','chemistry') if key in frame}
    product_paths={str(k):int(v) for k,v in frame['product_path'].value_counts(dropna=False).items()} if 'product_path' in frame else {'UNLABELED_LEGACY':len(frame)}
    return {'schema':'spps-v9-data-audit-v1','total_rows':len(frame),
            'unique_parseable_sequence_groups':len(set(identities)),
            'unparseable_sequence_rows':invalid_sequence[:25],
            'unparseable_sequence_count':len(invalid_sequence),
            'chemistry_annotated_sequence_count':len(chemistry_annotated),
            'exact_duplicate_rows':exact,'duplicate_run_ids':duplicate_ids,
            'conflicting_run_ids':conflicts,'target_quality':targets,
            'missing_fields':missing,'product_path_counts':product_paths,
            'training_blocked':bool(invalid_sequence or duplicate_ids or exact),
            'warnings':warnings}


def combine_reviewed_tables(*tables: pd.DataFrame) -> tuple[pd.DataFrame, dict[str,Any]]:
    """Combine already reviewed tables, retaining every row and missing-value marker.

    No numeric averaging, imputation, implicit deduplication or chemistry guess.
    """
    if not tables:
        raise ValueError('No reviewed files to combine.')
    if any(not isinstance(table,pd.DataFrame) for table in tables):
        raise ValueError('Each file must be an explicitly reviewed table.')
    frames=[table.copy() for table in tables if len(table)]
    if not frames:
        raise ValueError('All reviewed files are empty.')
    if any('sequence' not in table for table in frames):
        raise ValueError('Every reviewed file needs a Sequence column.')
    combined=pd.concat(frames,ignore_index=True,sort=False)
    if len(combined)>MAX_ROWS:
        raise ValueError(f'Maximum combined dataset size: {MAX_ROWS} rows.')
    return combined,audit_reviewed_data(combined)


def append_reviewed_dataset(records: pd.DataFrame, report: dict[str,Any],
                            source_digest: str, user_dir: str | Path) -> dict[str,Any]:
    """Append operator-reviewed files without silently deleting old records.

    Read and verify the previous dataset *before* attempting any write.
    Atomic replacement ensures that an error leaves the old dataset untouched.
    """
    root=Path(user_dir)
    previous=root/'ai_excel_reviewed_v9.json'
    if not previous.exists():
        return save_reviewed_dataset(records,report,source_digest,user_dir)
    earlier,meta=load_reviewed_dataset(root)
    merged,audit=combine_reviewed_tables(earlier,records)
    history=list(meta.get('import_report',{}).get('import_history',[]))
    history.append({'source_sha256':source_digest,'added_rows':len(records)})
    combined_report={**report,'merge_mode':'APPEND_KEEP_ALL',
         'prior_rows':len(earlier),'new_rows':len(records),
         'import_history':history[-100:],'quality_audit':audit}
    provenance_digest=sha256((str(meta.get('source_sha256',''))+'|'+str(source_digest)).encode('utf-8')).hexdigest()
    return save_reviewed_dataset(merged,combined_report,provenance_digest,user_dir)


# Avoid fabricating residues for an exact Fmoc-free / D-form protected bottle name.
_NATURAL_AA = frozenset('ARNDCQEGHILKMFPSTWYV')
_AA3 = {
    'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLN':'Q','GLU':'E',
    'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
    'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V',
}
_BOTTLE_TOKEN = re.compile(
    r'^(?:(?:FMOC|BOC|AC|H)-)(D-)?([A-Za-z]{3})(?:\([^)]*\))?-(?:OH|NH2)$', re.I
)
_D_3LETTER = re.compile(
    r'(?<![A-Za-z0-9])D-(' + '|'.join(_AA3) + r')(\([^()]*\))?(?![A-Za-z0-9])',re.I
)
_NONCANONICAL_TOKENS = frozenset({
    'AHX','CHA','AIB','NLE','ORN','CIT','HYP','DAB','NAL','BALA','GALA',
    'AEEA','PEG1','PEG2','PEG3','PEG4','PEG6','PEG8','PEG12','PEG24',
    'G4S','G4SX2','SMCC','SULFOSMCC','DSS',
})


@lru_cache(maxsize=4096)
def _cached_residue_identity(sequence: str) -> tuple[tuple[str, ...], int]:
    """Return explicit residue identities plus branch length for safe ML features.

    Unknown bottle identities are withheld instead of guessed from their first
    character (e.g. H-Ser(tBu)-OH is Ser, not His).
    """
    from spps_planner.parser import parse_sequence
    raw = str(sequence or '').strip()
    # The general parser currently splits D-Nle into D + Nle. A false
    # aspartate feature is worse than abstaining from an unsupported token.
    if re.search(r'(?<![A-Za-z0-9])D-(?:Nle|Orn|Aib|Hyp|Cit|Cha|Nal|Dab)(?=$|[-(])',raw,re.I):
        raise ValueError('D-form noncanonical residues require explicit validated descriptors before ML.')
    if not _BOTTLE_TOKEN.fullmatch(raw):
        # Preserve exact bracketed vendor tokens, which may contain D-Arg etc.
        pieces = re.split(r'(\[[^]]*\])',raw)
        for index in range(0,len(pieces),2):
            pieces[index] = _D_3LETTER.sub(
                lambda match: 'd' + _AA3[match.group(1).upper()] + (match.group(2) or ''),pieces[index]
            )
        raw = ''.join(pieces)
    bottle = _BOTTLE_TOKEN.fullmatch(raw)
    if bottle:
        tokens, branch_length = [raw], 0
    else:
        parsed = parse_sequence(raw)
        tokens, branch_length = list(parsed.core_tokens) + list(parsed.branch_tokens), len(parsed.branch_tokens)
    if not tokens:
        raise ValueError('Unrecognized peptide sequence.')
    identities = []
    for original in tokens:
        token = str(original).strip()
        if token.upper() in _NATURAL_AA and len(token) == 1:
            identities.append(token.upper())
        elif len(token) == 2 and token[0] == 'd' and token[1].upper() in _NATURAL_AA:
            identities.append('d' + token[1].upper())
        elif (m := _BOTTLE_TOKEN.fullmatch(token)) and m.group(2).upper() in _AA3:
            identity = _AA3[m.group(2).upper()]
            identities.append('d' + identity if m.group(1) else identity)
        elif re.fullmatch(r'[ARNDCQEGHILKMFPSTWYV]\([^()]*\)', token, re.I):
            identities.append(token[0].upper())
        elif token.upper() in _NONCANONICAL_TOKENS:
            identities.append('X:' + token.upper())
        else:
            raise ValueError(f'Unsupported residue identity for ML features: {token[:60]}')
    return tuple(identities), branch_length


def _residue_identity(sequence: str) -> tuple[list[str], int]:
    """Copy cached immutable identities to avoid external mutation of cached data."""
    identities, branch_length = _cached_residue_identity(str(sequence))
    return list(identities), branch_length


def _seq_features(sequence: str) -> dict[str,int]:
    try:
        residues, branch_length = _residue_identity(sequence)
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError(f'Unable to parse sequence for AI: {str(sequence)[:40]} ({exc})') from exc
    natural = [aa[-1] for aa in residues if len(aa) == 1 or (len(aa) == 2 and aa.startswith('d'))]
    return {
        'sequence_length':len(residues), 'cys_count':natural.count('C'),
        'asp_count':natural.count('D'), 'pro_count':natural.count('P'),
        'gly_count':natural.count('G'),
        'd_residue_count':sum(aa.startswith('d') for aa in residues),
        'noncanonical_count':sum(aa.startswith('X:') for aa in residues),
        'branch_residue_count':branch_length,
    }


def _sequence_group(sequence: str) -> str:
    """Group equivalent separator spellings to prevent holdout data leakage."""
    residues, branch_length = _residue_identity(sequence)
    return '|'.join(residues) + f'|branch:{branch_length}'


FEATURES=('sequence_length','cys_count','asp_count','pro_count','gly_count',
          'd_residue_count','noncanonical_count','branch_residue_count',
          'scale_mmol','loading_mmol_g','resin','chemistry')
CATEGORICAL=('resin','chemistry')
NUMERIC=tuple(c for c in FEATURES if c not in CATEGORICAL)


def _clean_category(value: Any) -> str:
    if value is None or (not isinstance(value,(list,tuple,dict)) and pd.isna(value)):
        return ''
    return str(value).strip()[:120]


def _features(frame: pd.DataFrame) -> pd.DataFrame:
    """Extract the same ML features without pandas Series allocations per row."""
    rows = []
    if frame.columns.is_unique:
        positions = {name: index for index, name in enumerate(frame.columns)}
        sequence_pos, scale_pos, loading_pos, resin_pos, chemistry_pos = (
            positions.get(name) for name in
            ('sequence', 'scale_mmol', 'loading_mmol_g', 'resin', 'chemistry')
        )
        for values in frame.itertuples(index=False, name=None):
            basic = _seq_features(str(values[sequence_pos] if sequence_pos is not None else ''))
            basic['scale_mmol'] = _positive_number(values[scale_pos] if scale_pos is not None else None, 'mmol')
            basic['loading_mmol_g'] = _positive_number(values[loading_pos] if loading_pos is not None else None, 'mmol/g')
            basic['resin'] = _clean_category(values[resin_pos] if resin_pos is not None else '')
            basic['chemistry'] = _clean_category(values[chemistry_pos] if chemistry_pos is not None else '')
            rows.append(basic)
    else:
        for _, entry in frame.iterrows():
            basic = _seq_features(str(entry.get('sequence', '')))
            basic['scale_mmol'] = _positive_number(entry.get('scale_mmol'), 'mmol')
            basic['loading_mmol_g'] = _positive_number(entry.get('loading_mmol_g'), 'mmol/g')
            basic['resin'] = _clean_category(entry.get('resin', ''))
            basic['chemistry'] = _clean_category(entry.get('chemistry', ''))
            rows.append(basic)
    return pd.DataFrame(rows, columns=FEATURES)


def _requires_chemistry_aware_features(sequence: Any) -> bool:
    """Do not treat annotated protection, branching or special termini as plain 1D sequence.

    Precise reaction topology/protecting-group state is *not* an input feature of
    the Excel RandomForest. Keep such records available for similarity and
    audit, but never fit/predict an unqualified linear model from them.
    """
    value=str(sequence or '')
    return any(c in value for c in ('(',')','[',']')) or bool(re.search(r'(?i)\b(?:Fmoc|Boc|Alloc|Ac|Biotin|FITC)[-_]',value))


def _labeled(frame: pd.DataFrame,target: str) -> pd.DataFrame:
    if target not in ('actual_yield_percent','actual_purity_percent'):
        raise ValueError('Only measured yield/purity % are supported.')
    if target not in frame:
        raise ValueError(f'Map measured {target} before training.')
    selected=frame.copy()
    if 'product_path' in selected:
        selected=selected[selected['product_path'].map(normalize_product_path).isin(('', 'linear_deprotected'))].copy()
    selected=selected[~selected['sequence'].map(_requires_chemistry_aware_features)].copy()
    selected[target] = selected[target].map(_percentage)
    return selected[selected[target].notna() & selected['sequence'].astype(bool)].reset_index(drop=True)


def ml_readiness_report(frame: pd.DataFrame) -> dict[str, Any]:
    """Read-only training readiness report for non-technical Excel users.

    This is a data-quality assessment, NOT model validation or permission to
    automatically adjust an experimental synthesis method.
    """
    audit = audit_reviewed_data(frame)
    targets: dict[str, Any] = {}
    for target in ('actual_yield_percent', 'actual_purity_percent'):
        if target not in frame:
            targets[target] = {'ready': False, 'reason': 'Map a measured outcome column first.'}
            continue
        labeled = _labeled(frame, target)
        reasons = []
        if audit['training_blocked']:
            reasons.append('Resolve repeated rows, duplicate Run IDs, and unparseable sequences before training.')
        if len(labeled) < MIN_TRAIN:
            reasons.append(f'Need {MIN_TRAIN} valid measured rows; currently {len(labeled)}.')
        try:
            groups = int(labeled['sequence'].map(_sequence_group).nunique())
        except (ValueError, TypeError, KeyError):
            groups = 0
            reasons.append('Resolve unrecognized amino acid sequence notation.')
        if groups < MIN_SEQUENCE_GROUPS:
            reasons.append(f'Need {MIN_SEQUENCE_GROUPS} distinct sequence groups; currently {groups}.')
        if labeled[target].nunique() < 3:
            reasons.append('Need at least three different measured target values.')
        for col in ('scale_mmol', 'loading_mmol_g'):
            valid = sum(_positive_number(v, 'mmol' if col == 'scale_mmol' else 'mmol/g') is not None
                        for v in labeled[col]) if col in labeled else 0
            if valid < max(5, len(labeled)//3):
                reasons.append(f'More positive {col} values must be entered; currently {valid}.')
        targets[target] = {'ready': not reasons, 'measured_rows': len(labeled),
                           'unique_sequence_groups': groups, 'reasons': reasons}
    return {'schema': 'spps-v9-ml-readiness-v1', 'quality_audit': audit,
            'targets': targets, 'meaning': 'Readiness does not prove prediction accuracy or chemical feasibility.'}


def train_local_advisor(frame: pd.DataFrame,target: str,user_dir: str | Path,source_digest: str) -> dict[str,Any]:
    """Experimental Random Forest, grouped by peptide identity; never changes a Plan."""
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import mean_absolute_error
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.inspection import permutation_importance
    import numpy as np
    from suite_gui.ai_safe_forest_v9 import export_forest

    quality=audit_reviewed_data(frame)
    if quality['training_blocked']:
        raise ValueError('Data quality check blocked model training: '
                         + '; '.join(quality['warnings'])[:350])
    labeled=_labeled(frame,target)
    excluded_non_linear=int(len(frame)-len(labeled)) if 'product_path' in frame else 0
    groups=labeled['sequence'].map(_sequence_group)
    if len(labeled)<MIN_TRAIN or groups.nunique()<MIN_SEQUENCE_GROUPS:
        raise ValueError(f'Need >= {MIN_TRAIN} measured outcomes from >= {MIN_SEQUENCE_GROUPS} distinct sequences. Current: {len(labeled)} rows / {groups.nunique()} sequences.')
    if labeled[target].nunique()<3:
        raise ValueError('Outcome values are too uniform for supervised regression.')
    features=_features(labeled)
    if len(features)!=len(labeled):raise ValueError('Feature alignment error.')
    data=features.copy()
    data[list(NUMERIC)]=data[list(NUMERIC)].apply(pd.to_numeric,errors='coerce')
    # All-empty columns are filled with known safe defaults, not unseen measurements.
    for col in ('scale_mmol','loading_mmol_g'):
        if data[col].notna().sum() < max(5, len(data)//3):
            raise ValueError(f'Too few usable {col} values for meaningful training.')
    if any((data[col].dropna()<=0).any() for col in ('scale_mmol','loading_mmol_g')):
        raise ValueError('Scale and loading must be positive.')
    y=labeled[target].astype(float)
    def new_pipeline():
        return Pipeline([
            ('prep',ColumnTransformer([
                ('num',SimpleImputer(strategy='median'),list(NUMERIC)),
                ('cat',Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='Unknown')),
                    ('ohe',OneHotEncoder(handle_unknown='ignore'))]),list(CATEGORICAL)),
            ])),
            ('model',RandomForestRegressor(n_estimators=140,min_samples_leaf=2,random_state=42,n_jobs=1)),
        ])

    # Repeat grouped holdout rather than treating a fortunate single split as validation.
    splitter=GroupShuffleSplit(n_splits=3,test_size=0.25,random_state=42)
    split_results=[]
    holdout_abs_errors=[]
    explanations=[]
    for split_no, (idx_train,idx_test) in enumerate(splitter.split(data,y,groups=groups)):
        candidate=new_pipeline()
        candidate.fit(data.iloc[idx_train],y.iloc[idx_train])
        predicted=candidate.predict(data.iloc[idx_test])
        test_mae=float(mean_absolute_error(y.iloc[idx_test],predicted))
        baseline_mae=float(mean_absolute_error(
            y.iloc[idx_test],[float(y.iloc[idx_train].median())]*len(idx_test)))
        split_results.append((test_mae,baseline_mae,len(idx_test),int(groups.iloc[idx_test].nunique())))
        holdout_abs_errors.extend(abs(float(actual)-float(pred)) for actual,pred in zip(y.iloc[idx_test],predicted))
        if split_no == 0:
            importance=permutation_importance(candidate,data.iloc[idx_test],y.iloc[idx_test],
                        scoring='neg_mean_absolute_error',n_repeats=2,random_state=42,n_jobs=1)
            explanations=[{'feature':key,'mean_increase_in_mae_points':round(float(importance.importances_mean[i]),3)}
                          for i,key in enumerate(FEATURES) if math.isfinite(float(importance.importances_mean[i]))]
            explanations=sorted(explanations,key=lambda item:-item['mean_increase_in_mae_points'])[:5]
    mae=sum(x[0] for x in split_results)/len(split_results)
    baseline=sum(x[1] for x in split_results)/len(split_results)
    wins=sum(x[0] < x[1] for x in split_results)
    # Descriptive repeat-heldout residual quantiles, NOT calibrated prediction intervals.
    # The same peptide group can recur across different holdouts, so never claim
    # distribution-free coverage or a per-sequence confidence level.
    empirical_errors={str(int(q*100)):round(float(np.quantile(holdout_abs_errors,q)),3)
                      for q in (0.8,0.9)}
    # At least 2/3 of the independent held-out group partitions must beat baseline.
    if baseline <= 0 or mae >= baseline or wins < 2:
        root=Path(user_dir);root.mkdir(parents=True,exist_ok=True)
        name='ai_excel_yield_v9' if target=='actual_yield_percent' else 'ai_excel_purity_v9'
        # Explicitly revoke any older model approval on a failed retraining.
        _atomic_json(root/(name+'.json'),{'schema':SCHEMA,'status':'WITHHELD_UNRELIABLE',
                     'target':target,'dataset_sha256':source_digest})
        return {'status':'WITHHELD_UNRELIABLE','rows':len(labeled),'sequence_groups':int(groups.nunique()),
                'holdout_mae_percent_points':round(mae,3),'baseline_mae_percent_points':round(baseline,3),
                'validation_splits':3,'splits_better_than_baseline':wins,
                'reason':'Insufficient gain over a median baseline across grouped holdouts. Model disabled.'}
    pipeline=new_pipeline()
    pipeline.fit(data,y)
    root=Path(user_dir);root.mkdir(parents=True,exist_ok=True)
    stem='ai_excel_yield_v9' if target=='actual_yield_percent' else 'ai_excel_purity_v9'
    model_name=stem+'.forest.json'
    from suite_gui.ai_safe_forest_v9 import FORMAT as SAFE_FOREST_FORMAT
    safe_model=export_forest(pipeline,NUMERIC,CATEGORICAL)
    target_file=root/model_name
    _atomic_json(target_file,safe_model)
    metadata={'schema':SCHEMA,'status':'EXPERIMENTAL_REVIEW_ONLY', 'target':target,
              'model_format':SAFE_FOREST_FORMAT,
              'model_sha256':_sha256_file(target_file),
              'model_file':model_name,'dataset_sha256':source_digest,
              'rows':len(labeled),'excluded_unusable_or_other_path_rows':excluded_non_linear,
              'sequence_groups':int(groups.nunique()),
              'holdout_rows':round(sum(x[2] for x in split_results)/len(split_results)),
              'holdout_groups':round(sum(x[3] for x in split_results)/len(split_results)),
              'validation_splits':3,'splits_better_than_baseline':wins,
              'holdout_mae_percent_points':round(mae,3),
              'baseline_mae_percent_points':round(baseline,3),
              'descriptive_holdout_abs_error_quantiles_points':empirical_errors,
              'holdout_feature_importance':explanations,
              'feature_schema':list(FEATURES),
              'observed_lengths':[int(data['sequence_length'].min()),int(data['sequence_length'].max())],
              'observed_scale_mmol':[float(data['scale_mmol'].min()),float(data['scale_mmol'].max())],
              'observed_loading_mmol_g':[float(data['loading_mmol_g'].min()),float(data['loading_mmol_g'].max())],
              **{'observed_'+key:sorted(set(int(v) for v in data[key])) for key in ('d_residue_count','noncanonical_count','branch_residue_count')},
              'observed_residue_vocab':sorted({token for seq in labeled['sequence'] for token in _residue_identity(seq)[0]}),
              'observed_resins':sorted(set(data['resin'])),
              'observed_chemistry':sorted(set(data['chemistry'])),
              'notes':('Three grouped holdouts; error quantiles and feature importance are descriptive and '
                       'not calibrated intervals, causal relationships, or validated predictive accuracy.')}
    _atomic_json(root/(stem+'.json'),metadata)
    return metadata


def _residue_edit_distance(left: list[str], right: list[str]) -> int:
    """Exact Levenshtein distance for chemically distinct residue tokens.

    Skip identical termini before dynamic programming. This preserves the
    exact result but avoids comparing long common segments in similar runs.
    """
    if len(left) > 128 or len(right) > 128:
        raise ValueError('Sequence is too long for trustworthy local similarity review.')
    if left == right:
        return 0
    common = 0
    limit = min(len(left), len(right))
    while common < limit and left[common] == right[common]:
        common += 1
    left = left[common:]
    right = right[common:]
    while left and right and left[-1] == right[-1]:
        left.pop()
        right.pop()
    if not left:
        return len(right)
    if not right:
        return len(left)
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, aa in enumerate(left, 1):
        current = [i]
        for j, bb in enumerate(right, 1):
            current.append(min(current[j-1] + 1, previous[j] + 1,
                               previous[j-1] + (aa != bb)))
        previous = current
    return previous[-1]


def similar_runs(frame: pd.DataFrame, context: dict[str, Any], top_k: int = 3) -> list[dict[str, Any]]:
    """Review nearby experiments without changing the original screening order.

    Stream candidates through a bounded top-candidate heap rather than
    retaining all eligible rows. Distances, screening and tie order stay the
    same as the reviewed implementation.
    """
    try:
        wanted, wanted_branch = _residue_identity(str(context['sequence']))
        if len(wanted) > 128:
            return []
    except (ValueError, KeyError, TypeError):
        return []
    wanted_counts = Counter(wanted)
    top_k = max(0, min(20, int(top_k)))
    if not top_k:
        return []
    columns = tuple(frame.columns)
    positions = {column: i for i, column in enumerate(columns)}
    sequence_pos = positions.get('sequence')
    resin_pos = positions.get('resin')
    chemistry_pos = positions.get('chemistry')
    product_pos = positions.get('product_path')
    yield_pos = positions.get('actual_yield_percent')
    purity_pos = positions.get('actual_purity_percent')
    desired_path = normalize_product_path(context.get('product_path', 'linear_deprotected'))
    wanted_conditions = {key: _clean_category(context.get(key, '')).casefold()
                         for key in ('resin', 'chemistry')}
    # Select the same approximate top candidates in input order, but do not
    # retain every eligible experiment in memory. heapq.nsmallest
    # preserves input ordering for ties, including duplicate runs.
    def candidate_stream():
        for values in frame.itertuples(index=False, name=None):
            if product_pos is not None:
                observed_path = normalize_product_path(values[product_pos])
                if desired_path == 'linear_deprotected' and observed_path not in ('', 'linear_deprotected'):
                    continue
                if desired_path != 'linear_deprotected' and observed_path != desired_path:
                    continue
            elif desired_path != 'linear_deprotected':
                continue
            try:
                if sequence_pos is None:
                    continue
                sequence = str(values[sequence_pos])
                got, got_branch = _residue_identity(sequence)
                if len(got) > 128:
                    continue
                outcome = {
                    'actual_yield_percent': _percentage(values[yield_pos]) if yield_pos is not None else None,
                    'actual_purity_percent': _percentage(values[purity_pos]) if purity_pos is not None else None,
                }
                if all(value is None for value in outcome.values()):
                    continue
            except (ValueError, TypeError, KeyError):
                continue
            branch_penalty = 5 if wanted_branch != got_branch else 0
            resin = values[resin_pos] if resin_pos is not None else ''
            chemistry = values[chemistry_pos] if chemistry_pos is not None else ''
            conditions = {
                'resin': bool(wanted_conditions['resin'] and
                              _clean_category(resin).casefold() == wanted_conditions['resin']),
                'chemistry': bool(wanted_conditions['chemistry'] and
                                  _clean_category(chemistry).casefold() == wanted_conditions['chemistry']),
            }
            condition_penalty = 5 * sum(not matched for matched in conditions.values())
            counts = Counter(got)
            composition_delta = sum(abs(wanted_counts[k] - counts[k]) for k in wanted_counts.keys() | counts.keys())
            lower_bound = max(abs(len(wanted) - len(got)), (composition_delta + 1) // 2)
            yield (2 * lower_bound + branch_penalty + condition_penalty,
                               sequence, got, branch_penalty, condition_penalty,
                               conditions, outcome, str(resin)[:80], str(chemistry)[:80])
    pool = nsmallest(max(128, top_k * 64), candidate_stream(),
                     key=lambda x: (x[0], x[1]))
    output = []
    for _, sequence, got, branch_penalty, condition_penalty, conditions, outcome, resin, chemistry in pool:
        edits = _residue_edit_distance(wanted, got)
        score = 2 * edits + branch_penalty + condition_penalty
        output.append({'sequence': sequence[:80], 'distance': float(score),
            'residue_edits': int(edits),
            'exact_residue_identity': bool(edits == 0 and branch_penalty == 0),
            'conditions_match': conditions,
            'resin': resin, 'chemistry': chemistry, **outcome,
            'screening': 'APPROXIMATE_TOP_CANDIDATES',
            'note': 'Descriptive sequence/condition match; not validated chemical or yield similarity.'})
    return sorted(output, key=lambda x: (x['distance'], x['residue_edits'], x['sequence']))[:top_k]


def advise_from_local_data(context: dict[str,Any], data_dir: str | Path,model_dir: str | Path,
                           target: str='actual_yield_percent') -> dict[str,Any]:
    """Read only user-reviewed local data / locally-trained model, never external pickle."""
    try: frame, dataset=load_reviewed_dataset(data_dir)
    except ValueError as exc:
        return {'status':'NO_REVIEWED_DATA','reason':str(exc),'similar_runs':[]}
    if target not in ('actual_yield_percent','actual_purity_percent'):
        raise ValueError('Unknown AI outcome target.')
    result={'status':'SIMILAR_EXPERIMENTS_ONLY','similar_runs':similar_runs(frame,context),
            'dataset_rows':len(frame),'dataset_sha256':dataset.get('dataset_sha256'),
            'target':target,'prediction':None,
            'meaning':'Observed cases are not validated optimal conditions.'}
    # The imported training schema does not represent precise protected bonds/branch topology.
    # A model trained from untyped outcomes must not predict cyclic/protected yield.
    path = str(context.get('product_path','linear_deprotected') or 'linear_deprotected')
    if path != 'linear_deprotected':
        result.update(status='TOPOLOGY_NOT_MODELED',prediction=None,
                      reason='Imported outcome rows do not identify this protected/cyclic product pathway. Prediction withheld.')
        return result
    if _requires_chemistry_aware_features(context.get('sequence','')):
        result.update(status='CHEMISTRY_NOT_MODELED',prediction=None,
                      reason='Protected, branched or terminally modified sequence requires chemical-state features not represented in this ML model. Prediction withheld.')
        return result
    basename='ai_excel_yield_v9' if target=='actual_yield_percent' else 'ai_excel_purity_v9'
    meta_file=Path(model_dir)/(basename+'.json')
    model_file=Path(model_dir)/(basename+'.forest.json')
    if meta_file.exists() and not model_file.exists() and (Path(model_dir)/(basename+'.joblib')).exists():
        result.update(status='MODEL_SCHEMA_OUTDATED',reason='Older joblib models are never loaded by Excel AI. Retrain locally to export JSON.')
        return result
    if not (meta_file.exists() and model_file.exists()):return result
    if meta_file.is_symlink() or meta_file.stat().st_size > 2 * 1024 * 1024:
        return {**result,'status':'MODEL_METADATA_INVALID','reason':'Model metadata is a symlink or oversized.'}
    try:
        meta=json.loads(meta_file.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError):
        result.update(status='MODEL_METADATA_INVALID',reason='Model metadata is unreadable; retrain locally.')
        return result
    if not isinstance(meta,dict):
        result.update(status='MODEL_METADATA_INVALID',reason='Model metadata is invalid; retrain locally.')
        return result
    if (meta.get('schema')!=SCHEMA or meta.get('status')!='EXPERIMENTAL_REVIEW_ONLY' or meta.get('target')!=target):return result
    if meta.get('dataset_sha256')!=dataset.get('dataset_sha256'):return result
    from suite_gui.ai_safe_forest_v9 import FORMAT as SAFE_FOREST_FORMAT, load_verified_forest, predict_forest
    if meta.get('model_format') != SAFE_FOREST_FORMAT or meta.get('model_file') != basename+'.forest.json':
        result.update(status='MODEL_SCHEMA_OUTDATED',reason='Older executable model formats are not loaded. Retrain locally to use safe JSON inference.')
        return result
    if meta.get('feature_schema')!=list(FEATURES):
        result.update(status='MODEL_SCHEMA_OUTDATED',reason='Feature definitions changed; retrain the local model.')
        return result
    feature=_features(pd.DataFrame([context]))
    if not len(feature):return result
    seq_len=int(feature['sequence_length'].iloc[0])
    scale_value=_positive_number(context.get('scale_mmol'),'mmol')
    loading_value=_positive_number(context.get('loading_mmol_g'),'mmol/g')
    if (seq_len < meta['observed_lengths'][0] or seq_len>meta['observed_lengths'][1]
        or scale_value is None or not meta['observed_scale_mmol'][0]<=scale_value<=meta['observed_scale_mmol'][1]
        or loading_value is None or not meta['observed_loading_mmol_g'][0]<=loading_value<=meta['observed_loading_mmol_g'][1]
        or str(context.get('resin','')) not in meta['observed_resins']
        or str(context.get('chemistry','')) not in meta['observed_chemistry']
        or any(not meta.get('observed_'+k) or int(feature[k].iloc[0]) not in meta['observed_'+k]
               for k in ('d_residue_count','noncanonical_count','branch_residue_count'))):
        result['status']='OUT_OF_DISTRIBUTION'
        result['reason']='Current sequence length, scale, loading, resin or coupling is outside training examples. Prediction withheld.'
        return result
    try:
        vocabulary={str(x) for x in meta['observed_residue_vocab']}
        query_residues=_residue_identity(str(context.get('sequence','')))[0]
        if not set(query_residues).issubset(vocabulary):
            result.update(status='OUT_OF_DISTRIBUTION',
                          reason='Current sequence contains residue identities absent from training experiments. Prediction withheld.')
            return result
    except (ValueError,KeyError,TypeError):
        result.update(status='MODEL_SCHEMA_OUTDATED',reason='Residue vocabulary unavailable; retrain locally.')
        return result
    # Read bounded data-only JSON. Never deserialize external or locally tampered pickle/joblib.
    if (model_file.is_symlink() or meta_file.is_symlink()
        or model_file.stat().st_size > 80 * 1024 * 1024):
        result.update(status='MODEL_INTEGRITY_MISMATCH',reason='Model path is a symlink or file exceeds size limit.')
        return result
    try:
        raw_model=load_verified_forest(model_file,meta.get('model_sha256',''))
        predicted=float(predict_forest(raw_model,feature.iloc[0].to_dict(),validated=True))
    except ValueError as exc:
        if 'checksum mismatch' in str(exc):
            result.update(status='MODEL_INTEGRITY_MISMATCH',reason='Local model file checksum changed. Do not load an external model.')
        else:
            result.update(status='MODEL_UNREADABLE',reason=f'Local safe model invalid; retrain: {type(exc).__name__}')
        return result
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, KeyError, IndexError) as exc:
        result.update(status='MODEL_UNREADABLE',reason=f'Local safe model unreadable; retrain: {type(exc).__name__}')
        return result
    quantiles=meta.get('descriptive_holdout_abs_error_quantiles_points') or {}
    q80=quantiles.get('80')
    interval=None
    if isinstance(q80,(float,int)) and math.isfinite(q80) and q80>=0:
        interval=[round(max(0.,predicted-float(q80)),2),round(min(100.,predicted+float(q80)),2)]
    result.update(status='EXPERIMENTAL_PREDICTION_REVIEW_ONLY', prediction=round(min(100.,max(0.,predicted)),2),
                  descriptive_error_band_80=interval,
                  error_band_meaning='Heuristic based on repeated grouped-holdout errors; NOT a calibrated prediction interval or coverage guarantee.',
                  holdout_feature_importance=meta.get('holdout_feature_importance',[]),
                  holdout_mae_percent_points=meta['holdout_mae_percent_points'],
                  baseline_mae_percent_points=meta.get('baseline_mae_percent_points'),
                  training_rows=meta['rows'],sequence_groups=meta['sequence_groups'],
                  model_format=SAFE_FOREST_FORMAT,
                  meaning='Exploratory local ML estimate. Not a guaranteed synthesis yield or approved protocol.')
    return result


def create_process_excel_template(path: str | Path) -> Path:
    """Optional operator-filled process data workbook; no synthetic observations."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    dest=Path(path)
    if dest.suffix.lower()!='.xlsx' or dest.is_symlink():
        raise ValueError('Choose a new .xlsx path (not a symlink).')
    headers=['Sequence','Run ID','Product path','Reaction step','Reaction method',
             'Cleavage method','Scale (mmol)','Loading (mmol/g)','Resin',
             'Coupling','Reaction time (h)','Reaction concentration (mM)',
             'Coupling conversion %','Cyclization yield %','Crude yield %',
             'Purification recovery %','Actual yield %','Purity %',
             'Cleavage recovery %','Protecting groups','HPLC method','Observed m/z']
    book=Workbook();ws=book.active;ws.title='Process_Runs';ws.append(headers)
    ws.freeze_panes='A2';ws.auto_filter.ref='A1:V1'
    for cell in ws[1]:
        cell.fill=PatternFill('solid',fgColor='17365D');cell.font=Font(color='FFFFFF',bold=True)
        ws.column_dimensions[cell.column_letter].width=23
    product=DataValidation(type='list',formula1='"'+','.join(PRODUCT_PATHS)+'"',allow_blank=True)
    stage=DataValidation(type='list',formula1='"coupling,cyclization,cleavage,crude,purification,final"',allow_blank=True)
    ws.add_data_validation(product);product.add('C2:C5000')
    ws.add_data_validation(stage);stage.add('D2:D5000')
    guide=book.create_sheet('GUIDE')
    guide.append(['RULE','EXPLANATION'])
    for row in [
        ('Real observations only','Never enter predictions, simulated rows or planned recoveries as measurements.'),
        ('One Run ID per real run','Avoid conflicting experiment identifiers; do not combine yields from unrelated stages.'),
        ('Stage-specific yield','Enter corresponding reaction stage, product pathway and method for every outcome.'),
        ('Chemistry annotations','Preserve full protected/branched sequence. Unsupported structures will be withheld from ML.'),
        ('All percentages','Use measured 0–100% values. Empty cells mean unknown, not zero.'),
        ('No automatic SOP','Data and ML suggestions do not authorize a laboratory reaction.'),
        ('Protection profile','For protected products specify positions/groups, e.g. 1:S(tBu);3:S(tBu). Record observed chemistry only.')]:
        guide.append(row)
    guide.column_dimensions['A'].width=32;guide.column_dimensions['B'].width=94
    dest.parent.mkdir(parents=True,exist_ok=True)
    book.save(dest)
    return dest
