"""V9 AI assistant correctness & integrity regressions; no laboratory claim."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pandas as pd
import pytest

from suite_gui.ai_excel_core_v9 import (
    _seq_features, _sequence_group, _features, preview_file, verify_preview_source,
    normalize_preview, load_reviewed_dataset, save_reviewed_dataset,
    train_local_advisor, advise_from_local_data, MAX_XLSX_UNCOMPRESSED,
)


@pytest.mark.parametrize(('sequence','length','asp','d_count','modified','branch'),[
    ('H-Ser(tBu)-OH',1,0,0,0,0),
    ('H-D-Ser(tBu)-OH',1,0,1,0,0),
    ('Fmoc-D-Arg(Pbf)-OH',1,0,1,0,0),
    ('[Fmoc-D-Arg(Pbf)-OH]',1,0,1,0,0),
    ('D-Ser(tBu)-D-Val',2,0,2,0,0),
    ('Nle-Orn-Aib',3,0,0,3,0),
    ('K(GGEP)',5,0,0,0,4),
    ('dS-dV-dS',3,0,3,0,0),
])
def test_exact_identity_not_first_letter(sequence,length,asp,d_count,modified,branch):
    features=_seq_features(sequence)
    assert features['sequence_length']==length
    assert features['asp_count']==asp
    assert features['d_residue_count']==d_count
    assert features['noncanonical_count']==modified
    assert features['branch_residue_count']==branch


def test_canonical_groups_and_distinct_stereochemistry():
    assert _sequence_group('ACD')==_sequence_group('A-C-D')
    assert _sequence_group('D-Ala')==_sequence_group('dA')
    assert _sequence_group('H-Ser(tBu)-OH')==_sequence_group('S')
    assert _sequence_group('dS') != _sequence_group('S')
    assert _sequence_group('K(GGEP)') != _sequence_group('KGGEP')


def test_unknown_vendor_identity_fails_closed():
    with pytest.raises(ValueError,match='Unsupported residue identity'):
        _seq_features('[Abc-Unknown-OH]')


def test_non_string_categories_do_not_become_nan_labels():
    frame=pd.DataFrame([{'sequence':'ACD','resin':float('nan'),'chemistry':None,
                         'scale_mmol':0.1,'loading_mmol_g':0.6}])
    features=_features(frame)
    assert features['resin'].iloc[0]==''
    assert features['chemistry'].iloc[0]==''


def test_file_changed_between_preview_and_review_rejected(tmp_path):
    path=tmp_path/'records.csv'
    path.write_text('Sequence,Yield %\nACD,60\n',encoding='utf-8')
    preview=preview_file(path)
    verify_preview_source(preview)
    path.write_text('Sequence,Yield %\nACD,80\n',encoding='utf-8')
    with pytest.raises(ValueError,match='changed after preview'):
        verify_preview_source(preview)


def test_oversized_xlsx_archive_blocked_before_parser(tmp_path):
    path=tmp_path/'zipbomb.xlsx'
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('xl/worksheets/sheet1.xml','A'*(MAX_XLSX_UNCOMPRESSED + 1))
    with pytest.raises(ValueError,match='oversized'):
        preview_file(path)


def test_reviewed_dataset_tampering_rejected(tmp_path):
    records=pd.DataFrame([{'sequence':'ACD','actual_yield_percent':60.0}])
    save_reviewed_dataset(records,{},'original-file-hash',tmp_path)
    frame,meta=load_reviewed_dataset(tmp_path)
    assert len(frame)==1
    path=tmp_path/'ai_excel_reviewed_v9.json'
    doc=json.loads(path.read_text(encoding='utf-8'))
    doc['records'][0]['actual_yield_percent']=99.0
    path.write_text(json.dumps(doc,ensure_ascii=False),encoding='utf-8')
    with pytest.raises(ValueError,match='integrity mismatch'):
        load_reviewed_dataset(tmp_path)
    result=advise_from_local_data({'sequence':'ACD'},tmp_path,tmp_path/'models')
    assert result['status']=='NO_REVIEWED_DATA'


def _training_frame():
    return pd.DataFrame([{'sequence':'A'*(i+5),'actual_yield_percent':30+i*.7,
        'scale_mmol':0.15+(i%3)*0.02,'loading_mmol_g':0.734,
        'resin':'2-CTC','chemistry':'DIC/HOBt'} for i in range(40)])


def test_grouped_three_splits_or_safe_withholding(tmp_path):
    folder=tmp_path/'dataset'; models=tmp_path/'models'
    save_reviewed_dataset(_training_frame(),{},'x',folder)
    data,meta=load_reviewed_dataset(folder)
    result=train_local_advisor(data,'actual_yield_percent',models,meta['dataset_sha256'])
    assert result['status'] in ('WITHHELD_UNRELIABLE','EXPERIMENTAL_REVIEW_ONLY')
    if result['status']=='EXPERIMENTAL_REVIEW_ONLY':
        assert result['validation_splits']==3
        assert result['splits_better_than_baseline']>=2
        reviewed=advise_from_local_data(dict(sequence='A'*18,scale_mmol=.15,
            loading_mmol_g=.734,resin='2-CTC',chemistry='DIC/HobT'),folder,models)
        assert reviewed['status'] in ('OUT_OF_DISTRIBUTION','EXPERIMENTAL_PREDICTION_REVIEW_ONLY')
        meta_path=models/'ai_excel_yield_v9.json'
        model_meta=json.loads(meta_path.read_text(encoding='utf-8'))
        model_meta['feature_schema']=['obsolete_feature']
        meta_path.write_text(json.dumps(model_meta),encoding='utf-8')
        out=advise_from_local_data(dict(sequence='A'*18,scale_mmol=.15,
            loading_mmol_g=.734,resin='2-CTC',chemistry='DIC/HobT'),folder,models)
        assert out['status'] in ('OUT_OF_DISTRIBUTION','MODEL_SCHEMA_OUTDATED')


def test_corrupt_local_model_metadata_is_nonfatal(tmp_path):
    from suite_gui.ai_excel_core_v9 import SCHEMA
    data=tmp_path/'data'; models=tmp_path/'models'
    save_reviewed_dataset(pd.DataFrame([{'sequence':'ACD','actual_yield_percent':50.0}]),{},'x',data)
    models.mkdir()
    (models/'ai_excel_yield_v9.forest.json').write_bytes(b'test content')
    (models/'ai_excel_yield_v9.json').write_text('{bad json',encoding='utf-8')
    result=advise_from_local_data({'sequence':'ACD'},data,models)
    assert result['status']=='MODEL_METADATA_INVALID'


def test_bad_target_rejected(tmp_path):
    save_reviewed_dataset(pd.DataFrame([{'sequence':'ACD','actual_yield_percent':50.0}]),{},'x',tmp_path)
    with pytest.raises(ValueError,match='Unknown AI outcome'):
        advise_from_local_data({'sequence':'ACD'},tmp_path,tmp_path/'models',target='conversion')


def test_d_noncanonical_not_silently_counted_as_aspartate():
    with pytest.raises(ValueError,match='noncanonical'):
        _seq_features('D-Nle-V')


def test_exact_duplicates_are_flagged_not_deleted(tmp_path):
    source=tmp_path/'dupes.csv'
    source.write_text('Sequence,Yield %,Resin\nACD,44,CTC\nACD,44,CTC\n',encoding='utf-8')
    records,report=normalize_preview(preview_file(source))
    assert len(records)==2
    assert report['possible_exact_duplicate_rows']==1
    assert any('duplicate' in warning for warning in report['warnings'])


def test_header_mapping_priority_remains_stable_for_duplicate_and_unknown_columns():
    from suite_gui.ai_excel_core_v9 import auto_mapping, _header_score
    columns = ['Ignore', 'Sequence', 'sequence', 'Yield (%)', '실험번호', 'Actual yield %', 'NHS']
    mapping = auto_mapping(columns)
    assert mapping['sequence'] == 'Sequence'
    assert mapping['actual_yield_percent'] == 'Yield (%)'
    assert mapping['run_id'] == '실험번호'
    assert _header_score(columns) >= 7


def test_discovery_fallback_keeps_likeliest_visible_sheet(tmp_path):
    from openpyxl import Workbook
    from suite_gui.ai_excel_core_v9 import discover_import_sources
    workbook = Workbook()
    guide = workbook.active
    guide.title = 'GUIDE'
    guide.append(['How to use', 'A', 'B'])
    data = workbook.create_sheet('Samples')
    data.append(['Sequence', 'Comments'])
    data.append(['ACD', 'No measured outcome'])
    path = tmp_path / 'no_outcome.xlsx'
    workbook.save(path)
    queued, notices = discover_import_sources([path])
    assert queued == [(str(path), 'Samples')]
    assert any('manual mapping' in notice for notice in notices)
