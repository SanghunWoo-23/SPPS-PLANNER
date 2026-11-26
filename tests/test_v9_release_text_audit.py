"""V9 release TXT/BAT metadata regression checks, no GUI or network."""
from __future__ import annotations

from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from audit_release_text_v9 import TEXT_FILES, audit


def fixture(tmp_path: Path) -> Path:
    target = tmp_path / ROOT.name
    for rel in TEXT_FILES:
        source = ROOT / rel
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    if 'PRIVATE' not in ROOT.name:
        for rel in ('CITATION.cff','.github/workflows/github-source-preflight.yml','PUBLIC_DATA_POLICY.md'):
            source=ROOT/rel; dest=target/rel; dest.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source,dest)
    return target


def test_current_root_text_contract():
    result = audit(ROOT)
    assert result['passed'], result['errors']
    assert result['checked_text_files'] >= 16


def test_installer_version_mismatch_is_rejected(tmp_path):
    target=fixture(tmp_path)
    file=target/'installer/SPPS_Planner_Setup.iss'
    file.write_text(file.read_text(encoding='utf-8').replace('#define MyAppVersion "9.0.0"','#define MyAppVersion "8.0.0"'), encoding='utf-8')
    assert any('Inno Setup MyAppVersion' in e for e in audit(target)['errors'])


def test_missing_runtime_dependency_is_rejected(tmp_path):
    target=fixture(tmp_path)
    file=target/'requirements.txt'
    file.write_text('pandas>=2.0\npypdf>=5.0\n', encoding='utf-8')
    assert any('RDKit is required' in e for e in audit(target)['errors'])


def test_second_bat_entrypoint_rejected(tmp_path):
    target=fixture(tmp_path)
    (target/'BUILD_INSTALLER.bat').write_text('@echo off\n', encoding='utf-8')
    assert any('one supported root Windows BAT' in e for e in audit(target)['errors'])


def test_wrong_release_text_encoding_is_reported(tmp_path):
    target=fixture(tmp_path)
    (target/'RELEASE_NOTES_V9.0.0.txt').write_bytes(b'\xff\xf0')
    assert any('Cannot read UTF-8' in e for e in audit(target)['errors'])


def test_wrong_version_txt_is_rejected(tmp_path):
    target=fixture(tmp_path)
    (target/'VERSION.txt').write_text('V8.0.0\n', encoding='utf-8')
    assert any('VERSION.txt' in e and 'Version mismatch' in e for e in audit(target)['errors'])


def test_installer_filename_mismatch_is_rejected(tmp_path):
    target = fixture(tmp_path)
    file = target / 'installer/SPPS_Planner_Setup.iss'
    source = file.read_text(encoding='utf-8')
    file.write_text(source.replace('Setup_V9.0.0', 'Setup_V8.0.0'), encoding='utf-8')
    assert any('Inno Setup output filename differs' in e for e in audit(target)['errors'])

def test_build_bat_filename_mismatch_is_rejected(tmp_path):
    target = fixture(tmp_path)
    file = target / 'INSTALL_BUILD_TOOLS_AND_BUILD.bat'
    source = file.read_text(encoding='utf-8-sig')
    file.write_text(source.replace('Setup_V9.0.0.exe', 'Setup_V8.0.0.exe'), encoding='utf-8')
    assert any('Windows BAT installer filename differs' in e for e in audit(target)['errors'])
