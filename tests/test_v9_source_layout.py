"""Tests for source layout and documentation; no network/GUI/experiment access."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from audit_repository_layout_v9 import audit


def test_actual_release_source_layout_passes():
    result = audit(ROOT)
    assert result['errors'] == []
    assert result['status'] == 'PASS'


def test_current_and_archived_documents_are_distinct():
    assert (ROOT/'docs/INDEX.md').is_file()
    assert (ROOT/'docs/history/README.md').is_file()
    assert (ROOT/'docs/history/README_V9_LEGACY_DEVELOPMENT.md').is_file()
    assert 'Current Development Scope' in (ROOT/'README_V9_DEVELOPMENT.md').read_text(encoding='utf-8')


def test_broken_link_is_reported(tmp_path):
    from shutil import copytree
    # Small independent fixture copied from real source, for link validation.
    r = tmp_path/'source'
    for dir in ('suite_gui', 'apps/spps_planner_app/spps_planner', 'tools', 'tests', 'docs/history'):
        (r/dir).mkdir(parents=True, exist_ok=True)
    for file in ('README.md','README_KO.md','README_V9_DEVELOPMENT.md','VERSION','VERSION.txt','LICENSE','main_launcher.py',
                 'suite_gui/classic_base.py','apps/spps_planner_app/spps_planner/engine.py','tools/verify_windows_release.py',
                 'docs/INDEX.md','docs/CURRENT_STATUS_KO.md','docs/SOURCE_LAYOUT_KO.md','docs/ARCHITECTURE.md',
                 'docs/USER_MANUAL_EN.md','docs/USER_MANUAL_KO.md','docs/history/README.md','docs/history/README_V9_LEGACY_DEVELOPMENT.md'):
        (r/file).write_text('V9.0.0\n',encoding='utf-8')
    (r/'README.md').write_text('[broken](missing.md)',encoding='utf-8')
    result=audit(r)
    assert any('Broken documentation link' in error for error in result['errors'])


def test_runtime_file_removed_is_rejected(tmp_path):
    result = audit(tmp_path)
    assert any('Relocated runtime/build module' in e for e in result['errors'])


def test_no_duplicate_v9_historical_guides_in_active_root():
    current = {x.name for x in (ROOT/'docs').glob('V9_*.md')}
    assert current == {'V9_DEPENDENCY_LICENSE_NOTICE.md'}


def test_old_notes_preserved_not_deleted():
    historic = list((ROOT/'docs/history').glob('V9_*.md'))
    assert len(historic) >= 20


def test_no_build_artifacts_in_release():
    result = audit(ROOT)
    assert not any('Generated artifact committed' in e for e in result['errors'])
