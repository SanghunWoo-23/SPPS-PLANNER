"""Audit V9 source layout and current documentation without importing the GUI.

This is a source-quality audit, not a Windows runtime or scientific validation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
ROOT_ENTRIES = (
    'README.md', 'README_KO.md', 'README_V9_DEVELOPMENT.md',
    'VERSION', 'VERSION.txt', 'LICENSE', 'main_launcher.py',
    'suite_gui', 'apps', 'tools', 'tests', 'docs',
)
CURRENT_DOCS = (
    'docs/INDEX.md', 'docs/CURRENT_STATUS_KO.md',
    'docs/SOURCE_LAYOUT_KO.md', 'docs/ARCHITECTURE.md',
    'docs/USER_MANUAL_EN.md', 'docs/USER_MANUAL_KO.md',
)
ARCHIVE_DIR = Path('docs/history')
# Only link check docs that describe the current package. Historical notes are
# intentionally preserved but can describe superseded file layouts.
LINK_RE = re.compile(r'(?<!!)\[[^\]]+\]\(([^)]+)\)')
SKIP_LINK_PREFIXES = ('http:', 'https:', 'mailto:', 'data:', '#')
BLOCKED_ARTIFACTS = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.venv', 'build', 'dist'}
BLOCKED_NAMES = {'.DS_Store', 'Thumbs.db', 'runtime_selftest.json', 'WINDOWS_INSTALLER_ACCEPTANCE_V9.json'}


def audit(root: Path) -> dict:
    root = root.resolve()
    errors: list[str] = []
    for rel in ROOT_ENTRIES + CURRENT_DOCS:
        if not (root / rel).exists():
            errors.append(f'Missing required source/document: {rel}')
    history = root / ARCHIVE_DIR
    if not (history / 'README.md').is_file() or not (history / 'README_V9_LEGACY_DEVELOPMENT.md').is_file():
        errors.append('Historical notes directory or previous V9 cumulative log missing')
    for f in root.rglob('*'):
        # Local test execution creates caches; source packaging excludes them.
        # Audit the managed source candidates, not transient interpreter caches.
        if set(f.relative_to(root).parts) & BLOCKED_ARTIFACTS or f.name in BLOCKED_NAMES:
            continue
        if f.is_symlink():
            errors.append(f'Symbolic link in source package: {f.relative_to(root).as_posix()}')
    # Existing imports and build tools depend on these stable top-level paths.
    for required in ('suite_gui/classic_base.py',
                     'apps/spps_planner_app/spps_planner/engine.py',
                     'tools/verify_windows_release.py'):
        if not (root/required).is_file():
            errors.append(f'Relocated runtime/build module: {required}')
    check_pages = [root / rel for rel in ('README.md', 'README_KO.md', 'README_V9_DEVELOPMENT.md')]
    check_pages += sorted((root/'docs').glob('*.md'))
    # Strip fenced blocks; hyperlinks in quoted code samples are not navigation.
    for doc in check_pages:
        if not doc.is_file():
            continue
        content = re.sub(r'```.*?```', '', doc.read_text(encoding='utf-8'), flags=re.S)
        for link in LINK_RE.findall(content):
            target = link.strip().split()[0].strip('<>')
            if target.startswith(SKIP_LINK_PREFIXES):
                continue
            # URI percent-unescape only. No symbolic file path resolution outside root.
            target = unquote(target.split('#')[0].split('?')[0])
            if not target:
                continue
            resolved = (doc.parent/target).resolve()
            if not resolved.is_relative_to(root) or not resolved.exists():
                errors.append(f'Broken documentation link: {doc.relative_to(root).as_posix()} -> {target}')
    return {
        'project': 'SPPS Planner', 'version': (root/'VERSION').read_text(encoding='utf-8').strip() if (root/'VERSION').exists() else None,
        'status': 'PASS' if not errors else 'FAIL',
        'files': sum(f.is_file() and f.name not in BLOCKED_NAMES and not(set(f.relative_to(root).parts) & BLOCKED_ARTIFACTS) for f in root.rglob('*')),
        'historical_documents': sum(f.is_file() and f.suffix.lower()=='.md' for f in history.rglob('*')) if history.exists() else 0,
        'current_documentation_pages_checked': len(check_pages),
        'errors': errors,
        'scope_note': 'Source layout and links only; no Windows installation or wet-lab validation.',
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--report', type=Path)
    args = p.parse_args(argv)
    result = audit(args.root)
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding='utf-8')
    return int(result['status'] != 'PASS')


if __name__ == '__main__':
    sys.exit(main())
