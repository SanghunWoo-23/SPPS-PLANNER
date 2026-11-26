"""V9 AI/ML evolution: data-only inference, evidence, topology and template contracts."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from suite_gui.ai_excel_core_v9 import (
    _features, _labeled, NUMERIC, CATEGORICAL,
    audit_reviewed_data, create_blank_excel_template, load_reviewed_dataset,
    ml_readiness_report, normalize_preview, preview_file, save_reviewed_dataset,
    similar_runs, train_local_advisor, advise_from_local_data,
)
from suite_gui.ai_safe_forest_v9 import export_forest, validate_forest, predict_forest


def sample_runs(n=64):
    return pd.DataFrame([dict(sequence='A'*(i+5), actual_yield_percent=min(95.,20+i*.9),
           actual_purity_percent=min(99.,70+i*.3), scale_mmol=.1 + (i%3)*.05,
           loading_mmol_g=.734, resin='2-CTC',chemistry='DIC/HOBt',run_id=f'RUN{i:03d}')
          for i in range(n)])


def train_with_metadata(tmp_path, rows=64):
    data_dir=tmp_path/'data'
    model_dir=tmp_path/'models'
    frame=sample_runs(rows)
    save_reviewed_dataset(frame,{'reviewed':True},'workbook',data_dir)
    loaded,metadata=load_reviewed_dataset(data_dir)
    output=train_local_advisor(loaded,'actual_yield_percent',model_dir,metadata['dataset_sha256'])
    return loaded,data_dir,model_dir,output


def test_safe_forest_matches_original_pipeline_inference(tmp_path):
    from sklearn.compose import ColumnTransformer
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    frame=sample_runs(45)
    x=_features(frame)
    pipe=Pipeline([('prep',ColumnTransformer([
        ('num',SimpleImputer(strategy='median'),list(NUMERIC)),
        ('cat',Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='Unknown')),
                         ('ohe',OneHotEncoder(handle_unknown='ignore'))]),list(CATEGORICAL))
    ])),('model',RandomForestRegressor(n_estimators=7,random_state=42,min_samples_leaf=2))])
    pipe.fit(x,frame['actual_yield_percent'])
    spec=export_forest(pipe,NUMERIC,CATEGORICAL)
    assert spec['format']=='spps-v9-safe-forest-v1'
    encoded=json.loads(json.dumps(spec))
    validate_forest(encoded)
    for item in [_features(pd.DataFrame([{'sequence':'A'*12,'scale_mmol':.1,'loading_mmol_g':.734,
                'resin':'2-CTC','chemistry':'DIC/HOBt'}])),
                 _features(pd.DataFrame([{'sequence':'A'*20,'scale_mmol':.15,'loading_mmol_g':.734,
                'resin':'2-CTC','chemistry':'unseen'}]))]:
        expected=float(pipe.predict(item)[0])
        actual=predict_forest(encoded,item.iloc[0].to_dict())
        assert actual==pytest.approx(expected,abs=1e-8)


def test_rejects_corrupt_tree_data():
    spec={'format':'spps-v9-safe-forest-v1','numeric':['scale_mmol'],'categorical':[],
          'numeric_medians':[.1],'category_fill':[],'categories':[],
          'trees':[{'left':[1],'right':[1],'feature':[0],'threshold':[.2],'value':[8.] }]}
    with pytest.raises(ValueError,match='topology'):
        validate_forest(spec)
    spec['trees'][0]={'left':[-1],'right':[-1],'feature':[-2],'threshold':[float('nan')],'value':[8.]}
    with pytest.raises(ValueError,match='node values'):
        validate_forest(spec)


def test_data_only_model_and_prediction_diagnostics(tmp_path):
    frame,data_dir,model_dir,meta=train_with_metadata(tmp_path)
    assert meta['status']=='EXPERIMENTAL_REVIEW_ONLY'
    assert meta['model_file'].endswith('.forest.json')
    assert 'holdout_feature_importance' in meta
    assert 'descriptive_holdout_abs_error_quantiles_points' in meta
    assert not list(model_dir.glob('*.joblib'))
    context=dict(sequence='A'*25,scale_mmol=.1,loading_mmol_g=.734,resin='2-CTC',
                 chemistry='DIC/HOBt',product_path='linear_deprotected')
    result=advise_from_local_data(context,data_dir,model_dir)
    assert result['status']=='EXPERIMENTAL_PREDICTION_REVIEW_ONLY'
    assert result['model_format']=='spps-v9-safe-forest-v1'
    assert result['descriptive_error_band_80'][0]<=result['prediction']<=result['descriptive_error_band_80'][1]
    assert 'NOT a calibrated prediction interval' in result['error_band_meaning']
    assert advise_from_local_data({**context,'sequence':'V'*25},data_dir,model_dir)['status']=='OUT_OF_DISTRIBUTION'
    model=(model_dir/meta['model_file'])
    model.write_text('{"payload":"__import__(\\"os\\").system(\\"touch HACK\\")"}',encoding='utf-8')
    assert advise_from_local_data(context,data_dir,model_dir)['status']=='MODEL_INTEGRITY_MISMATCH'
    assert not (tmp_path/'HACK').exists()


def test_protected_sequence_withholds_plain_sequence_model(tmp_path):
    _,data_dir,model_dir,metadata=train_with_metadata(tmp_path)
    q=dict(sequence='H-Ser(tBu)-OH',scale_mmol=.1,loading_mmol_g=.734,
           resin='2-CTC',chemistry='DIC/HOBt',product_path='linear_deprotected')
    result=advise_from_local_data(q,data_dir,model_dir)
    assert result['status']=='CHEMISTRY_NOT_MODELED'
    assert result['prediction'] is None
    annotated=sample_runs(34)
    annotated.loc[0,'sequence']='H-Ser(tBu)-OH'
    report=ml_readiness_report(annotated)
    assert report['quality_audit']['chemistry_annotated_sequence_count']==1


def test_old_joblib_not_loaded_and_requires_retrain(tmp_path):
    _,data_dir,model_dir,meta=train_with_metadata(tmp_path)
    context=dict(sequence='A'*25,scale_mmol=.1,loading_mmol_g=.734,resin='2-CTC',chemistry='DIC/HOBt')
    metadata_file=model_dir/'ai_excel_yield_v9.json'
    metadata=json.loads(metadata_file.read_text(encoding='utf-8'))
    metadata.pop('model_format')
    metadata_file.write_text(json.dumps(metadata),encoding='utf-8')
    (model_dir/'ai_excel_yield_v9.joblib').write_bytes(b'UNSAFE PICKLE SHOULD NEVER LOAD')
    result=advise_from_local_data(context,data_dir,model_dir)
    assert result['status']=='MODEL_SCHEMA_OUTDATED'
    assert result['prediction'] is None


def test_readiness_reports_help_without_model_leakage():
    data=sample_runs(12)
    report=ml_readiness_report(data)
    assert not report['targets']['actual_yield_percent']['ready']
    assert '24' in ' '.join(report['targets']['actual_yield_percent']['reasons'])
    assert ml_readiness_report(sample_runs(50))['targets']['actual_yield_percent']['ready']
    duplicate=pd.concat([sample_runs(30),sample_runs(30)],ignore_index=True)
    assert ml_readiness_report(duplicate)['quality_audit']['training_blocked']


def test_topology_is_not_mixed_with_linear_ml(tmp_path):
    data=sample_runs(64)
    data['product_path']='linear_deprotected'
    special=pd.DataFrame([{
        'sequence':'ACDE', 'actual_yield_percent':20, 'scale_mmol':.1,
        'loading_mmol_g':.734,'resin':'2-CTC','chemistry':'DIC/HOBt',
        'run_id':'CYCLIC001','product_path':'cyclic_protected'
    }])
    combined=pd.concat([data,special],ignore_index=True)
    loaded,data_dir,model_dir,metadata=train_with_metadata(tmp_path)
    assert len(_labeled(combined,'actual_yield_percent'))==64
    assert not any(d['sequence']=='ACDE' for d in similar_runs(combined,{'sequence':'ACDE',
           'product_path':'linear_deprotected','resin':'2-CTC','chemistry':'DIC/HOBt'}))
    actual=similar_runs(combined,{'sequence':'ACDE','product_path':'cyclic_protected',
                                 'resin':'2-CTC','chemistry':'DIC/HOBt'})
    assert actual and actual[0]['sequence']=='ACDE'
    save_reviewed_dataset(combined,{'reviewed':True},'different',data_dir)
    result=advise_from_local_data({'sequence':'ACDE','product_path':'cyclic_protected'},data_dir,model_dir)
    assert result['status']=='TOPOLOGY_NOT_MODELED'
    assert result['prediction'] is None


def test_blank_template_has_no_fabricated_measurements(tmp_path):
    from openpyxl import load_workbook
    file=create_blank_excel_template(tmp_path/'Experiment_TEMPLATE.xlsx')
    wb=load_workbook(file,read_only=False,data_only=True)
    try:
        sheet=wb['Runs']
        assert sheet.max_row==1
        assert 'Product path' in [x.value for x in sheet[1]]
        assert wb['GUIDE'].max_row>1
    finally:wb.close()
    preview=preview_file(file)
    assert any('No non-empty' in item for item in preview.warnings)
