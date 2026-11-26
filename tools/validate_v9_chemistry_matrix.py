"""Deterministic chemistry graph acceptance matrix (NOT experimental validation).

Run `python tools/validate_v9_chemistry_matrix.py --out report.json`.
No private files or network are read. Optional RDKit must be installed.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'apps'/'spps_planner_app')]
from spps_planner.extended_structure_v9 import graph_crosscheck

CASES=[
    ('Lys in the main chain', 'SKS','head_to_tail',None,True),
    ('N-terminal Pro secondary amine','PSP','head_to_tail',None,True),
    ('Retained tBu protection','S(tBu)KS(tBu)','head_to_tail',None,True),
    ('Natural L Lys branch','AK(GGEP)S','lysine_branch',None,True),
    ('Main-chain ring on Lys branch','AK(GGEP)S','lysine_branch_head_to_tail',None,True),
    ('Dde removed before branch product','AK(Dde)(GGEP)S','lysine_branch_head_to_tail',None,True),
    ('Disulfide explicit Cys sites','SCCS','disulfide',(2,3),True),
    ('Lys/Asp lactam','KED','sidechain_lactam',(1,3),True),
    ('N-acyl blocked ring','Ac-SKS-OH','head_to_tail',None,False),
    ('C-amide blocked ring','SKS-NH2','head_to_tail',None,False),
    ('Branched monomer ring unsupported','K(GGEP)','lysine_branch_head_to_tail',None,False),
    ('Unmodeled Arg Pbf fragment','R(Pbf)AC','linear',None,False),
]


def evaluate_matrix():
    entries=[]
    for label,seq,mode,sites,should_pass in CASES:
        result=graph_crosscheck(seq,'2-CTC',topology=mode,sites=sites,side_chain_mode='explicit')
        status=result['status'];passed=(status=='CROSSCHECK_PASS' if should_pass else status.startswith('WITHHELD'))
        entries.append({'case':label,'topology':mode,'expected':'CROSSCHECK_PASS' if should_pass else 'WITHHELD',
                        'status':status,'contract_pass':passed,
                        'product_formula':result.get('product_formula') if should_pass else None})
    return {'schema':'spps-v9-chemistry-contract-1','app_version':'V9.0.0',
            'scope':'Deterministic read-only molecular graph contract; no reaction outcome certification',
            'cases':entries,'passed':sum(x['contract_pass'] for x in entries),
            'total':len(entries),'all_pass':all(x['contract_pass'] for x in entries)}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args(argv)
    results=evaluate_matrix()
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        path=args.out
        path.write_text(json.dumps(results,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))
    return 0 if results['all_pass'] else 1

if __name__=='__main__':
    raise SystemExit(main())
