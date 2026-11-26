"""V9 stage-specific, review-only ML. Separate each process endpoint and topology.

Fits only on explicitly measured, operator-reviewed Excel outcomes. Selects
RandomForest or ExtraTrees via sequence-group holdouts; JSON-only inference.
No automatic chemical recipe optimization, claims of causality, or extrapolation.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import math
import pandas as pd
import numpy as np

from suite_gui.ai_excel_core_v9 import (
    MIN_TRAIN, MIN_SEQUENCE_GROUPS, _percentage, _features, _sequence_group,
    _requires_chemistry_aware_features, audit_reviewed_data, normalize_product_path,
    _atomic_json, load_reviewed_dataset, _positive_number, _clean_category)
from suite_gui.ai_safe_forest_v9 import export_forest,load_verified_forest,predict_forest,FORMAT

STAGE_TARGETS={
    'coupling_conversion_percent':'coupling',
    'cyclization_yield_percent':'cyclization',
    'crude_yield_percent':'crude',
    'cleavage_recovery_percent':'cleavage',
    'purification_recovery_percent':'purification',
}
NUMERIC=('sequence_length','cys_count','asp_count','pro_count','gly_count',
         'd_residue_count','noncanonical_count','branch_residue_count','scale_mmol',
         'loading_mmol_g','reaction_time_h','reaction_concentration_mm')
CATEGORICAL=('resin','chemistry','product_path','reaction_method','cleavage_method','protection_profile')
FEATURES=NUMERIC+CATEGORICAL


def _selected_rows(frame:pd.DataFrame,target:str) -> pd.DataFrame:
    if target not in STAGE_TARGETS:
        raise ValueError('Not a supported measured reaction-stage target.')
    required={'sequence','product_path','reaction_step',target,'scale_mmol','loading_mmol_g'}
    if not required.issubset(frame.columns):
        raise ValueError('Reaction-stage ML requires explicit Sequence, Product path, Reaction step, Scale, Loading and measured target columns.')
    subset=frame.copy()
    subset=subset[subset['reaction_step'].astype(str).str.strip().str.casefold()==STAGE_TARGETS[target]].copy()
    subset=subset[subset['product_path'].map(normalize_product_path).isin(('linear_deprotected','linear_protected','cyclic_deprotected','cyclic_protected','branched_protected','branched_deprotected'))].copy()
    subset=subset[~subset['sequence'].map(_requires_chemistry_aware_features)]
    subset[target]=subset[target].map(_percentage)
    subset=subset[subset[target].notna()].reset_index(drop=True)
    return subset


def _design(frame:pd.DataFrame)->pd.DataFrame:
    base=_features(frame)
    for c,unit in (('reaction_time_h','h'),('reaction_concentration_mm','mM')):
        base[c]=[(_positive_number(x,unit) if c in frame else None) for x in (frame[c] if c in frame else [None]*len(frame))]
    base['product_path']=frame['product_path'].map(normalize_product_path)
    base['reaction_method']=frame['reaction_method'].map(_clean_category) if 'reaction_method' in frame else ''
    base['cleavage_method']=frame['cleavage_method'].map(_clean_category) if 'cleavage_method' in frame else ''
    base['protection_profile']=frame['protection_profile'].map(_clean_category) if 'protection_profile' in frame else ''
    return base[list(FEATURES)]


def _pipeline(kind:str):
    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder
    from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
    if kind not in ('RandomForest','ExtraTrees'):
        raise ValueError('Unsupported safe model candidate.')
    cls=RandomForestRegressor if kind=='RandomForest' else ExtraTreesRegressor
    return Pipeline([('prep',ColumnTransformer([
        ('num',SimpleImputer(strategy='constant',fill_value=0.0),list(NUMERIC)),
        ('cat',Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='Unknown')),
                         ('ohe',OneHotEncoder(handle_unknown='ignore'))]),list(CATEGORICAL))])),
        ('model',cls(n_estimators=72,min_samples_leaf=2,random_state=42,n_jobs=1))])


def _stem(target):
    if target not in STAGE_TARGETS:
        raise ValueError('Unsupported target.')
    return 'ai_excel_stage_'+STAGE_TARGETS[target]+'_v9'


def _withheld(root,target,digest,reason,extras=None):
    meta={'schema':'spps-v9-stage-ml-v1','status':'WITHHELD_UNRELIABLE',
          'target':target,'dataset_sha256':digest,'reason':reason,**(extras or {})}
    _atomic_json(root/(_stem(target)+'.json'),meta)
    return meta


def train_stage_advisor(frame:pd.DataFrame,target:str,model_dir:str|Path,source_digest:str) ->dict:
    """Explicit stage/site separation, group CV and optional group conformal calibration.

    When >= 40 distinct sequence groups, keep disjoint calibration groups and
    use maximum per-group residual; do not refit on those groups afterwards.
    Smaller datasets report descriptive holdout errors, not coverage guarantees.
    """
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.metrics import mean_absolute_error
    root=Path(model_dir);root.mkdir(parents=True,exist_ok=True)
    audit=audit_reviewed_data(frame)
    if audit['training_blocked']:
        return _withheld(root,target,source_digest,'Data quality audit blocked training: duplicate IDs, rows or invalid sequences.')
    try: selected=_selected_rows(frame,target)
    except ValueError as exc: return _withheld(root,target,source_digest,str(exc))
    if len(selected)<MIN_TRAIN:
        return _withheld(root,target,source_digest,f'Need {MIN_TRAIN} measured rows for this exact stage, found {len(selected)}.')
    groups=selected['sequence'].map(_sequence_group)
    if groups.nunique()<MIN_SEQUENCE_GROUPS:
        return _withheld(root,target,source_digest,f'Need {MIN_SEQUENCE_GROUPS} distinct sequences for this stage.')
    if selected[target].nunique()<3:
        return _withheld(root,target,source_digest,'Not enough measured target variability.')
    features=_design(selected);y=selected[target].astype(float)
    if features['scale_mmol'].notna().sum()<len(selected)//2 or features['loading_mmol_g'].notna().sum()<len(selected)//2:
        return _withheld(root,target,source_digest,'Missing Scale/Loading measurements in many experiments.')
    unique_paths=sorted(set(features['product_path']))
    # Never fit a model across different product topology classes.
    if len(unique_paths)!=1:
        return _withheld(root,target,source_digest,'Split mixed product topologies into separate reviewed datasets.',{'paths':unique_paths})
    if unique_paths[0] in ('branched_deprotected','branched_protected'):
        return _withheld(root,target,source_digest,'Branched atom topology is not validated for ML features; hold predictions.')
    if unique_paths[0].endswith('_protected') and ((features['protection_profile']=='').any() or
                                                 features['protection_profile'].str.len().gt(120).any()):
        return _withheld(root,target,source_digest,'Protected products require explicit protecting-group profile on every record.')
    if target=='cyclization_yield_percent' and (features['reaction_time_h'].isna().any() or
                   features['reaction_concentration_mm'].isna().any()):
        return _withheld(root,target,source_digest,'Cyclization needs recorded reaction time and concentration for every training row.')
    # Explicit reaction method is needed for chemistry-dependent cyclization endpoints.
    if target=='cyclization_yield_percent' and ('reaction_method' not in selected or
        (features['reaction_method']=='').any()):
        return _withheld(root,target,source_digest,'Cyclization outcomes need explicit reaction method for every accepted row.')
    use_calibration=groups.nunique()>=40
    if use_calibration:
        main_idx,cal_idx=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=91).split(features,y,groups))
    else:
        main_idx=np.arange(len(selected));cal_idx=np.array([],dtype=int)
    x=features.iloc[main_idx];v=y.iloc[main_idx];g=groups.iloc[main_idx]
    splitter=GroupShuffleSplit(n_splits=3,test_size=.25,random_state=42)
    results={};errors={}
    baseline=[]
    splits=list(splitter.split(x,v,groups=g))
    for train_idx,test_idx in splits:
        baseline.append(float(mean_absolute_error(v.iloc[test_idx],[float(v.iloc[train_idx].median())]*len(test_idx))))
    for kind in ('RandomForest','ExtraTrees'):
        scores=[];residuals=[]
        for train_idx,test_idx in splits:
            model=_pipeline(kind)
            model.fit(x.iloc[train_idx],v.iloc[train_idx])
            predictions=np.asarray(model.predict(x.iloc[test_idx]))
            scores.append(float(mean_absolute_error(v.iloc[test_idx],predictions)))
            residuals.extend(abs(float(a)-float(b)) for a,b in zip(v.iloc[test_idx],predictions))
        results[kind]=scores;errors[kind]=residuals
    chosen=min(results,key=lambda k:sum(results[k])/len(results[k]))
    mae=float(np.mean(results[chosen]));base=float(np.mean(baseline))
    wins=sum(a<b for a,b in zip(results[chosen],baseline))
    summary={'candidates':{k:{'group_holdout_mae':round(float(np.mean(vv)),3),
                              'split_mae':[round(x,3) for x in vv]} for k,vv in results.items()},
             'baseline_mae':round(base,3),'chosen_candidate':chosen,'wins_vs_baseline':wins,
             'sequence_groups':int(groups.nunique()),'measured_rows':len(selected),
             'product_path':unique_paths[0],'target':target,'stage':STAGE_TARGETS[target]}
    if mae>=base or wins<2:
        return _withheld(root,target,source_digest,'Grouped evaluation did not reliably outperform median baseline.',summary)
    model=_pipeline(chosen);model.fit(x,v)
    calibration={'kind':'DESCRIPTIVE_HOLDOUT_ERRORS_NOT_COVERAGE',
                 'abs_error_q90_points':round(float(np.quantile(errors[chosen],.9)),3)}
    if use_calibration:
        # Independent held-out sequence groups, not used in model selection/training.
        pred=model.predict(features.iloc[cal_idx]);residual=pd.DataFrame({'group':groups.iloc[cal_idx].values,
           'error':abs(y.iloc[cal_idx].to_numpy()-pred)}).groupby('group')['error'].max().tolist()
        count=len(residual);rank=math.ceil((count+1)*.9)
        if rank<=count:
            calibration={'kind':'GROUP_SPLIT_CONFORMAL_EXCHANGEABILITY_ASSUMED',
                         'group_level_radius_points':round(sorted(residual)[rank-1],3),
                         'calibration_sequence_groups':count,'nominal_coverage':0.9,
                         'warning':'Coverage assumes exchangeable future sequence groups and same data regime; not a lab guarantee.'}
    from suite_gui.ai_safe_forest_v9 import export_forest
    forest=export_forest(model,NUMERIC,CATEGORICAL)
    name=_stem(target)
    _atomic_json(root/(name+'.forest.json'),forest)
    meta={'schema':'spps-v9-stage-ml-v1','status':'EXPERIMENTAL_REVIEW_ONLY',
          'model_format':FORMAT,'target':target,'dataset_sha256':source_digest,
          'model_file':name+'.forest.json',
          'model_sha256':sha256((root/(name+'.forest.json')).read_bytes()).hexdigest(),
          'calibration':calibration,'features':list(FEATURES),
          'observed_resins':sorted(set(features['resin'])),
          'observed_chemistry':sorted(set(features['chemistry'])),
          'observed_methods':sorted(set(features['reaction_method'])),
          'observed_profiles':sorted(set(features['protection_profile'])),
          'observed_cleavage_methods':sorted(set(features['cleavage_method'])),
          'observed_scale_mmol':[float(features['scale_mmol'].min()),float(features['scale_mmol'].max())],
          'observed_loading_mmol_g':[float(features['loading_mmol_g'].min()),float(features['loading_mmol_g'].max())],
          'observed_lengths':[int(features['sequence_length'].min()),int(features['sequence_length'].max())],
          'source':'Operator-reviewed local measurements only; no causality or guaranteed yield',**summary}
    _atomic_json(root/(name+'.json'),meta)
    return meta


def advise_stage(context:dict, data_dir:str|Path, model_dir:str|Path,target:str)->dict:
    """Fail-closed, no model load unless dataset digest and chemistry match."""
    if target not in STAGE_TARGETS:
        raise ValueError('Not a supported process endpoint.')
    output={'status':'WITHHELD','prediction':None,'target':target,'stage':STAGE_TARGETS[target]}
    if _requires_chemistry_aware_features(context.get('sequence','')):
        return {**output,'reason':'Exact protected/branch molecular features are not yet modeled.'}
    if str(context.get('reaction_step','')).casefold()!=STAGE_TARGETS[target]:
        return {**output,'reason':'Choose the corresponding reaction stage before using a stage model.'}
    try:
        _,data=load_reviewed_dataset(data_dir)
        import json
        path=normalize_product_path(context.get('product_path'))
        partition=Path(model_dir)/'stage_models'/target/path
        selected_root=partition if (partition/(_stem(target)+'.json')).is_file() else Path(model_dir)
        meta=json.loads((selected_root/(_stem(target)+'.json')).read_text(encoding='utf-8'))
        if meta.get('schema')!='spps-v9-stage-ml-v1' or meta.get('status')!='EXPERIMENTAL_REVIEW_ONLY' or meta.get('target')!=target:
            return {**output,'reason':'No approved stage model; train on measured data first.'}
        if meta.get('dataset_sha256')!=data['dataset_sha256']:
            return {**output,'reason':'Model is stale relative to reviewed dataset; retrain.'}
        if normalize_product_path(context.get('product_path'))!=meta['product_path']:
            return {**output,'reason':'Model trained for a different product topology.'}
        row=pd.DataFrame([context]);features=_design(row).iloc[0].to_dict()
        if features['resin'] not in meta['observed_resins'] or features['chemistry'] not in meta['observed_chemistry']:
            return {**output,'reason':'Resin/coupling outside the model training domain.'}
        if features['protection_profile'] not in meta['observed_profiles']:
            return {**output,'reason':'Protecting-group state not represented in training; prediction withheld.'}
        if features['cleavage_method'] not in meta['observed_cleavage_methods']:
            return {**output,'reason':'Cleavage method outside recorded conditions.'}
        if features['reaction_method'] not in meta['observed_methods']:
            return {**output,'reason':'Reaction method outside the model training domain.'}
        if target=='cyclization_yield_percent' and (features['reaction_time_h'] is None or
                 features['reaction_concentration_mm'] is None):
            return {**output,'reason':'Cyclization requires observed-equivalent time and concentration inputs.'}
        for key,bounds in [('scale_mmol','observed_scale_mmol'),('loading_mmol_g','observed_loading_mmol_g'),
                           ('sequence_length','observed_lengths')]:
            value=features[key]
            if value is None or not all(math.isfinite(float(v)) for v in meta[bounds]) or not meta[bounds][0]<=value<=meta[bounds][1]:
                return {**output,'reason':f'Input {key} is outside the observed training range.'}
        model=load_verified_forest(selected_root/meta['model_file'],meta['model_sha256'])
        pred=float(predict_forest(model,features,validated=True))
        if not math.isfinite(pred):
            return {**output,'reason':'Nonfinite model prediction.'}
        pred=min(100.,max(0.,pred))
        return {'status':'EXPLORATORY_PREDICTION','target':target,'stage':STAGE_TARGETS[target],
                'prediction':round(pred,3),'calibration':meta['calibration'],
                'model':meta['chosen_candidate'],
                'warning':'Review only. No conditions applied; unrelated or novel chemistry must be independently validated.'}
    except (ValueError, OSError,KeyError,TypeError,OverflowError) as exc:
        return {**output,'reason':str(exc)[:250]}


def train_partitioned_stage_advisors(frame:pd.DataFrame,target:str,model_dir:str|Path,
                                     source_digest:str)->dict:
    """One-click stage training, automatically partitioned by product topology.

    Independent models prevent protected/cyclic/linear records being pooled.
    Only partitions with enough valid observations get models; all others
    return explicit reasons for withholding. The original dataset is untouched.
    """
    if target not in STAGE_TARGETS:
        raise ValueError('Unsupported stage target.')
    if 'product_path' not in frame or 'reaction_step' not in frame:
        raise ValueError('Map Product path and Reaction step before learning process outcomes.')
    audit=audit_reviewed_data(frame)
    if audit['training_blocked']:
        return {'status':'WITHHELD_DATA_QUALITY', 'reason':'Resolve duplicate IDs and invalid rows first.',
                'audit':audit}
    selection=frame[frame['reaction_step'].astype(str).str.strip().str.casefold()==STAGE_TARGETS[target]].copy()
    selection['_normalized_path']=selection['product_path'].map(normalize_product_path)
    models={}
    root=Path(model_dir)
    for path in sorted(set(selection['_normalized_path'])):
        if path not in ('linear_deprotected','linear_protected','cyclic_protected','cyclic_deprotected',
                        'branched_deprotected','branched_protected'):
            continue
        group=selection[selection['_normalized_path']==path].drop(columns='_normalized_path').copy()
        # Ensure aliases become stable and distinguish model identity.
        group['product_path']=path
        result=train_stage_advisor(group,target,root/'stage_models'/target/path,source_digest)
        models[path]={'status':result.get('status'),'reason':result.get('reason'),
                      'measured_rows':len(group),
                      'model':result.get('chosen_candidate'),
                      'mae':result.get('candidates',{}).get(result.get('chosen_candidate'),{}).get('group_holdout_mae')}
    return {'status':'STAGE_PARTITIONS_REVIEW_ONLY','target':target,'models':models,
            'trained_models':sum(x['status']=='EXPERIMENTAL_REVIEW_ONLY' for x in models.values()),
            'meaning':'Grouped validation per topology, no cross-topology transfer or auto-applied chemistry.'}
