"""Verify human-facing V9 release text, dependency and Windows build contracts.

Checks only source metadata/text; does NOT assert actual Windows installation,
experiment verification or machine-learning predictive accuracy.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

VERSION = "V9.0.0"
EXPECTED = "9.0.0"
ROOT = Path(__file__).resolve().parents[1]
TEXT_FILES = (
    "README.md", "README_KO.md", "README_V9_DEVELOPMENT.md",
    "RELEASE_NOTES_V9.0.0.txt", "requirements.txt",
    "requirements-dev.txt", "requirements-rdkit-optional.txt",
    "apps/spps_planner_app/requirements.txt", "VERSION", "VERSION.txt",
    "INSTALL_BUILD_TOOLS_AND_BUILD.bat", "installer/version_info.txt",
    "installer/SPPS_Planner_Setup.iss", "docs/INDEX.md",
    "docs/CURRENT_STATUS_KO.md", "docs/WINDOWS_BUILD_KO.md",
)


def _get(root: Path, rel: str, errors: list[str]) -> str:
    file = root / rel
    if not file.is_file():
        errors.append(f"Required text/build input missing: {rel}")
        return ""
    try:
        if file.stat().st_size > 2 * 1024 * 1024:
            errors.append(f"Unexpected oversized text/build input: {rel}")
            return ""
        return file.read_text(encoding="utf-8-sig")
    except (UnicodeError, OSError) as exc:
        errors.append(f"Cannot read UTF-8 text/build input: {rel}: {exc}")
        return ""


def audit(root: Path) -> dict:
    root = Path(root).resolve()
    errors: list[str] = []
    texts = {p: _get(root, p, errors) for p in TEXT_FILES}
    for f in ("VERSION", "VERSION.txt"):
        if texts[f].strip() != VERSION:
            errors.append(f"Version mismatch in {f}; expected {VERSION}")
    for f in ("README.md", "README_KO.md", "README_V9_DEVELOPMENT.md", "RELEASE_NOTES_V9.0.0.txt"):
        if VERSION not in texts[f]:
            errors.append(f"V9.0.0 heading/release identity missing: {f}")

    bat = texts["INSTALL_BUILD_TOOLS_AND_BUILD.bat"]
    iss = texts["installer/SPPS_Planner_Setup.iss"]
    info = texts["installer/version_info.txt"]
    if 'set "APP_VERSION=V9.0.0"' not in bat:
        errors.append("Windows BAT APP_VERSION differs from release version")
    # Compare the actual installer output contract instead of an outdated
    # shared filename: PUBLIC and PRIVATE produce different installers.
    distribution = 'PRIVATE' if 'PRIVATE' in root.name.upper() else 'PUBLIC'
    expected_filename = f"SPPS_Planner_{distribution}_Setup_{VERSION}.exe"
    match_bat = re.search(r'^set "SETUP_EXE=installer\\output\\([^"\r\n]+)"\s*$', bat, flags=re.M | re.I)
    bat_filename = match_bat.group(1) if match_bat else None
    if bat_filename != expected_filename:
        errors.append("Windows BAT installer filename differs from release version")
    if re.search(r'^#define MyAppVersion "9\.0\.0"\s*$', iss, flags=re.M) is None:
        errors.append("Inno Setup MyAppVersion differs from release version")
    match_iss = re.search(r'^OutputBaseFilename=([^\r\n]+)\s*$', iss, flags=re.M)
    iss_filename = (match_iss.group(1).strip() + '.exe') if match_iss else None
    if iss_filename != bat_filename or iss_filename != expected_filename:
        errors.append("Inno Setup output filename differs from Windows BAT")
    if "VersionInfoVersion=9.0.0.0" not in iss:
        errors.append("Inno Setup EXE version metadata differs from release version")
    if "filevers=(9, 0, 0, 0)" not in info or "prodvers=(9, 0, 0, 0)" not in info:
        errors.append("Windows file version resource differs from release version")
    if "SPPS Planner V9.0.0" not in info:
        errors.append("Windows file description differs from release version")
    # One BAT entry point avoids contradictory EXE/Installer paths.
    bats = sorted(x.name for x in root.glob('*.bat'))
    if bats != ['INSTALL_BUILD_TOOLS_AND_BUILD.bat']:
        errors.append(f"Expected one supported root Windows BAT, found {bats}")
    if r'tools\audit_release_text_v9.py' not in bat:
        errors.append("Windows BAT does not run release-text contract before packaging")

    runtime = texts["requirements.txt"]
    compatibility = texts["requirements-rdkit-optional.txt"]
    def dependency(text: str, name: str) -> bool:
        return bool(re.search(rf'^\s*{re.escape(name)}\s*(?:[<>=!~]|$)', text, flags=re.I | re.M))
    if not dependency(runtime, 'rdkit'):
        errors.append("RDKit is required by default source requirements but missing")
    if not dependency(compatibility, 'rdkit'):
        errors.append("RDKit compatibility list missing RDKit")
    if 'already includes RDKit' not in compatibility:
        errors.append("RDKit compatibility TXT misleadingly implies an additional install is required")
    if dependency(runtime, 'pypdf') is False:
        errors.append("Local PDF reader dependency pypdf missing from default requirements")

    is_private = 'PRIVATE' in root.name.upper()
    public_only = ("CITATION.cff", ".github/workflows/github-source-preflight.yml", "PUBLIC_DATA_POLICY.md")
    if not is_private:
        for file in public_only:
            if not (root / file).is_file():
                errors.append(f"Public release file missing: {file}")
        if 'source' not in texts["RELEASE_NOTES_V9.0.0.txt"].lower():
            errors.append("Public release notes do not state source distribution")
    else:
        if 'DO NOT PUBLISH' not in texts["README.md"] and 'DO NOT PUBLISH' not in texts["RELEASE_NOTES_V9.0.0.txt"]:
            errors.append("Private package missing prominent do-not-publish notice")
        if 'PRIVATE INTERNAL' not in texts["RELEASE_NOTES_V9.0.0.txt"]:
            errors.append("Private release TXT must identify internal distribution")
    return {"version": VERSION, "distribution": "private" if is_private else "public",
            "passed": not errors, "checked_text_files": len(TEXT_FILES),
            "native_windows_tested": False, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    result = audit(args.root)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    print(output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding='utf-8')
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
