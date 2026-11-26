"""Explicit opt-in Crossref title/DOI search (bibliography, not article analysis).

No peptide sequence, project metadata, experimental records, or API keys are
sent automatically. Network is used *only* on an explicit operator action.
Returned publisher metadata is untrusted text and is not a laboratory method.
"""
from __future__ import annotations
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_ENDPOINT='https://api.crossref.org/works'
_MAX_RESPONSE=512*1024


def _parse_crossref_result(data: bytes, limit: int) -> list[dict]:
    if len(data)>_MAX_RESPONSE:
        raise ValueError('Crossref response too large.')
    response=json.loads(data.decode('utf-8'))
    if not isinstance(response,dict) or response.get('status')!='ok':
        raise ValueError('Crossref returned invalid metadata.')
    entries=response.get('message',{}).get('items',[])
    if not isinstance(entries,list):
        raise ValueError('Crossref work list malformed.')
    result=[]
    for entry in entries[:limit]:
        if not isinstance(entry,dict): continue
        doi=str(entry.get('DOI','')).strip().lower()
        if not re.fullmatch(r'10\.\d{4,9}/[^\s<>"\']{1,200}',doi,re.I):continue
        titles=entry.get('title') or []
        if not isinstance(titles,list) or not titles:continue
        title=re.sub(r'<[^>]*>','',str(titles[0])).strip()[:280]
        if not title:continue
        year=None
        dates=(entry.get('published') or entry.get('issued') or {}).get('date-parts',[])
        if isinstance(dates,list) and dates and isinstance(dates[0],list) and dates[0]:
            try:year=int(dates[0][0]);year=year if 1600<=year<=2200 else None
            except (ValueError,TypeError): pass
        result.append({'title':title,'doi':doi,'year':year,
                       'url':'https://doi.org/'+doi,
                       'status':'EXTERNAL_BIBLIOGRAPHY_UNVERIFIED_APPLICABILITY'})
    return result


def search_crossref_metadata(query: str, *, limit: int=4, timeout: float=6.0, fetch=None) -> dict:
    """Send only an explicitly supplied generic bibliographic query to Crossref.

    No sequence/project data is read by this function. Do not pass confidential
    sequences in query text; the UI confirms external transfer beforehand.
    """
    if not isinstance(query,str) or not 3<=len(query.strip())<=160:
        raise ValueError('Enter 3–160 characters of general reaction keywords.')
    if any(ord(c)<32 for c in query):
        raise ValueError('Control characters are not permitted in search text.')
    if type(limit) is not int or limit not in range(1,6):
        raise ValueError('Result count out of range.')
    if not 0.5 <= float(timeout) <= 15:
        raise ValueError('Timeout outside safe limit.')
    url=_ENDPOINT+'?'+urlencode({'query.bibliographic':query.strip(),
                                'rows':str(limit),'select':'DOI,title,published,issued,type'})
    if fetch is None:
        request=Request(url,headers={'User-Agent':'SPPS-Planner-V9/1.0 (metadata-only research preview)',
                                     'Accept':'application/json'})
        with urlopen(request,timeout=timeout) as response:
            data=response.read(_MAX_RESPONSE+1)
    else:
        data=fetch(url)
    if not isinstance(data,bytes):
        raise ValueError('Invalid metadata response type.')
    return {'status':'BIBLIOGRAPHY_ONLY_NOT_VALIDATED_SOP',
            'query':query.strip(),'source':'Crossref public REST metadata',
            'references':_parse_crossref_result(data,limit),
            'review_required':True,
            'limitations':'Title/DOI metadata only. Read original papers, verify versions and chemistry; no recipe or optimized protocol inferred.'}
