"""Reproducible operator-chemistry acceptance matrix for V9 atom-mapped paths."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps'/'spps_planner_app'))
from spps_planner.atomic_topology_v9 import calculate_atomic_topology,load_atomic_topology_json


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=None)
    args=ap.parse_args(argv)
    entries=[]
    for path in sorted((ROOT/'docs'/'examples').glob('*.json')):
        if 'CATALOG' in path.name or 'LIBRARY' in path.name:continue
        result=calculate_atomic_topology(load_atomic_topology_json(path))
        entries.append({'case':path.name,'status':result['status'],
                        'formula':result.get('formula'),'average_mw':result.get('average_mw'),
                        'pass':result['status']=='ATOM_MAPPED_GRAPH_PASS'})
    negative=calculate_atomic_topology({'monomers':[{'smiles':'C1CC1'}]})
    entries.append({'case':'nonpeptide_missing_atom_maps','status':negative['status'],
                    'pass':negative['status']=='WITHHELD_INVALID_ATOMIC_TOPOLOGY'})
    report={'version':'V9.0.0','validated_scope':'operator-mapped RDKit graph, not verified chemical identity',
            'cases':entries,'passed':sum(x['pass'] for x in entries),'total':len(entries),
            'status':'PASS' if all(x['pass'] for x in entries) else 'FAIL'}
    raw=json.dumps(report,ensure_ascii=False,indent=2)
    if args.out:Path(args.out).write_text(raw+'\n',encoding='utf-8')
    print(raw)
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
