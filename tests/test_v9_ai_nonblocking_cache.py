"""V9 AI: nonblocking Tk work, tamper-aware model cache, residue cache safety."""
from __future__ import annotations
import json
import os
import time
from pathlib import Path

import pytest

from suite_gui.ai_background_v9 import UiBackgroundRunner
from suite_gui.ai_excel_core_v9 import _residue_identity, _cached_residue_identity
from suite_gui.ai_safe_forest_v9 import load_verified_forest
from hashlib import sha256


def minimal_valid_forest():
    return {
        'format':'spps-v9-safe-forest-v1',
        'numeric':['sequence_length'],'categorical':[],
        'numeric_medians':[4.0],'category_fill':[],'categories':[],
        'trees':[{'left':[-1],'right':[-1],'feature':[-2],'threshold':[0.0],'value':[33.0]}]
    }


def test_safe_forest_cache_revalidates_checksum_even_with_unchanged_mtime(tmp_path, monkeypatch):
    import suite_gui.ai_safe_forest_v9 as forest
    path=tmp_path/'safe.forest.json'
    raw=json.dumps(minimal_valid_forest(),ensure_ascii=False).encode()
    path.write_bytes(raw)
    digest=sha256(raw).hexdigest()
    forest._MODEL_CACHE.clear()
    original_validate=forest.validate_forest
    calls=[]
    def count_validate(model):
        calls.append(1)
        return original_validate(model)
    monkeypatch.setattr(forest,'validate_forest',count_validate)
    first=load_verified_forest(path,digest)
    second=load_verified_forest(path,digest)
    assert first is second and len(calls)==1
    before=path.stat()
    path.write_bytes(raw.replace(b'33.0',b'44.0'))
    os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
    assert path.stat().st_size==before.st_size
    with pytest.raises(ValueError,match='checksum mismatch'):
        load_verified_forest(path,digest)
    # The cache may hold the old validated model, but changed bytes cannot use it.


def test_cached_residue_identifiers_cannot_be_mutated_by_caller():
    first,branch=_residue_identity('A-C-D')
    assert first==['A','C','D']
    first[0]='BOGUS'
    second,again=_residue_identity('A-C-D')
    assert second==['A','C','D'] and branch==again==0
    assert _cached_residue_identity.cache_info().hits>=1


@pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Tk requires a display')
def test_worker_keeps_event_loop_responsive_and_rejects_double_submit():
    import tkinter as tk
    root=tk.Tk();root.withdraw()
    try:
        events=[]
        runner=UiBackgroundRunner(root,lambda busy:events.append(('busy',busy)),poll_ms=10)
        root.after(30,lambda:events.append(('tick',True)))
        def slow():
            time.sleep(.16)
            return 'ok'
        assert runner.submit(slow,lambda result:events.append(('done',result)),lambda exc:events.append(('error',str(exc))))
        assert runner.busy
        assert not runner.submit(lambda:None,lambda _:None,lambda _:None)
        deadline=time.monotonic()+3
        while time.monotonic()<deadline and not any(e[0]=='done' for e in events):
            root.update();time.sleep(.004)
        assert ('tick',True) in events and ('done','ok') in events
        assert events.index(('tick',True))<events.index(('done','ok'))
        assert runner.busy is False
        assert ('busy',True) in events and ('busy',False) in events
    finally:
        root.destroy()


@pytest.mark.skipif(os.name!='nt' and not os.environ.get('DISPLAY'),reason='Tk requires a display')
def test_window_close_while_worker_busy_ignores_late_results():
    import tkinter as tk
    root=tk.Tk();root.withdraw()
    child=tk.Toplevel(root)
    called=[]
    try:
        runner=UiBackgroundRunner(child,lambda busy:called.append(('busy',busy)),poll_ms=10)
        assert runner.submit(lambda:(time.sleep(.09),'done')[1],
                    lambda _:called.append(('success',True)),
                    lambda _:called.append(('failure',True)))
        runner.close()
        time.sleep(.13)
        root.update()
        assert not child.winfo_exists()
        assert not any(label in ('success','failure') for label,*_ in called)
    finally:root.destroy()
