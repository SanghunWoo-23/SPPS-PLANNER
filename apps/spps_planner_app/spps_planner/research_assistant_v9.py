"""Offline, source-limited research assistant with traceable reference IDs.

Never synthesizes unseen literature or recommends unreviewed lab conditions.
Curated references are internal records; DOI/URL are stable citation links.
"""
from __future__ import annotations
from .reaction_evidence_v9 import REACTION_REFERENCES

KEYWORDS={
    'head_to_tail':('CONNORS_2022_PROTECTED_CYCLIZATION','MALESEVIC_2004_DILUTION','MCMURRAY_1994_CYCLIZATION'),
    'cyclization':('CONNORS_2022_PROTECTED_CYCLIZATION','MALESEVIC_2004_DILUTION'),
    'selective_cleavage':('BARLOS_1991_CTC','CHENEVAL_2014_CYCLIC_DISULFIDE'),
    'aspartimide':('KONG_2025_ASPARTIMIDE',),
    'oxyma':('ERNY_2020_DIC_OXYMA_HCN','MANNE_2021_CARBODIIMIDES'),
    'disulfide':('CHENEVAL_2014_CYCLIC_DISULFIDE',),
}


def search_local_evidence(query:str, *, max_results:int=6)->list[dict]:
    """Token overlap over a curated bibliography; never accesses the network."""
    value=str(query or '').strip().casefold()
    if not value:return []
    words={w for w in value.replace('/',' ').replace('_',' ').split() if len(w)>=2}
    ranked=[]
    for key,record in REACTION_REFERENCES.items():
        haystack=(record.get('title','')+' '+record.get('scope','')+' '+key.replace('_',' ')).casefold()
        weight=sum((2 if w in record.get('title','').casefold() else 1) for w in words if w in haystack)
        if value in haystack:weight+=3
        if weight:
            ranked.append((weight,key,record))
    ranked.sort(key=lambda item:(-item[0],item[1]))
    return [dict(id=key,**record, evidence_class='LITERATURE_CONTEXT_NOT_RECIPE')
            for _,key,record in ranked[:max(1,min(10,int(max_results)))]]


def build_research_brief(sequence:str, product_path:str, resin:str,
                         reaction_review:dict|None=None)->dict:
    relevant=[]
    if str(product_path).startswith('head_to_tail') or str(product_path).startswith('cyclic'):
        relevant.extend(KEYWORDS['head_to_tail'])
    if 'CTC' in str(resin).upper() or 'CHLOROTRITYL' in str(resin).upper():
        relevant.extend(KEYWORDS['selective_cleavage'])
    if 'D' in str(sequence).upper():
        relevant.extend(KEYWORDS['aspartimide'])
    if reaction_review and reaction_review.get('system_id')=='DIC_OXYMA':
        relevant.extend(KEYWORDS['oxyma'])
    if 'C' in str(sequence).upper():
        relevant.extend(KEYWORDS['disulfide'])
    unique=list(dict.fromkeys(relevant))
    references=[{'id':key,**REACTION_REFERENCES[key]} for key in unique]
    return {'status':'OFFLINE_CURATED_CONTEXT','references':references,
            'review_required':True,
            'limitations':'Literature class context only; never an exact validated recipe, recommendation of reagent ratios, or measured performance.',
            'missing_sources':'If no reference matches, record INSUFFICIENT_EVIDENCE rather than inventing a study.'}
