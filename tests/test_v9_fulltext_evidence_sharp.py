from pathlib import Path
import pytest
from spps_planner.local_fulltext_v9 import index_local_documents, search_local_fulltext, EvidenceInputError


def test_search_cited_local_text_never_fabricates_page_or_protocol(tmp_path):
    p=tmp_path/'operator_paper.txt'
    p.write_text('Head-to-tail cyclization studies report oligomerization under some conditions.\n'
                 'No optimized general reagent mixture is assumed here.',encoding='utf-8')
    idx=index_local_documents([p]); result=search_local_fulltext(idx,'cyclization')
    assert result['status']=='LOCAL_SOURCE_EXCERPTS_ONLY'
    assert result['hits'][0]['page']==1
    assert result['hits'][0]['source_file']=='operator_paper.txt'
    assert 'oligomerization' in result['hits'][0]['excerpt']
    assert result['hits'][0]['source_sha256']
    assert search_local_fulltext(idx,'impossiblyunlikelyterm')['status']=='NO_MATCH'


def test_rejects_large_file(tmp_path):
    p=tmp_path/'huge.txt';p.write_bytes(b'a'*10_000_100)
    with pytest.raises(EvidenceInputError):index_local_documents([p])


def test_rejects_too_many_documents(tmp_path):
    p=tmp_path/'small.txt';p.write_text('synthesis')
    with pytest.raises(EvidenceInputError):index_local_documents([p]*9)


def test_unreadable_scanned_pdf_reports_limitation(tmp_path):
    from pypdf import PdfWriter
    p=tmp_path/'scan.pdf'
    w=PdfWriter();w.add_blank_page(width=400,height=400)
    with p.open('wb') as handle:w.write(handle)
    idx=index_local_documents([p])
    assert idx['warnings']
    assert search_local_fulltext(idx,'peptide')['status']=='NO_EXTRACTABLE_TEXT'
