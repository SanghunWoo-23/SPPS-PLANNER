<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner icon" width="150">

# SPPS Planner V4.0.0

**Desktop planning software for solid-phase peptide synthesis (SPPS)**

Sequence parsing · editable synthesis plans · materials · checklist · batch workflow · experimental-data recommendations

[![Release](https://img.shields.io/badge/release-V4.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#quick-start)

**[한국어](README_KO.md) · [User Manual](docs/USER_MANUAL_EN.md) · [Architecture](docs/ARCHITECTURE.md) · [Windows Build](docs/WINDOWS_BUILD_KO.md)**

</div>

---

## Overview

SPPS Planner converts a peptide design and synthesis settings into an editable, traceable workflow. The generated Plan remains user-editable, and **Apply Change** recalculates connected outputs from the visible Plan instead of silently regenerating the original sequence.

V4.0.0 also adds an experimental-data layer for locally recorded Loading, Coupling, and Cleavage results. Recommendations are evidence-first: repeated historical conditions are preferred, model-based advice is limited by available reviewed data, and the public build contains no private experimental history.

```text
Sequence / modifiers / branch settings
                ↓
Resin · scale · loading · coupling chemistry
                ↓
           Generate
                ↓
Plan · Materials · Checklist · Total Materials
                ↓
        manual Plan edits
                ↓
          Apply Change
```

## Main features

- **Sequence processing** — terminal groups, D/non-natural residues, chemicals, linkers, labels, tags, and protected bottle-level building blocks.
- **Resin & loading** — Rink Amide families, 2-CTC direct loading, Wang, HMPB, Sieber Amide, PAL, Tentagel, and manual profiles.
- **Editable synthesis Plan** — coupling, deprotection, washing, loading, terminal modification, repeat, and doubling workflows.
- **Materials / Checklist / Totals** — synchronized calculations from the active Plan.
- **Cleavage planning** — presets and custom cocktails with component-specific mass/volume handling.
- **Branch support** — branched synthesis settings and orthogonal protecting-group workflow support.
- **Project & Batch management** — multiple peptide items, saved state, batch calculations, and export.
- **Custom DB** — user-defined amino acids, chemicals, reagents, catalysts/additives, bases, solvents, resins, and other materials.
- **Experimental Data** — record/import Loading, Coupling, and Cleavage results into a local knowledge base.
- **Recommendations** — exact/repeated historical consensus first, then conservative data-driven or chemistry-rule guidance when supported.
- **Windows release tooling** — PyInstaller portable build, packaged runtime self-test, and Inno Setup installer workflow.

## Public data policy

This GitHub distribution is intentionally **data-sanitized**. It includes the schema, import/record UI, recommendation engine, and empty runtime templates, but it does not bundle private/company experimental history or private product-to-sequence mappings.

Runtime data is written outside the repository under a public-build-specific user directory. See [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md).

## Quick start

### Requirements

- Windows 10 or 11
- 64-bit Python 3.11 or 3.12

### Run from source

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main_launcher.py
```

## Build for Windows

### Portable EXE

```bat
BUILD_EXE_ONLY.bat
```

Expected output:

```text
dist\SPPS_Planner\SPPS_Planner.exe
```

### Installer

With Inno Setup installed:

```bat
BUILD_INSTALLER.bat
```

Or install/check build dependencies and build in one step:

```bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

Expected output:

```text
installer\output\SPPS_Planner_Setup_V4.0.0.exe
```

The build scripts distinguish source validation, PyInstaller creation, packaged runtime self-test, and installer validation so a failed post-build check is not reported as a missing EXE.

## Repository structure

```text
SPPS-Planner/
├─ main_launcher.py              # Desktop entry point
├─ suite_gui/                    # Tkinter UI and workflow controllers
├─ apps/spps_planner_app/
│  ├─ spps_planner/              # Parser, calculation engine, database, export
│  └─ data/                      # Public reagent/process defaults and empty templates
├─ tests/                        # Regression and behavior contracts
├─ tools/                        # Release/build/source-audit utilities
├─ docs/                         # User, architecture, parser, and data documentation
├─ installer/                    # Inno Setup configuration
├─ requirements.txt
└─ requirements-dev.txt
```

## Runtime data

The public build keeps user-generated data outside the repository. On Windows, the core data directory is based on:

```text
%LOCALAPPDATA%\SPPS_Planner_PUBLIC\
```

Session-state components use their corresponding public-build user directory. Experimental databases, imported lab data, models, logs, and outputs should never be committed to Git.

## Verification

Install development requirements and run the release verification:

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
python tools\verify_windows_release.py
```

Audit the active release for prohibited runtime rebinding:

```bat
python tools\audit_monkey_patches.py --active-release
```

The test suite covers sequence/parser behavior, Generate/Apply Change, loading, coupling, cleavage, doubling/repeats, materials/checklist/totals, persistence, experimental-data workflows, recommendation safety, and Windows release contracts.

## Documentation

- [English user manual](docs/USER_MANUAL_EN.md)
- [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Parser contract](docs/SPPS_PARSER_CONTRACT.md)
- [Reagent database schema](docs/SPPS_REAGENT_DATABASE_SCHEMA.md)
- [Experimental Data / ML guide (KO)](docs/V4_EXPERIMENTAL_ML_KO.md)
- [Windows build guide (KO)](docs/WINDOWS_BUILD_KO.md)
- [Public data policy](PUBLIC_DATA_POLICY.md)

## Version

Current public release: **V4.0.0**.

## License

See [LICENSE](LICENSE). The repository uses its included custom public academic citation license; do not describe it as an OSI-approved open-source license unless the license is changed accordingly.
