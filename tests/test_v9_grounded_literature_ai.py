"""No-network opt-in AI review tests. Deliberately do not call a live API."""
import pytest
from spps_planner.grounded_literature_ai_v9 import (
    prepare_literature_packet,request_grounded_literature_review,LiteratureReviewError)


def packet():
    return {'schema':'spps-v9-cited-excerpts-1','question':'What was observed?',
            'excerpts':[{'id':'E1','page':2,'source_sha256':'a'*64,
                         'excerpt':'The article reports protected peptide cyclization in solution.'}]}


def response(quote='protected peptide cyclization', source_id='E1'):
    import json
    return {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({
        'summary':'Relevant report found.', 'caveats':'Operator review is required.',
        'findings':[{'claim':'A report addresses cyclization.', 'evidence_id':source_id,
                     'exact_quote':quote,'limitation':'Not an experimentally validated SOP.'}]})}]}]}


def test_without_consent_never_calls_transport():
    def forbidden(*args):
        raise AssertionError('Should never transmit data')
    with pytest.raises(LiteratureReviewError,match='consent'):
        request_grounded_literature_review(packet(),explicit_consent=False,model='demo',api_key='secret',transport=forbidden)


def test_only_selected_short_excerpts_go_to_provider():
    recorded=[]
    def capture(url,payload,key):
        recorded.append((url,payload,key))
        return response()
    actual=request_grounded_literature_review(packet(),explicit_consent=True,
                      model='demo',api_key='test-key',transport=capture)
    assert actual['status']=='AI_EXCERPT_REVIEW_OPERATOR_APPROVAL_REQUIRED'
    assert actual['findings'][0]['source_page']==2
    assert len(recorded)==1
    assert recorded[0][1]['store'] is False
    assert 'The article reports' in recorded[0][1]['input']
    assert 'secret' not in str(actual)


@pytest.mark.parametrize('bad', [response('hallucinated data'), response(source_id='E5'),
                                     {'status':'failed','output':[]}, {'status':'completed','output':[]}])
def test_unverifiable_ai_output_withheld(bad):
    with pytest.raises(LiteratureReviewError):
        request_grounded_literature_review(packet(),explicit_consent=True,model='demo',api_key='key',
                                           transport=lambda *_:bad)


def test_packet_from_real_local_index(tmp_path):
    from spps_planner.local_fulltext_v9 import index_local_documents
    p=tmp_path/'sample.txt';p.write_text('Cyclization was conducted using a protected linear substrate.',encoding='utf8')
    result=prepare_literature_packet(index_local_documents([p]),'cyclization')
    assert len(result['excerpts'])==1
    assert result['excerpts'][0]['page']==1
    with pytest.raises(LiteratureReviewError):
        prepare_literature_packet(index_local_documents([p]),'unrelated nonmatch')
