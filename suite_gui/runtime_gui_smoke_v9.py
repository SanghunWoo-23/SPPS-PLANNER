"""Isolated native Tk create/update/destroy acceptance, without user-data access.

Requires explicit environment destinations. This is a real GUI lifecycle test,
not a substitute for interaction testing or a promise of crash-free operation.
"""
from __future__ import annotations

import json
import os
import platform
from pathlib import Path


def run_gui_smoke() -> int:
    output=os.environ.get('SPPS_PLANNER_GUI_SMOKE_OUTPUT','').strip()
    sandbox=os.environ.get('SPPS_PLANNER_USER_DATA','').strip()
    if not output or not sandbox:
        raise ValueError('GUI smoke requires isolated SPPS_PLANNER_GUI_SMOKE_OUTPUT and SPPS_PLANNER_USER_DATA.')
    report={'schema':'SPPS-V9-GUI-SMOKE-1','app_version':'V9.0.0',
            'platform':platform.platform(),'status':'FAIL','checks':{}}
    app=None
    try:
        from suite_gui.release import SPPSGui
        app=SPPSGui()
        app.withdraw()
        app.update_idletasks()
        app.update()
        report['checks']['title']='PASS' if 'V9.0.0' in app.title() else 'FAIL'
        report['checks']['root_exists']='PASS' if app.winfo_exists() else 'FAIL'
        report['status']='PASS' if all(v=='PASS' for v in report['checks'].values()) else 'FAIL'
    except Exception as exc:
        report['error_type']=type(exc).__name__
        report['checks']['tk_lifecycle']='FAIL'
    finally:
        if app is not None:
            try:app.destroy()
            except Exception as exc:
                report['checks']['destroy']='FAIL'
                report['error_type']=type(exc).__name__
                report['status']='FAIL'
        destination=Path(output)
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if report['status']=='PASS' else 1
