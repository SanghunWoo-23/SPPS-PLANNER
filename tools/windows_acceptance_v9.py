"""Run on *actual Windows* to produce local evidence, not simulated PASS status.

Command: python tools/windows_acceptance_v9.py
Does not install/uninstall EXE; package deployment remains a separate check.
"""
from __future__ import annotations
import json
import platform
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path


def main():
    results={'schema':'spps-v9-windows-acceptance-v1',
             'timestamp_utc':datetime.now(timezone.utc).isoformat(),
             'os':platform.platform(),'python':sys.version.split()[0],
             'checks':{}}
    if platform.system()!='Windows':
        results['checks']['native_windows']='NOT_TESTED_NOT_WINDOWS'
        print(json.dumps(results,ensure_ascii=False,indent=2))
        return 2
    root=Path(__file__).resolve().parents[1]
    cmd=[sys.executable,str(root/'main_launcher.py'),'--self-test']
    try:
        completed=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=90)
        results['checks']['selftest']='PASS' if completed.returncode==0 else 'FAIL'
        results['selftest_exit_code']=completed.returncode
        results['selftest_stderr_last_300']=completed.stderr[-300:]
    except subprocess.TimeoutExpired:
        results['checks']['selftest']='TIMEOUT'
    try:
        sys.path.insert(0,str(root));sys.path.insert(0,str(root/'apps/spps_planner_app'))
        import tkinter as tk
        from suite_gui.release import SPPSGui
        app=SPPSGui()
        app.update_idletasks()
        results['checks']['native_tk_create']='PASS' if 'V9.0.0' in app.title() else 'FAIL'
        app.destroy()
    except Exception as exc:
        results['checks']['native_tk_create']='FAIL'
        results['tk_error']=f'{type(exc).__name__}: {exc}'[:300]
    dest=root/'WINDOWS_ACCEPTANCE_V9.json'
    dest.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(results,indent=2,ensure_ascii=False))
    return 0 if all(v=='PASS' for v in results['checks'].values()) else 1

if __name__=='__main__':
    raise SystemExit(main())
