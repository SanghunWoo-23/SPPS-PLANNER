<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner icon" width="150">

# SPPS Planner

### From peptide sequence to an editable, export-ready synthesis plan

Desktop workflow software for planning **solid-phase peptide synthesis (SPPS)**,
calculating materials, managing multiple peptides, and exporting operator-ready
records.

[![Release](https://img.shields.io/badge/release-V2.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#quick-start)
[![Tests](https://img.shields.io/badge/regression_tests-61%20passed-16A34A?style=for-the-badge)](#verification)

**[한국어](README_KO.md) · [English Manual](docs/USER_MANUAL_EN.md) · [한국어 매뉴얼](docs/USER_MANUAL_KO.md) · [Quick start](#quick-start) · [Features](#what-it-does) · [Build](#build-for-windows)**

</div>

---

## Why SPPS Planner?

SPPS planning is more than converting a sequence into amino-acid weights.
Resin type, loading, coupling chemistry, repeat cycles, deprotection, washing,
terminal modifications, cleavage cocktails, and manual operator edits all need
to remain synchronized.

SPPS Planner keeps those decisions in one workflow:

```text
Peptide sequence
      ↓
Resin · scale · loading · chemistry
      ↓
Editable synthesis Plan
      ↓
Apply Change
      ↓
Materials · Checklist · Totals · Batch · Export
```

## What it does

| Area | Capabilities |
| --- | --- |
| **Project Manager** | Manage multiple peptides, duplicate/delete/reorder items, preserve per-peptide inputs and calculated outputs |
| **Sequence processing** | Interpret terminal groups, amino acids, D/non-natural residues, chemicals, modifiers, tags, labels, and linkers |
| **Resin & loading** | Rink Amide families, 2-CTC direct loading, preloaded `CTC(합성기)`, Wang, HMPB, Sieber Amide, PAL, Tentagel, and Manual profiles |
| **Synthesis Plan** | Generate coupling/deprotection/wash operations and directly edit unit, MW, density, eq, reagent, solvent, and repeat values |
| **Apply Change** | Recalculate from the visible edited Plan without silently regenerating it from the original sequence |
| **Materials** | Calculate resin, amino acids, coupling reagents, catalysts, bases, solvents, modifiers, and cleavage components |
| **Doubling & repeats** | Position-based doubling plus repeat values beyond 2×, synchronized through materials and checklist outputs |
| **Cleavage** | Presets and custom cocktail composition with mass/volume display policies for liquid and solid components |
| **Batch Manager** | Consolidate multiple projects and calculate peptide-level and batch-level material requirements |
| **Records & export** | Autosave sessions and export CSV/XLSX/JSON records with project, peptide, and LOT information |
| **Custom DB** | Add, update, and delete user materials with class, MW, density, and notes |

## Operator-focused behavior

- **Generate** intentionally creates or recreates a Plan from the current inputs.
- **Apply Change** preserves manual Plan edits and updates connected results.
- Empty sequence fields stay empty—no fake peptide or placeholder Plan is injected.
- Chemistry preset buttons update conditions without unexpectedly generating rows.
- `2-CTC` direct-loading rows retain loading AA/DIEA chemistry instead of being
  converted into ordinary DIC/HOBt coupling rows.
- Legacy saved `CTC(합성용)` values migrate to `CTC(합성기)`.

## Quick start

New users should read the
**[Detailed English User Manual](docs/USER_MANUAL_EN.md)**.
The **[Korean manual](docs/USER_MANUAL_KO.md)** is also available.

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

### Portable application

```bat
BUILD_EXE_ONLY.bat
```

Output:

```text
dist\SPPS_Planner\SPPS_Planner.exe
```

### Windows installer

Install [Inno Setup](https://jrsoftware.org/isinfo.php), then run:

```bat
BUILD_INSTALLER.bat
```

Output:

```text
installer\output\SPPS_Planner_Setup_V2.0.0.exe
```

## Project structure

```text
SPPS-Planner/
├─ main_launcher.py              # Application entry point
├─ suite_gui/                    # Tkinter UI and workflow controllers
│  ├─ modules/                   # Plan, operator, and release workflows
│  ├─ release.py                 # Canonical public GUI entry
│  ├─ release_composition.py     # Explicit release-layer order
│  └─ release_contract.py        # Active-route validation
├─ apps/spps_planner_app/
│  ├─ spps_planner/              # Parser, engine, database, and export
│  └─ data/                      # Bundled process and reagent data
├─ tests/                        # Regression and behavior contracts
├─ tools/                        # Release and source-audit utilities
├─ docs/                         # Architecture and data contracts
└─ installer/                    # Inno Setup configuration
```

See [Architecture](docs/ARCHITECTURE.md) for the complete execution flow and
the boundary between compatibility code and active workflows.

### Documentation

- [Detailed User Manual — English](docs/USER_MANUAL_EN.md)
- [상세 사용자 매뉴얼 — 한국어](docs/USER_MANUAL_KO.md)
- Plain-text copies: [English TXT](docs/USER_MANUAL_EN.txt) · [한국어 TXT](docs/USER_MANUAL_KO.txt)
- [Architecture and execution flow](docs/ARCHITECTURE.md)

## Session and Custom DB

The normal Windows autosave location is:

```text
%LOCALAPPDATA%\SPPS Planner\spps_planner_session_v1.json
```

To reset the restored session, close SPPS Planner and remove this file.

Custom materials are available under:

```text
Project Manager → Show setup → Custom DB
```

Supported classes include AA/Chemical, coupling reagent, catalyst/additive,
base, solvent, cleavage cocktail, resin, and other materials.

## Verification

The final release includes fixed calculation snapshots and focused contracts
for Plan generation, Apply Change, 2-CTC loading, terminal behavior, doubling,
repeat cycles, material ordering, project items, persistence, and release
routing.

Run the complete verification five times:

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py --passes 5
```

Audit only the routes active in the final controller:

```bat
python tools\audit_monkey_patches.py --active-release
```

## Version

This repository is the fixed public release **SPPS Planner V2.0.0**.
Historical internal version names remain only where required to preserve
accepted behavior and import compatibility.

## License

See [LICENSE](LICENSE). This project uses a custom public academic citation
license and is not presented as an OSI-approved open-source license.

---

<div align="center">

**SPPS Planner V2.0.0**  
Practical peptide-synthesis planning with editable, traceable calculations.

</div>
