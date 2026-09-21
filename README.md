<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner" width="150">

# SPPS Planner v6.0.0

**Windows-first desktop software for solid-phase peptide synthesis planning, calculation, traceability, and evidence-driven decision support**

Sequence parsing · Editable synthesis plans · Materials · Checklists · Batch planning · Loading Advisor · Cleavage Advisor · Experimental history

[![Release](https://img.shields.io/badge/release-v6.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#quick-start)
[![License](https://img.shields.io/badge/license-Academic%20%2F%20Non--commercial-6B7280?style=for-the-badge)](LICENSE)

**[한국어 README](README_KO.md) · [User Manual](docs/USER_MANUAL_EN.md) · [한국어 매뉴얼](docs/USER_MANUAL_KO.md) · [Architecture](docs/ARCHITECTURE.md) · [Public Data Policy](PUBLIC_DATA_POLICY.md)**

Repository: **SanghunWoo-23/SPPS-PLANNER**

</div>

> **Current release: v6.0.0.** This public package is built from the validated V6 R19 source line. It contains the functional planner and decision-support code but **does not bundle private laboratory history, private seed data, source photographs, or local experimental databases**.

---

## Overview

SPPS Planner is a desktop workbench for planning and reviewing **solid-phase peptide synthesis (SPPS)** workflows. It converts a peptide design and synthesis settings into an editable synthesis Plan, then keeps that Plan connected to materials, checklists, batch totals, cleavage settings, experimental records, and evidence-based recommendations.

The central workflow is:

```text
Peptide / project definition
        ↓
Sequence + modifiers + resin + scale + chemistry
        ↓
Generate
        ↓
Editable Plan
 ├─ Materials
 ├─ Checklist
 ├─ Total Materials
 ├─ Cleavage
 └─ Export / Batch outputs
        ↓
Experiment
        ↓
Add Result / Add Issue
        ↓
Run-linked local evidence
        ↓
Loading / Cleavage recommendation support
```

SPPS Planner is intentionally **not** a black-box synthesis oracle. Operator-edited plans remain visible state, recommendation provenance is shown, and chemistry defaults are kept separate from measured experimental evidence.

---

## Highlights in v6.0.0

### Editable planning workflow

- Generate a synthesis Plan from sequence, resin, scale, coupling, loading, and terminal settings.
- Edit the visible Plan directly.
- Use **Apply Change** to recalculate connected outputs from the edited Plan without silently rebuilding the original Plan.
- Track multiple peptide work items and batch material requirements.

### Sequence and building-block handling

- Natural L-amino acids.
- D-form amino acids.
- Data-supported special / non-natural loading identities such as `Cit`, `Hyp`, and `Dab`.
- Linkers, labels, tags, N-terminal modifiers, and terminal chemistry.
- Protected building-block identity remains chemically meaningful rather than being silently collapsed.

### Loading Advisor

Loading recommendations are evidence-first and intentionally conservative.

- Exact recommendation evidence is restricted to **same resin + same normalized loaded-AA identity**.
- D-form and L-form evidence are kept separate.
- Special/non-natural identity recognition does **not** create experimental support by itself.
- Repeated observed conditions can support `OBSERVED REPEATED CONDITION` recommendations.
- Target inversion uses bounded interpolation only **inside observed evidence ranges**.
- Out-of-range extrapolation is not presented as experimental evidence.
- `CHEMISTRY DEFAULT` remains explicitly labeled as a fallback rather than a measured prediction.
- Recommendation details expose record counts, observed ranges, repeatability, dates, capping notes, source locators, and nearby real conditions when available.

Examples of supported identity normalization include:

```text
Cit          -> Fmoc-Cit-OH
Hyp          -> Fmoc-Hyp(tBu)-OH when that exact observed identity exists
Dab          -> Fmoc-Dab(Boc)-OH
D-Leu / dL   -> Fmoc-D-Leu-OH
D-Phe / dF   -> Fmoc-D-Phe-OH
D-His(Trt)   -> Fmoc-D-His(Trt)-OH
```

Gly is treated as achiral; the planner does not create a fictitious D-Gly loading identity.

### Cleavage Advisor

- Keeps cleavage cocktail identity separate from equivalent amount.
- Preserves the established Cys hard rule: **TFA equivalent = 100 eq × Cys count** when automatic Cys handling applies.
- Does not double-add the peptide-length baseline when the Cys hard rule is active.
- Keeps optional post-cleavage NH4I reduction separate from the normal cleavage cocktail.
- Does not automatically insert NH4I merely because Met is present.

### Experimental records and traceability

- Add measured Loading, Cleavage, Outcome, Issue, and related records.
- Link records to the active Run and Planner-condition snapshot where available.
- Preserve raw source text alongside normalized lookup keys.
- Keep ambiguous or provisional data reviewable instead of silently upgrading it to strong evidence.
- Local data remain local unless the user deliberately exports or publishes them.

### Explicit model workflow

- Loading-model rebuild is explicit rather than automatic.
- Candidate models can be validated, promoted, and rolled back.
- Adding an experimental result does **not** silently retrain a model.

---

## Quick start

### Requirements

Recommended source-run environment:

- Windows 10 or Windows 11
- 64-bit Python 3.11 or 3.12
- Tk-capable desktop Python environment

### Run from source

From the repository root:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

### Development / verification

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

The release also provides dedicated integrity and Windows-release checks:

```bat
python tools\verify_v6_integrity.py
python tools\verify_windows_release.py
```

---

## Core workflow

### 1. Define the peptide

Configure the sequence and, where applicable:

- N-terminal modifier;
- C-terminal output;
- linker / label / tag;
- resin and loading;
- scale;
- coupling system;
- special or D-form building blocks;
- repeat / doubling behavior.

### 2. Generate the Plan

`Generate` creates a new Plan from the current setup.

### 3. Edit and recalculate

The Plan is editable. `Apply Change` recalculates connected outputs from the **current visible Plan**, preserving operator edits.

### 4. Review materials and execution views

Use the connected views for:

- Materials;
- Checklist;
- Total Materials;
- Cleavage;
- Batch calculations;
- Export.

### 5. Record the experiment

Use **Add Result** and **Add Issue** to connect laboratory outcomes back to the active run and planning condition.

### 6. Review evidence

Use **Recommendations & Lab History** for Loading/Cleavage guidance, evidence detail, and data-health review.

---

## Generate vs Apply Change

This distinction is deliberate:

| Action | Meaning |
| --- | --- |
| **Generate** | Build a new Plan from the current setup inputs |
| **Apply Change** | Keep the edited visible Plan and recalculate downstream outputs |

This prevents manual Plan corrections from disappearing when the user only wants refreshed calculations.

---

## Batch Manager / Project Manager synchronization

Batch Manager is a **sequence-driven synthesizer stock/solution preparation calculator**. It reads peptide sequences from Project Manager, but R19 deliberately does **not** aggregate Project Manager DIC/HOBt/HBTU choices, project-specific reagent equivalents, resin/loading settings, or other synthesis-condition history. Preparation quantities are recalculated from the visible **Solution prep defaults** only.

- Only Project Manager records with a real peptide sequence are used.
- `Copies` represents the number of synthesizer columns; preparation scale comes from Batch Manager `Scale mmol`.
- AA stock uses `Scale mmol × AA eq ÷ AA concentration`.
- HBTU/NMP stock uses `Scale mmol × HBTU eq ÷ HBTU concentration`.
- `Round-up mL` and `Extra reserve mL` convert calculated volume into practical preparation volume.
- A Project saved with DIC/HOBt does not create DIC/HOBt rows in Batch Manager.
- Empty/default placeholders and bundled sample/demo sequences are ignored.
- **Refresh totals** simply recalculates the current sequences with the current prep defaults.
- Autosave and existing Project history remain preserved.

This change is isolated to Batch Manager workflow logic; the locked chemistry engine is unchanged.

---

## Loading recommendation policy

The Loading Advisor follows a strict evidence hierarchy.

1. Use exact same-resin + same-loaded-AA history where available.
2. Exclude records marked as outliers from evidence-driven inversion.
3. Prefer a repeated real condition when the requested target lies within that condition's measured range.
4. Use bounded interpolation only within observed evidence coverage.
5. Keep broader similarity as diagnostic context rather than direct support.
6. Fall back to a clearly labeled chemistry default only where defined.
7. Return insufficient/out-of-range evidence rather than inventing an extrapolated experimental prediction.

The UI distinguishes:

- **Exact experimental match**
- **Bounded interpolation**
- **Default fallback**
- **Insufficient / outside observed range**

For D-form and special/non-natural building blocks, identity recognition and evidence support are deliberately separate. A name can be recognized while its exact-history count remains 0 or 1.

---

## Public data and privacy model

The GitHub package is a **sanitized public build**.

It intentionally does not bundle:

- private/internal measured loading history;
- private cleavage history;
- confidential product-to-sequence mappings;
- private source-image manifests or laboratory photographs;
- local SQLite databases;
- privately trained model artifacts;
- user-generated exports or logs.

The public build starts with a public-safe experimental seed area and remains fully usable for planning. Users can build their own local evidence base from data they are authorized to use.

On Windows, public-build runtime data are stored outside the repository under the application's local user-data area, based on:

```text
%LOCALAPPDATA%\SPPS_Planner_PUBLIC\
```

See [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md) before publishing any database, model, export, log, or imported laboratory file.

---

## Project structure

```text
SPPS-PLANNER/
├─ main_launcher.py
├─ suite_gui/                     # release GUI and decision-support integration
├─ apps/spps_planner_app/         # planner/data implementation
├─ tests/                         # regression and release-contract tests
├─ tools/                         # audit and verification utilities
├─ docs/                          # manuals, architecture, parser/data notes
├─ assets/                        # application icon/assets
├─ installer/                     # Windows installer definition
├─ requirements.txt
├─ requirements-dev.txt
├─ SPPS_Planner.spec
├─ BUILD_EXE_ONLY.bat
├─ BUILD_INSTALLER.bat
├─ LICENSE
└─ CITATION.cff
```

For implementation ownership and release boundaries, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Windows build

The repository includes PyInstaller/Inno Setup release support.

Common entry points:

```bat
BUILD_EXE_ONLY.bat
BUILD_INSTALLER.bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

Before distributing a binary build, run the release verification tools and review [docs/WINDOWS_BUILD_KO.md](docs/WINDOWS_BUILD_KO.md).

---

## Release validation

The v6.0.0 public source package was validated from a fresh-unzipped release archive.

- Full public headless pytest: **370 passed / 28 skipped**
- Full public Real-Tk/Xvfb pytest: **395 passed / 3 skipped**
- R19 sequence-driven Batch prep Real-Tk regression: **PASS**
- `tools/verify_v6_integrity.py`: **PASS**
- `tools/verify_windows_release.py`: **PASS**
- Public bundled experimental seed: documentation-only (`README.md`)
- Public SQLite/DB files: **0**
- ZIP integrity check: **PASS** (`testzip = None`)
- Locked chemistry-engine golden behavior remained unchanged through the R19 Batch solution-prep correction

The internal release validation also confirmed shared source parity between the corresponding public/private builds while preserving the data boundary.

---

## Scientific scope and limitations

SPPS Planner is intended for **planning, screening, traceability, and research decision support**.

It does not replace:

- an approved laboratory SOP;
- reagent SDS and institutional safety requirements;
- trained operator review;
- validated analytical methods;
- experimental confirmation of synthesis outcome;
- GMP/GLP documentation where formally required.

Recommendation output should be interpreted according to its displayed provenance. A chemistry default, empirical rule, interpolation, model estimate, and measured repeated condition are not equivalent forms of evidence.

---

## Documentation

| Document | Purpose |
| --- | --- |
| [README_KO.md](README_KO.md) | Korean project overview |
| [docs/USER_MANUAL_EN.md](docs/USER_MANUAL_EN.md) | English user manual |
| [docs/USER_MANUAL_KO.md](docs/USER_MANUAL_KO.md) | Korean user manual |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Architecture / ownership boundaries |
| [docs/SPPS_PARSER_CONTRACT.md](docs/SPPS_PARSER_CONTRACT.md) | Sequence-parser contract |
| [docs/SPPS_REAGENT_DATABASE_SCHEMA.md](docs/SPPS_REAGENT_DATABASE_SCHEMA.md) | Reagent data schema |
| [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md) | Public/private data boundary |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidance |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [RELEASE_NOTES_V6.0.0.md](RELEASE_NOTES_V6.0.0.md) | v6.0.0 release notes |

The V5 decision-support documents and Historical development checkpoint notes were removed from the release root to keep the distribution compact; the public changelog retains the release history.

---

## Citation

If SPPS Planner contributes to academic work, please cite the software and the corresponding tagged release/DOI when available.

Suggested citation:

> Woo, S. **SPPS Planner: Solid-Phase Peptide Synthesis Planning and Evidence-Driven Decision Support.** Version 6.0.0. GitHub repository, 2026. https://github.com/SanghunWoo-23/SPPS-PLANNER

GitHub-compatible citation metadata are provided in [CITATION.cff](CITATION.cff).

---

## License

SPPS Planner is distributed under the **SPPS Planner Public Academic Citation License**.

The license permits academic, educational, research, portfolio-review, and non-commercial use subject to its terms and citation requirement. It is a custom source-available license and is **not an OSI-approved open-source license**.

See [LICENSE](LICENSE) for the complete terms.

---

## Contributing

Contributions are welcome when they preserve the release contracts around chemistry behavior, editable Plan state, evidence provenance, privacy, and Windows compatibility.

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a change.

---

## Release notes

See [RELEASE_NOTES_V6.0.0.md](RELEASE_NOTES_V6.0.0.md) for the public v6.0.0 release summary and [CHANGELOG.md](CHANGELOG.md) for the longer development history.
