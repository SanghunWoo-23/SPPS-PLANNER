<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner icon" width="150">

# SPPS Planner

### From peptide sequence to an editable, export-ready synthesis plan

Desktop workflow software for planning **solid-phase peptide synthesis (SPPS)**,
calculating materials, managing multiple peptides, and exporting operator-ready
records.

[![Release](https://img.shields.io/badge/release-V3.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#quick-start)
[![Tests](https://img.shields.io/badge/regression_tests-149%20passed-16A34A?style=for-the-badge)](#verification)

**[한국어](README_KO.md) · [Quick start](#quick-start) · [Features](#what-it-does) · [Build](#build-for-windows) · [Architecture](docs/ARCHITECTURE.md)**

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

See the [V3 development roadmap (KO)](docs/V3_DEVELOPMENT_ROADMAP_KO.md)
for the staged implementation scope and current status.

Through Stage 6/6, V3 provides the independent Work Item window, execution and
ML ledgers, a Project → Work Item → Run hierarchy, and a Data / HPLC workspace.
Multiple synthesis runs remain separate, HPLC results and source files are
linked, and the complete hierarchy round-trips through a multi-sheet workbook.
Risk Review adds explained rule findings and real-data ML signals only when a
valid reviewed-data model exists.
The completed hybrid UI adds responsive sizing, three display densities,
keyboard operation, Windows DPI handling and a fully versioned build path.

| Area | Capabilities |
| --- | --- |
| **Project Manager** | Manage multiple peptides, duplicate/delete/reorder items, preserve per-peptide inputs and calculated outputs |
| **Sequence processing** | Interpret terminal groups, amino acids, D/non-natural residues, chemicals, modifiers, tags, labels, and linkers |
| **Resin & loading** | Rink Amide families, 2-CTC direct loading, preloaded `CTC(합성기)`, Wang, HMPB, Sieber Amide, PAL, Tentagel, and Manual profiles |
| **Synthesis Plan** | Generate coupling/deprotection/wash operations and directly edit unit, MW, density, eq, reagent, solvent, and repeat values |
| **Apply Change** | Recalculate from the visible edited Plan without silently regenerating it from the original sequence |
| **Materials** | Calculate resin, amino acids, coupling reagents, catalysts, bases, solvents, modifiers, and cleavage components |
| **Doubling & repeats** | Position-based doubling plus repeat values beyond 2×, synchronized through materials and checklist outputs |
| **Live execution records** | Record step status, actual material amount/status, Plan corrections, doubling, reasons, and operator notes in an append-only event ledger |
| **Compensating revert** | Restore Plan values and linked results by appending an inverse event without deleting the original record |
| **Cleavage** | Presets and custom cocktail composition with mass/volume display policies for liquid and solid components |
| **Batch Manager** | Edit regions/linkers/tags/labels, synchronize Project rows, and calculate peptide-level and batch-level protected-reagent requirements |
| **Records & export** | Autosave sessions and export CSV/XLSX/JSON records with project, peptide, and LOT information |
| **Project data system** | Multiple Runs per Work Item, atomic JSON, last-good recovery, recent files, and external-edit conflict protection |
| **Excel workbook** | Round-trip Project, Runs, Plan, events, ML, HPLC, materials, totals, checklist, cleavage, history, and column mappings |
| **HPLC linkage** | Searchable/sortable results, analysis metadata, audit history, and path/size/time/SHA-256 links to data and method files |
| **Custom DB** | Add, update, and delete user materials with class, MW, density, and notes |
| **Observed-data ML** | Derive features from execution history and train/predict only from at least five included reviewed yield, purity, failure, or doubling outcomes |
| **ML data review** | Preserve outcome revisions, inclusion/exclusion reasons, immutable dataset snapshots, fingerprints, manifests, and model metadata |
| **Synthesis risk review** | Explained aspartimide, aggregation, difficult-coupling, oxidation/protection and execution-history rules plus real-data ML signals and per-Run audit revisions |
| **Final UI & Windows** | Responsive windows, three display densities, keyboard access, DPI handling, V3 EXE/Installer metadata, and automated build validation |
| **V2-speed interaction** | Debounced autosave/live sync, cached Batch results, one engine Plan per Batch item, and one-click linked-result rendering |

## Operator-focused behavior

- **Generate** creates or recreates Plan, Materials, Checklist and Total Materials together from the current inputs.
- **Apply Change** preserves manual Plan edits, updates connected results, and remains the explicit action that applies Cleavage.
- Empty sequence fields stay empty—no fake peptide or placeholder Plan is injected.
- Chemistry preset buttons update conditions without unexpectedly generating rows.
- `2-CTC` direct-loading rows retain loading AA/DIEA chemistry instead of being
  converted into ordinary DIC/HOBt coupling rows.
- Legacy saved `CTC(합성용)` values migrate to `CTC(합성기)`.
- Static unit-name normalization remains a static method through the final Classic controller, preventing the Generate-time argument mismatch.
- Natural, D, and non-natural amino acids are shown with their full protected `Fmoc-AA-OH` bottle names in Plan choices and Batch preparation tables; one- and three-letter material labels are not exposed.
- Linker choices distinguish exact commercial end-group forms such as `Fmoc-NH-PEGn-CH2COOH` and `Fmoc-N-amido-PEGn-acid`, and every selectable Fmoc item is connected to a database MW and calculation route.
- Legacy saved values such as `R`, `D-R`, `dR`, `PEG4`, and `Ahx` migrate to full bottle names on load. One-letter peptide sequence input remains supported.
- The duplicate `Unit defaults → mL per mmol` input was removed. Working volume is calculated and persisted only from the Amide/Rink or 2-CTC/Trityl factor—or the molarity basis—under `Solvents / Wash`.
- Bracketed chemicals, linkers, tags, and labels remain single parser tokens; dashed residue input such as `A-C-D` is never mistaken for `Ac-`.
- Project switching saves only changed output tables, avoiding repeated full Treeview serialization on ordinary clicks.

## Quick start

See the [English user manual](docs/USER_MANUAL_EN.md) for the complete workflow
and the [Windows build guide (KO)](docs/WINDOWS_BUILD_KO.md) for source builds.

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
installer\output\SPPS_Planner_Setup_V3.0.0.exe
```

## Project structure

```text
SPPS-Planner/
├─ main_launcher.py              # Application entry point
├─ suite_gui/                    # Tkinter UI and workflow controllers
│  ├─ controller.py              # Direct V3.0.0 runtime controller
│  ├─ classic_base.py            # Static retained Classic UI base
│  ├─ position_rules.py          # C-terminal eq/repeat rules
│  ├─ modules/                   # Semantic Plan, operator, and release workflows
│  ├─ release.py                 # Canonical public GUI entry
│  └─ release_contract.py        # Active-route validation
├─ apps/spps_planner_app/
│  ├─ spps_planner/              # Parser, engine, database, and export
│  └─ data/                      # Bundled process and reagent data
├─ tests/                        # Regression and behavior contracts
├─ tools/                        # Release and source-audit utilities
├─ docs/                         # Architecture and data contracts
└─ installer/                    # Inno Setup configuration
```

See [Architecture](docs/ARCHITECTURE.md) for the complete direct execution
flow. Numbered compatibility modules and the legacy controller are no longer
part of the source tree, and the release audit requires zero runtime controller
rebinding.

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
repeat cycles, material ordering, project items, persistence, immediate Custom
DB reflection, observed synthesis logging/ML routing, and release routing.
Risk rules, real classifier probabilities, assessment acknowledgement history,
and risk-sheet workbook round trips are also covered.

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

This repository is the fixed public release **SPPS Planner V3.0.0**.
Historical internal version names remain only where required to preserve
accepted behavior and import compatibility.

## License

See [LICENSE](LICENSE). This project uses a custom public academic citation
license and is not presented as an OSI-approved open-source license.

---

<div align="center">

**SPPS Planner V3.0.0**  
Practical peptide-synthesis planning with editable, traceable calculations.

</div>
