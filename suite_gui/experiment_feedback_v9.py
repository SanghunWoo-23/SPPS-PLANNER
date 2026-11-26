"""Evidence-aware, read-only process outcome summaries from reviewed Excel data.

No inferred overall yield, no automated recipe changes, and no aggregation
across different experimental endpoints masquerading as one outcome.
"""
from __future__ import annotations
from collections import defaultdict
import statistics
from typing import Any
import pandas as pd
from suite_gui.ai_excel_core_v9 import _percentage,_clean_category
from suite_gui.process_ai_v9 import STAGE_TARGETS


def summarize_stage_feedback(frame:pd.DataFrame)->dict[str,Any]:
    if not isinstance(frame,pd.DataFrame):
        raise ValueError('Expected reviewed experimental DataFrame.')
    stats={}
    by_run=defaultdict(set)
    for target,stage in STAGE_TARGETS.items():
        if target not in frame or 'reaction_step' not in frame:
            continue
        measurements=[]
        run_ids=[]
        for _,row in frame.iterrows():
            if _clean_category(row.get('reaction_step','')).casefold()!=stage:
                continue
            measured=_percentage(row.get(target))
            if measured is None:
                continue
            measurements.append(measured)
            rid=_clean_category(row.get('run_id'))
            if rid:
                by_run[rid].add(stage)
                run_ids.append(rid)
        if measurements:
            stats[stage]={'target':target,'measured_records':len(measurements),
                          'unique_runs_with_ids':len(set(run_ids)),
                          'median_observed_percent':round(statistics.median(measurements),2),
                          'minimum_observed_percent':round(min(measurements),2),
                          'maximum_observed_percent':round(max(measurements),2),
                          'evidence_class':'OBSERVED_DATA_NOT_PREDICTIVE'}
    linked={rid:sorted(steps) for rid,steps in by_run.items() if len(steps)>1}
    return {'schema':'spps-v9-process-feedback-v1','stage_summaries':stats,
            'runs_with_multiple_measured_stages':linked,
            'meaning':'Read-only observed summaries; medians are not transfer-safe reaction recommendations or predicted yields.',
            'caution':'Do not multiply unrelated percent endpoints without verified mass and recovery definitions.'}
