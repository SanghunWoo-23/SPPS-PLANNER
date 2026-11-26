<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner" width="150">

# SPPS Planner V9.0.0

**Windows-first solid-phase peptide synthesis planning, chemistry review, and evidence-aware laboratory decision support**

Project Manager · Auto Plan · Linear / Branched / Cyclic · Editable Plan · Materials · Checklist · Batch Manager · MW / MS Review · AI & ML · Lab History

[![Version](https://img.shields.io/badge/release-V9.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#quick-start)

**[한국어 README](README_KO.md) · [English manual](docs/USER_MANUAL_EN.md) · [한국어 매뉴얼](docs/USER_MANUAL_KO.md)**

**Repository:** [SanghunWoo-23/SPPS-PLANNER](https://github.com/SanghunWoo-23/SPPS-PLANNER)

</div>

> **V9.0.0 PUBLIC SOURCE DISTRIBUTION.** The source archive contains Python source code and Windows build inputs, **not** a prebuilt Windows EXE or Installer. Source regression testing is not equivalent to native Windows installation, laboratory SOP validation, or experimentally validated ML predictions. The release's GitHub-hosted CI checks remain to be confirmed after uploading the updated PUBLIC source.

## Overview

SPPS Planner is a research-oriented desktop application for preparing **reviewable and editable solid-phase peptide synthesis (SPPS) plans**. It links peptide configuration, chemistry and topology reviews, reagent/material calculations, experiment history, and evidence-aware ML workflows. The operator remains responsible for reviewing experimental conditions and approving laboratory actions.

```text
Project Manager → Add / Edit Peptide
       ↓
Sequence + Scale + Copies + Resin + Loading + Exact bottles
       ↓
Linear / Branched / Cyclic setup
       ↓
Generate  OR  Auto Plan (Optional) → Review → Generate Full Plan
       ↓
Plan ─── Materials ─── Checklist ─── Total Materials
  └──── Cleavage Cocktail ─── Workup
       ↓
MW / MS review · Sequence Risk Map · Recommendations & Lab History
       ↓
Experimental runs → Verified QC records → Reviewed AI / ML import
       ↓
Batch Manager · Export · Operator review · Experimental validation
```

## Highlights — V9.0.0

### Linear, branched and cyclic workflows

- **Linear SPPS:** sequence-aware synthesis planning, resin/loading calculations, editable coupling setup, deprotection, cleavage and workup.
- **Branched peptides:** operator-defined Lys branch information, branch-arm coupling methods and N-terminal Boc protection workflow. Branching does **not** automatically require selective cleavage.
- **Head-to-tail cyclization:** distinct selective-cleavage → cyclization-review → global-deprotection workflow, with product/protection-state checks.
- **Disulfide cyclization:** separately reviewed Cys–Cys linkage and oxidation route; the head-to-tail amide-coupling system is **not** applied to disulfide formation.
- **Topology and chemistry review:** supported protecting groups and noncanonical monomers, optional RDKit atom-mapped structure checks, theoretical stage-wise mass and MS-ion candidates. Unsupported or ambiguous structures remain unverified rather than being guessed.

### Operator-selectable coupling and cleavage methods

- Reviewable coupling systems include **HBTU/NMM, HBTU/DIEA, DIC/HOBt, EDC·HCl/HOBt, EDC·HCl/NHS, HATU/DIEA, DIC/Oxyma and PyBOP/NMM**, where applicable.
- **1.5% TFA/DCM** is available as a commonly used selective-cleavage draft for compatible head-to-tail workflows; alternative concentrations, solvents and user-defined conditions require review.
- Reaction equivalents, solvent volumes and time are controlled by the operator. Selecting a named reagent system **does not validate the chemistry or authorize a laboratory SOP**.
- Proposed/review-only steps are distinguished from confirmed material consumption, and unreviewed reagents are not silently counted as approved laboratory quantities.

### Project Manager, calculations and export

- Project/peptide identity, LOT, sequence, scale, copies, resin and loading, exact reagent-bottle choices, and local **My Recipes**.
- Connected **Generate / Apply Change** and optional Auto Plan workflows, with editable Plan and synchronized Materials, Checklist, Total Materials, Cleavage and Workup views.
- Batch Manager retains independent preparation defaults; peptide-specific settings do not silently overwrite them.
- Excel, CSV and JSON output paths support reviewable calculation and method evidence. Material amounts reflect valid entered settings; missing or stale review data remain flagged.

### Evidence-aware AI, ML and laboratory history

- Guided Excel/CSV import supports multiple workbooks/sheets, column recognition, quality auditing, duplicate detection and explicit user confirmation.
- Distinguishes **measured observations**, **planned conditions**, **unapproved drafts** and **model predictions**.
- Local Loading/yield/purity model workflows include grouped validation where supported, readiness checks and model review/approval mechanisms. Insufficient or unsuitable experimental data must not be represented as a validated predictor.
- **Recommendations & Lab History** connects experiment Run context, results and issue records. Final cleavage measurements and QC records use coordinated storage to reduce partial-result persistence.
- **Data Health** reports missing/duplicate/review-needed observations. **Export Verified QC CSV** produces a reviewable dataset; an exported file is **not** automatically treated as a complete, confirmed experiment protocol or used for unattended training.
- Local literature evidence and explicitly consented external excerpt review are research aids, not independently verified reaction instructions.

### Data integrity and release hygiene

- JSON project validation, last-good backups and guarded persistence; laboratory records and planned conditions are tracked separately.
- Public and Private use separate runtime profiles. **PUBLIC must never contain Private experimental seed data, lab notebooks, confidential sequences, user sessions, trained model artifacts or company datasets.** See [Public Data Policy](PUBLIC_DATA_POLICY.md).
- Only the existing **`INSTALL_BUILD_TOOLS_AND_BUILD.bat`** is the official Windows build entry point. No redundant build launcher is required.

## Quick start

**Target:** Windows 10/11, 64-bit Python **3.11 or 3.12**, and Tk support. Linux/Xvfb is used for development and source testing.

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py --self-test
python main_launcher.py
```

RDKit is already included in the default `requirements.txt`. The legacy optional RDKit requirements file is retained for compatibility and is **not** a second mandatory installation step.

### Build a Windows EXE and Installer

Extract the **complete** PUBLIC source archive on Windows and run:

```bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

The BAT checks the required tools, builds the executable, performs packaged checks and attempts to create an Inno Setup installer. It may need internet access and tool-installation privileges. Expected paths include:

- `dist\SPPS_Planner\SPPS_Planner.exe` — keep the complete dist directory for portable use.
- `installer\output\SPPS_Planner_PUBLIC_Setup_V9.0.0.exe` — installer generated by the Windows build, **not** included in this source archive.

**Building an installer is different from installing and testing it.** Native Windows installation/upgrade/uninstall and long-running GUI operation have not been accepted as fully verified for this source release. See [Windows build guide](docs/WINDOWS_BUILD_KO.md).

### Test from source

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
python tools\verify_windows_release.py
python tools\github_release_preflight_v9.py --strict
```

## Verification and limitations

| Check | Status |
|---|---|
| Latest PUBLIC Linux 3.13 / Xvfb source regression | **880 passed, 3 skipped, 0 failed** |
| PUBLIC source preflight and source checks | **Passed** in the local release environment |
| ZIP integrity and SHA-256 | **Verified for the existing archive** listed in the GitHub Release notes |
| GitHub Actions: Linux 3.11.9 / Windows 3.11.9 / Windows 3.12.10 | **Pending successful run after updated PUBLIC source is uploaded** |
| Windows-native EXE/Installer install, upgrade and uninstall | **Not verified** |
| Independent wet-lab reaction success or externally validated ML accuracy | **Not established** |

Theoretical MW/MS results and proposed synthesis conditions are **not proof** of chemical feasibility, reaction completion, product identity, purity, yield, or biological activity. SPPS Planner does not replace approved SOPs, safety rules, SDS, trained operator review or independently validated analytical methods.

## Source package and documentation

The intended GitHub Release asset is the **PUBLIC-only source ZIP**, with a SHA-256 checksum published alongside it. Repacking the ZIP changes its hash and requires generating a new checksum.

For current and versioned details, see [Documentation index](docs/INDEX.md), [V9 scope](README_V9_DEVELOPMENT.md), [Architecture](docs/ARCHITECTURE.md), [Public data policy](PUBLIC_DATA_POLICY.md), and [GitHub publication guide](docs/GITHUB_PUBLICATION_V9_KO.md).

## License and citation

This project uses the **SPPS Planner Public Academic Citation License**: a custom, non-commercial, source-available license with academic citation requirements. It is **not an OSI-approved open-source license**. Review [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff) before redistributing or using the software.

Suggested citation: **Woo, S.** *SPPS Planner: Solid-Phase Peptide Synthesis Planning and Evidence-Driven Decision Support.* Version 9.0.0 (2026). [GitHub repository](https://github.com/SanghunWoo-23/SPPS-PLANNER).

---

**SPPS Planner V9.0.0 — From peptide sequence to traceable synthesis planning, experimental evidence, and reviewable decisions.**
