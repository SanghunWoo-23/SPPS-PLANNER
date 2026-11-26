"""Public V9 source release integrity/preflight; Python standard library only.

Checks actual checked-out source; never reads/exports an experiment workbook or a
local model. Strict failure means the release package MUST NOT be published.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
VERSION = "V9.0.0"
MANIFEST = "SOURCE_MANIFEST.sha256"
REQUIRED = (
    "README.md", "README_KO.md", "VERSION", "VERSION.txt", "LICENSE",
    "CITATION.cff", ".gitignore", ".gitattributes", "requirements.txt",
    "requirements-dev.txt", "requirements-rdkit-optional.txt", "main_launcher.py",
    "INSTALL_BUILD_TOOLS_AND_BUILD.bat", ".github/workflows/ci.yml",
    ".github/workflows/github-source-preflight.yml",
    "tools/github_release_preflight_v9.py", "tools/build_github_source_release_v9.py",
    "PUBLIC_DATA_POLICY.md", "docs/INDEX.md", "docs/CURRENT_STATUS_KO.md",
    "docs/SOURCE_LAYOUT_KO.md", "tools/audit_repository_layout_v9.py",
)
BLOCKED_PARTS = {
    ".git", ".env", "private_data", "private_experiments",
    "user_experiments", "local_models", "__pycache__", ".pytest_cache",
    "build", "dist", "runtime_logs", "outputs", "models",
    ".venv", "venv", ".tox",
}
BLOCKED_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".pkl", ".pickle", ".joblib", ".exe", ".dll", ".pem", ".key"}
SKIP_PARTS = {"__pycache__", ".pytest_cache", ".git", ".ruff_cache", ".mypy_cache"}
SKIP_GENERATED = {"runtime_selftest.json", "WINDOWS_INSTALLER_ACCEPTANCE_V9.json"}


def inventory(root: Path) -> list[Path]:
    """Sorted tracked-source candidates, excluding generated caches and manifest."""
    result = []
    for f in root.rglob("*"):
        if not f.is_file() and not f.is_symlink():
            continue
        relative = f.relative_to(root)
        if relative.as_posix() == MANIFEST or relative.name in SKIP_GENERATED or set(relative.parts) & SKIP_PARTS or f.suffix == ".pyc":
            continue
        result.append(relative)
    return sorted(result, key=lambda p: p.as_posix())


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for part in iter(lambda: fp.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def make_manifest(root: Path) -> str:
    return "".join(f"{file_hash(root / rel)}  {rel.as_posix()}\n" for rel in inventory(root))


def _issues(root: Path, *, strict: bool = True) -> list[str]:
    issues = []
    for needed in REQUIRED:
        if not (root / needed).is_file():
            issues.append(f"missing required source: {needed}")
    for version_path in ("VERSION", "VERSION.txt"):
        file = root / version_path
        if file.is_file() and file.read_text(encoding="utf-8").strip() != VERSION:
            issues.append(f"wrong version: {version_path}")
    for rel in inventory(root):
        p = root / rel
        lower = [item.lower() for item in rel.parts]
        if p.is_symlink():
            issues.append(f"symlink not allowed in public release: {rel}")
            continue
        if set(lower) & BLOCKED_PARTS:
            issues.append(f"private/runtime path: {rel}")
        if p.suffix.lower() in BLOCKED_SUFFIXES or p.name.lower().startswith(".env"):
            issues.append(f"private/executable file type: {rel}")
        if "experimental_seed" in lower and p.name != "README.md":
            issues.append(f"experimental seed data in public release: {rel}")
        if p.stat().st_size > 30 * 1024 * 1024:
            issues.append(f"unexpected >30 MiB file: {rel}")
    runs = root / "apps/spps_planner_app/data/actual_runs.csv"
    if runs.exists() and len(runs.read_text(encoding="utf-8-sig").splitlines()) > 1:
        issues.append("actual_runs.csv includes rows; it must be an empty public template")
    license_file = root / "LICENSE"
    if license_file.is_file():
        content = license_file.read_text(encoding="utf-8")
        if "not an OSI-approved open-source license" not in content:
            issues.append("custom license warning must be retained")
    citation = root / "CITATION.cff"
    if citation.is_file() and not re.search(r'^version:\s*["\']?9\.0\.0', citation.read_text(encoding="utf-8"), re.M):
        issues.append("CITATION.cff version is not 9.0.0")
    if strict:
        manifest = root / MANIFEST
        if not manifest.is_file():
            issues.append(f"missing SHA-256 manifest: {MANIFEST}")
        elif manifest.read_text(encoding="utf-8") != make_manifest(root):
            issues.append("SHA-256 manifest mismatch (source changed, missing, or extra file)")
    return issues


def validate(root: Path, *, strict: bool = True) -> dict:
    root = root.resolve()
    errors = _issues(root, strict=strict)
    return {"project": "SPPS Planner", "version": VERSION,
            "kind": "public-source-preflight", "passed": not errors,
            "source_files": len(inventory(root)), "errors": errors,
            "windows_native_tested": False, "wet_lab_validated": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true", default=False,
                        help="verify the exact source-file SHA-256 manifest")
    parser.add_argument("--write-manifest", action="store_true",
                        help="maintainer only: refresh manifest AFTER reviewed changes")
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.write_manifest:
        root = args.root.resolve()
        (root / MANIFEST).write_text(make_manifest(root), encoding="utf-8")
    report = validate(args.root, strict=args.strict)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
