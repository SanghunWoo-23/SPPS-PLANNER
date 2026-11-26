"""Ephemeral Windows CI only: silent install, packaged self-test, uninstall.

Never run against a user's installed application or data. The --ci-sandbox and
CI=true safeguards are mandatory. Does not assert production acceptance.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--installer',required=True)
    parser.add_argument('--ci-sandbox',action='store_true')
    parser.add_argument('--report',required=True)
    args=parser.parse_args(argv)
    report={'app_version':'V9.0.0','platform':platform.platform(),'checks':{},'status':'NOT_TESTED'}
    if (platform.system()!='Windows' or not args.ci_sandbox
            or os.getenv('CI','').lower()!='true' or os.getenv('GITHUB_ACTIONS','').lower()!='true'):
        report['reason']='Requires a Windows ephemeral CI worker and explicit --ci-sandbox.'
        print(json.dumps(report,indent=2))
        return 2
    installer=Path(args.installer).resolve()
    if not installer.is_file():
        raise FileNotFoundError(installer)
    with tempfile.TemporaryDirectory(prefix='spps-v9-installer-ci-') as tmp:
        destination=Path(tmp)/'Installed App'
        log=Path(tmp)/'setup.log'
        isolated_data=Path(tmp)/'user-data'
        isolated_data.mkdir()
        sentinel=isolated_data/'preserve-this-user-file.txt'
        sentinel.write_text('SPPS V9 isolated test data — do not remove',encoding='utf-8')
        cmd=[str(installer),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',
             f'/DIR={destination}',f'/LOG={log}']
        install=subprocess.run(cmd,capture_output=True,text=True,timeout=200)
        report['checks']['silent_install']='PASS' if install.returncode==0 else f'FAIL:{install.returncode}'
        application=destination/'SPPS_Planner.exe'
        if install.returncode==0 and application.exists():
            report['checks']['installed_binary_exists']='PASS'
            env=os.environ.copy()
            env['SPPS_PLANNER_SELFTEST_OUTPUT']=str(Path(tmp)/'selftest.json')
            env['SPPS_PLANNER_USER_DATA']=str(isolated_data)
            env['SPPS_PLANNER_GUI_SMOKE_OUTPUT']=str(Path(tmp)/'gui-smoke.json')
            try:
                check=subprocess.run([str(application),'--self-test'],cwd=destination,
                                     capture_output=True,text=True,env=env,timeout=120)
                report['checks']['installed_selftest']='PASS' if check.returncode==0 else f'FAIL:{check.returncode}'
                if Path(env['SPPS_PLANNER_SELFTEST_OUTPUT']).is_file():
                    result=json.loads(Path(env['SPPS_PLANNER_SELFTEST_OUTPUT']).read_text(encoding='utf-8'))
                    if result.get('app_version')!='V9.0.0' or result.get('ok') is not True:
                        report['checks']['installed_selftest']='FAIL:bad_report'
            except (subprocess.TimeoutExpired, OSError,ValueError) as exc:
                report['checks']['installed_selftest']=f'FAIL:{type(exc).__name__}'
            try:
                gui=subprocess.run([str(application),'--gui-smoke'],cwd=destination,
                                   capture_output=True,text=True,env=env,timeout=120)
                record_path=Path(env['SPPS_PLANNER_GUI_SMOKE_OUTPUT'])
                record=json.loads(record_path.read_text(encoding='utf-8')) if record_path.exists() else {}
                report['checks']['installed_gui_lifecycle'] = ('PASS' if gui.returncode==0 and
                    record.get('status')=='PASS' and record.get('app_version')=='V9.0.0'
                    else f'FAIL:exit={gui.returncode},report={record.get("status")}')
            except (subprocess.TimeoutExpired,OSError,ValueError) as exc:
                report['checks']['installed_gui_lifecycle']=f'FAIL:{type(exc).__name__}'
        else:
            report['checks']['installed_binary_exists']='FAIL:missing'
        uninstall=destination/'unins000.exe'
        if uninstall.is_file():
            try:
                removal=subprocess.run([str(uninstall),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],
                    cwd=tmp,capture_output=True,text=True,timeout=160)
                report['checks']['silent_uninstall']='PASS' if removal.returncode==0 else f'FAIL:{removal.returncode}'
            except (subprocess.TimeoutExpired, OSError) as exc:
                report['checks']['silent_uninstall']=f'FAIL:{type(exc).__name__}'
        else:
            report['checks']['silent_uninstall']='FAIL:missing_uninstaller'
        # Verify the isolated installation is removed but its independent user
        # data directory is not silently erased by the uninstaller.
        report['checks']['binary_removed_after_uninstall']=('PASS' if not application.exists()
            and report['checks'].get('silent_uninstall')=='PASS' else 'FAIL')
        report['checks']['user_data_preserved']=('PASS' if sentinel.is_file() and
            sentinel.read_text(encoding='utf-8')=='SPPS V9 isolated test data — do not remove' else 'FAIL')
        report['status']='PASS' if report['checks'] and all(x=='PASS' for x in report['checks'].values()) else 'FAIL'
    target=Path(args.report);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,indent=2))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':
    raise SystemExit(main())
