<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner" width="150">

# SPPS Planner v7.0.0

**Windows-first desktop software for solid-phase peptide synthesis planning, calculation, batch preparation, cleavage/workup planning, and evidence-assisted laboratory workflows**

Project Manager · Exact bottle setup · Editable Plan · Materials · Checklist · Batch Manager · Loading · Cleavage · Workup · Experimental History

[![Release](https://img.shields.io/badge/release-v7.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#quick-start)

**[한국어 README](README_KO.md) · [English User Manual](docs/USER_MANUAL_EN.md) · [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md)**

Repository: **SanghunWoo-23/SPPS-PLANNER**

</div>

> **Current release: v7.0.0 Final R2.**  
> The GitHub release package may receive packaging-only revisions without changing the V7 chemistry engine or planner behavior.

---

## Overview

SPPS Planner is a desktop workbench for planning and reviewing **solid-phase peptide synthesis (SPPS)** workflows.

The V7 workflow is centered on **Project Manager**:

```text
Add / Edit peptide
      ↓
Sequence + Scale + Resin + Loading + Exact bottles
      ↓
Generate
      ↓
Plan
 ├─ Materials
 ├─ Checklist
 ├─ Total Materials
 ├─ Cleavage Cocktail
 └─ Workup
      ↓
Batch Manager / Experimental records / Recommendations
```

V7 focuses on making the synthesis setup easier to use while keeping the validated chemistry behavior stable.

---

## Main features

### Project Manager Add / Edit

Each peptide can store:

- Project and peptide name
- Sequence
- Scale and copies
- Resin and loading
- LOT number
- Coupling reagent / activator
- Additive / catalyst
- Base
- Solvent

Exact bottle names can be selected from the local reagent library or entered manually.

### My recipes

Frequently used coupling combinations can be saved locally.

Supported actions include:

- Save
- Load
- Rename
- Delete
- Favorite
- Backup / Import
- Recent recipe and recent bottle shortcuts

### Unified calculation

`Generate` refreshes the connected calculation views from the current peptide setup:

- Plan
- Materials
- Checklist
- Total Materials
- Cleavage Cocktail
- Workup

Manual Plan edits can be retained and recalculated through the existing Apply Change workflow.

### 2-CTC direct loading

When **2-CTC** is selected, Direct resin loading is enabled automatically.

Default loading conditions:

```text
Resin        1 eq
Amino acid   2 eq
DIEA         4 eq
```

The option can be disabled manually when an already-loaded 2-CTC resin is used.

Other resin types do not automatically enable Direct resin loading.

### Cleavage and workup

Cleavage calculation is integrated with the Project Manager result views.

Post-cleavage workup options include:

- Ethyl Ether
- n-Hexane
- Ether / n-Hexane 1:1
- Custom workup volume

Workup solvents are kept separate from the cleavage cocktail and are included in Materials / Total Materials.

### Batch Manager

Batch Manager reads real peptide sequences from Project Manager and calculates solution-preparation quantities from its own visible preparation defaults.

Project-specific coupling bottle choices do not silently rewrite Batch Manager preparation defaults.

---

## Quick start

### Requirements

- Windows 10 / 11
- 64-bit Python 3.11 or 3.12
- Tk-capable Python installation

### Run from source

From the repository root:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

### Build the Windows executable / installer

The release package includes the files required for the Windows build workflow.

The easiest entry point is:

```bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

Individual build scripts are also available:

```bat
BUILD_EXE_ONLY.bat
BUILD_INSTALLER.bat
```

`requirements-dev.txt` is required for the build-tool installation workflow and is included in the buildable release package.

---

## Public data policy

The public GitHub package does **not** bundle private laboratory history, private experimental databases, confidential sample/sequence information, private source photographs, or private model artifacts.

Runtime data are stored outside the repository in the application's user-data area.

Only data that the user is authorized to use should be imported or published.

---

## Scientific scope

SPPS Planner is intended for research planning, calculation, traceability, and laboratory decision support.

It does not replace:

- approved SOPs
- reagent SDS and institutional safety rules
- trained operator review
- validated analytical methods
- experimental confirmation
- formal GMP/GLP documentation where required

Recommendation outputs should always be interpreted together with their displayed evidence/provenance.

---

## License and citation

See [LICENSE](LICENSE) for the complete license terms.

If SPPS Planner contributes to academic work, cite the software and the corresponding tagged release.

Suggested citation:

> Woo, S. **SPPS Planner: Solid-Phase Peptide Synthesis Planning and Evidence-Driven Decision Support.** Version 7.0.0. GitHub repository, 2026.

See [CITATION.cff](CITATION.cff) for citation metadata.
