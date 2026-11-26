"""Independent, read-only external-stage-ML evaluation with leakage rejection.

Use only an *entirely separate measured external dataset* not used for fitting,
model selection or calibration. This tool NEVER trains or updates the model.
It reports aggregate outcomes only; sequences and confidential run IDs are not
emitted. No certification of predictive performance is implied by its output.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import math
from statistics import median
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'apps'/'spps_planner_app')]
from suite_gui.ai_excel_core_v9 import (preview_file,normalize_preview,load_reviewed_dataset,
                                         _sequence_group,_percentage,normalize_product_path)
from suite_gui.process_ai_v9 import STAGE_TARGETS,advise_stage


def evaluate_external_file(train_dir: str | Path, model_dir: str | Path,
                           external_file: str | Path, *, target: str,
                           min_independent_sequences: int = 8) -> dict:
    if target not in STAGE_TARGETS:
        raise ValueError('Unsupported measured endpoint.')
    training, meta=load_reviewed_dataset(train_dir)
    preview=preview_file(external_file)
    external, audit=normalize_preview(preview)
    required={'sequence','product_path','reaction_step',target}
    if not required.issubset(external.columns):
        return {'status':'WITHHELD_MISSING_FIELDS','required_fields':sorted(required),
                'available_fields':sorted(external.columns),'data_approved':False}
    frame=external.copy()
    frame=frame[frame['reaction_step'].astype(str).str.casefold().str.strip()==STAGE_TARGETS[target]]
    frame[target]=frame[target].map(_percentage)
    frame=frame[frame[target].notna()]
    if len(frame)==0:
        return {'status':'WITHHELD_NO_MEASUREMENTS','target':target,'evaluated_rows':0}
    train_groups=set(training['sequence'].map(_sequence_group))
    eval_groups=set(frame['sequence'].map(_sequence_group))
    # Do NOT silently exclude overlapping samples: overlap means the entire
    # purportedly independent set needs an operator audit first.
    overlap=train_groups & eval_groups
    if overlap:
        return {'status':'WITHHELD_LEAKAGE','target':target,
                'overlapping_sequence_groups':len(overlap), 'evaluated_rows':0,
                'reason':'External dataset overlaps training sequence identities; independently separate experiments first.'}
    # A distinct sequence does not prove a distinct experiment. Re-used Run IDs
    # are a second leakage boundary even when the corresponding sequence differs.
    if 'run_id' in training and 'run_id' in frame:
        def unique_ids(column):
            return {str(v).strip().casefold() for v in column.dropna()
                    if str(v).strip() and str(v).strip().casefold() not in ('nan','none','null')}
        duplicate_ids=unique_ids(training['run_id']) & unique_ids(frame['run_id'])
        if duplicate_ids:
            return {'status':'WITHHELD_RUN_ID_LEAKAGE','target':target,
                    'overlapping_run_ids':len(duplicate_ids),'evaluated_rows':0,
                    'reason':'External run identifiers overlap reviewed training records.'}
    distinct=len(eval_groups)
    if distinct<min_independent_sequences:
        return {'status':'WITHHELD_TOO_SMALL','target':target,
                'independent_sequence_groups':distinct,'required':min_independent_sequences,
                'evaluated_rows':0}
    predictions=[]; measured=[]; accepted_groups=[]; intervals=[]; reasons={}
    for record in frame.to_dict('records'):
        context=dict(record)
        context['product_path']=normalize_product_path(context['product_path'])
        result=advise_stage(context,train_dir,model_dir,target)
        if result.get('status')=='EXPLORATORY_PREDICTION':
            prediction=result.get('prediction')
            if isinstance(prediction,(float,int)) and math.isfinite(float(prediction)):
                predictions.append(float(prediction));measured.append(float(record[target]))
                accepted_groups.append(_sequence_group(record['sequence']))
                calibration=result.get('calibration') or {}
                if calibration.get('kind')=='GROUP_SPLIT_CONFORMAL_EXCHANGEABILITY_ASSUMED':
                    radius=calibration.get('group_level_radius_points')
                    if isinstance(radius,(float,int)) and not isinstance(radius,bool) and math.isfinite(radius) and radius>=0:
                        intervals.append((max(0.,float(prediction)-float(radius)),
                                          min(100.,float(prediction)+float(radius)),float(record[target])))
                continue
        reason=str(result.get('reason') or result.get('status') or 'WITHHELD')[:150]
        reasons[reason]=reasons.get(reason,0)+1
    accepted_distinct=len(set(accepted_groups))
    summary={'schema':'SPPS-V9-external-evaluation-v2',
             'timestamp_utc':datetime.now(timezone.utc).isoformat(),
             'status':'EXTERNAL_HOLDOUT_DESCRIPTIVE_ONLY' if accepted_distinct>=min_independent_sequences
                else 'WITHHELD_TOO_FEW_IN_DOMAIN_PREDICTIONS',
             'target':target,'external_rows_measured':int(len(frame)),
             'independent_sequence_groups':distinct,'predicted_independent_sequence_groups':accepted_distinct,
             'predicted_rows':len(predictions),
             'withheld_rows':len(frame)-len(predictions),'rejection_reasons':reasons,
             'training_dataset_sha256':meta.get('dataset_sha256'),
             'interpretation':'Read-only independent observation summary, not model retraining or validated lab SOP.'}
    if predictions:
        errors=[abs(a-b) for a,b in zip(predictions,measured)]
        summary.update(mae_percent_points=round(sum(errors)/len(errors),4),
                       median_absolute_error_percent_points=round(median(errors),4),
                       mean_bias_points=round(sum(a-b for a,b in zip(predictions,measured))/len(errors),4))
        if intervals and len(intervals)==len(predictions):
            summary['empirical_row_interval_coverage']=round(
                sum(low <= observation <= high for low,high,observation in intervals)/len(intervals),4)
            summary['interval_interpretation']='Descriptive held-out interval coverage, not a coverage guarantee.'
        # Each independent sequence contributes equally, regardless of how
        # many repeat measurements it has in the file.
        by_group={}
        for group,prediction,observation in zip(accepted_groups,predictions,measured):
            by_group.setdefault(group,[]).append(abs(prediction-observation))
        summary['sequence_balanced_mae_percent_points']=round(
            sum(sum(v)/len(v) for v in by_group.values())/len(by_group),4)
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--train-dir',required=True,type=Path)
    parser.add_argument('--model-dir',required=True,type=Path)
    parser.add_argument('--external',required=True,type=Path)
    parser.add_argument('--target',required=True,choices=tuple(STAGE_TARGETS))
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args(argv)
    if args.external.resolve()==args.out.resolve():
        parser.error('Never overwrite the external measurement file.')
    result=evaluate_external_file(args.train_dir,args.model_dir,args.external,target=args.target)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    temporary=args.out.with_suffix(args.out.suffix+'.tmp')
    temporary.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    temporary.replace(args.out)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['status']=='EXTERNAL_HOLDOUT_DESCRIPTIVE_ONLY' else 2

if __name__=='__main__':
    raise SystemExit(main())
