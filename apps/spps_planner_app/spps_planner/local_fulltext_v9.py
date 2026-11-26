"""V9 opt-in, local-only full-text evidence retrieval with page/file citations.

No automatic protocol extraction or synthesis recommendations. No networking.
Only text layers are supported; scanned/image-only PDFs report no readable text.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from pathlib import Path

MAX_FILES=8
MAX_BYTES_PER_FILE=10_000_000
MAX_PAGES=250
MAX_TEXT_PER_DOCUMENT=1_000_000
_TOKEN=re.compile(r'[A-Za-z0-9가-힣]{2,}',re.UNICODE)

class EvidenceInputError(ValueError):pass


def index_local_documents(paths):
    if not isinstance(paths,(list,tuple)) or not 1<=len(paths)<=MAX_FILES:
        raise EvidenceInputError('Choose 1–8 local PDFs or text documents.')
    indexed=[]; warnings=[]
    for original in paths:
        p=Path(original)
        if not p.is_file() or p.stat().st_size>MAX_BYTES_PER_FILE or p.stat().st_size<1:
            raise EvidenceInputError('Missing or oversized document (limit 10 MB).')
        if p.suffix.lower() not in ('.pdf','.txt','.md'):
            raise EvidenceInputError('Supported document types: PDF, TXT, MD.')
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if p.suffix.lower()=='.pdf':
            try:
                from pypdf import PdfReader
            except ImportError as exc:
                raise EvidenceInputError('Install optional pypdf for PDF text extraction.') from exc
            try:
                reader=PdfReader(str(p),strict=False)
                if reader.is_encrypted:
                    raise EvidenceInputError('Encrypted PDF is unsupported.')
                if len(reader.pages)>MAX_PAGES:
                    raise EvidenceInputError('Document exceeds 250 pages.')
                pages=[(number,(page.extract_text() or '')) for number,page in enumerate(reader.pages,1)]
            except EvidenceInputError:raise
            except Exception as exc:
                raise EvidenceInputError(f'Unreadable PDF: {type(exc).__name__}') from exc
        else:
            try:text=p.read_text(encoding='utf-8-sig')
            except UnicodeError as exc:raise EvidenceInputError('Only UTF-8 text supported.') from exc
            pages=[(1,text)]
        length=sum(len(t) for _,t in pages)
        if length>MAX_TEXT_PER_DOCUMENT:
            raise EvidenceInputError('Document exceeds 1 million readable characters.')
        good=0
        for page,text in pages:
            normalized=' '.join(text.split())
            if not normalized:continue
            good+=1
            # paragraph-sized searchable fragments preserve original page labels.
            for start in range(0,len(normalized),850):
                fragment=normalized[start:start+1000]
                tokens=Counter(w.lower() for w in _TOKEN.findall(fragment))
                if tokens:
                    indexed.append({'filename':p.name,'sha256':digest,'page':page,
                                   'text':fragment,'counts':tokens})
        if not good:warnings.append(f'{p.name}: no extractable text (scanned/image PDF needs separate OCR).')
    return {'status':'LOCAL_TEXT_INDEX_NOT_VALIDATED_SOP','fragments':indexed,'warnings':warnings,
            'document_count':len(paths),'no_network_transmission':True}


def search_local_fulltext(index: dict, query: str, *, limit: int=5):
    """BM25-like lexical scoring, bounded snippets; cited page labels are source positions."""
    if not isinstance(index,dict) or not isinstance(index.get('fragments'),list):
        raise EvidenceInputError('Build a text index first.')
    if not isinstance(query,str) or not 2<=len(query.strip())<=160 or type(limit)!=int or not 1<=limit<=10:
        raise EvidenceInputError('Search requires 2–160 text characters and 1–10 hits.')
    words=list(dict.fromkeys(w.lower() for w in _TOKEN.findall(query)))
    if not words:return {'status':'NO_MATCH','hits':[]}
    fragments=index['fragments']
    n=len(fragments)
    if n<1:return {'status':'NO_EXTRACTABLE_TEXT','hits':[],'warnings':index.get('warnings',[])}
    doc_freq=Counter(w for row in fragments for w in set(row['counts']))
    ranked=[]
    for row in fragments:
        counts=row['counts'];doclen=sum(counts.values())
        score=0.0
        for word in words:
            count=counts.get(word,0)
            if count:
                idf=math.log(1+(n-doc_freq[word]+.5)/(doc_freq[word]+.5))
                score+=idf*(count*2.2)/(count+1.2*(0.25+0.75*doclen/150))
        if score>0:
            text=row['text']
            positions=[match.start() for term in words for match in re.finditer(re.escape(term),text,re.I)]
            offset=max(0,min(positions)-60) if positions else 0
            excerpt=text[offset:offset+220]
            ranked.append((score,{'source_file':row['filename'],'source_sha256':row['sha256'],
                                  'page':row['page'],'excerpt':excerpt,'score':round(score,5),
                                  'evidence_status':'SOURCE_TEXT_ONLY_OPERATOR_REVIEW_REQUIRED'}))
    ranked.sort(key=lambda x:(-x[0],x[1]['source_file'],x[1]['page']))
    return {'status':'LOCAL_SOURCE_EXCERPTS_ONLY' if ranked else 'NO_MATCH',
            'hits':[item for _,item in ranked[:limit]],
            'notice':'Exact local text excerpts with PDF page references; not an autonomous chemical conclusion or validated SOP.'}
