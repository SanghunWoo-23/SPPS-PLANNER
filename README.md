<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner icon" width="160">

# SPPS Planner V5.0.0

**Windows-first desktop software for planning, reviewing, recording, and improving solid-phase peptide synthesis (SPPS) workflows**

Sequence parsing · editable synthesis plans · material calculations · checklists · batch planning · cleavage guidance · experimental history · evidence-driven recommendations

[![Release](https://img.shields.io/badge/release-V5.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#quick-start)
[![License](https://img.shields.io/badge/license-Custom%20Academic%20Citation-6B7280?style=for-the-badge)](LICENSE)

**[한국어 README](README_KO.md) · [English User Manual](docs/USER_MANUAL_EN.md) · [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md) · [Architecture](docs/ARCHITECTURE.md) · [Public Data Policy](PUBLIC_DATA_POLICY.md)**

Repository: **SanghunWoo-23/SPPS-PLANNER**

</div>

---

## Table of contents

- [What SPPS Planner is](#what-spps-planner-is)
- [Release status](#release-status)
- [Design philosophy](#design-philosophy)
- [What V5.0.0 adds](#what-v500-adds)
- [Feature overview](#feature-overview)
- [Core workflow](#core-workflow)
- [Quick start](#quick-start)
- [Sequence input and parser behavior](#sequence-input-and-parser-behavior)
- [Planning workflow](#planning-workflow)
- [Materials, checklist, and batch calculations](#materials-checklist-and-batch-calculations)
- [Loading Advisor](#loading-advisor)
- [Cleavage Advisor](#cleavage-advisor)
- [Post-cleavage NH4I rescue](#post-cleavage-nh4i-rescue)
- [Recommendations and Lab History](#recommendations-and-lab-history)
- [Natural-language Issue Log](#natural-language-issue-log)
- [Run traceability](#run-traceability)
- [Evidence and model policy](#evidence-and-model-policy)
- [Public data and privacy model](#public-data-and-privacy-model)
- [Runtime data locations](#runtime-data-locations)
- [Repository structure](#repository-structure)
- [Windows build](#windows-build)
- [Verification and regression testing](#verification-and-regression-testing)
- [Performance design](#performance-design)
- [Scientific scope and limitations](#scientific-scope-and-limitations)
- [Documentation map](#documentation-map)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## What SPPS Planner is

SPPS Planner is a desktop workbench for **solid-phase peptide synthesis planning and traceability**. It converts a peptide design plus synthesis settings into an editable Plan and keeps the Plan connected to calculated materials, totals, checklists, cleavage settings, batch summaries, execution records, and evidence from previous laboratory work.

The application is intentionally built around the way an operator actually works:

```text
Peptide / project definition
          ↓
Sequence + modifiers + resin + scale + loading + chemistry
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
Experiment is performed
          ↓
Measured Result or free-text Issue is recorded
          ↓
Planner conditions + active Run are linked automatically
          ↓
Verified local evidence accumulates
          ↓
Future recommendations become better grounded
```

SPPS Planner is not designed as a black-box synthesis oracle. The visible Plan remains editable, recommendation sources are kept distinguishable, and model output does not silently replace operator-approved chemistry.

---

## Release status

**V5.0.0 is the current public GitHub release.**

The public source package is intentionally separated from internal/private experimental history. The same planner and decision-support code can operate with an empty public experimental database and learn only from data the user later records or imports locally.

The V5 release keeps the validated planner behavior accumulated through earlier releases and adds the V5 evidence, traceability, usability, and performance work without replacing the established Generate / Apply Change calculation route.

For release-level changes, see [CHANGELOG.md](CHANGELOG.md).

---

## Design philosophy

SPPS Planner V5.0.0 follows several non-negotiable principles.

### 1. The visible Plan is real state

`Generate` creates a Plan from the current setup. After that, the operator can edit the visible Plan. `Apply Change` recalculates connected outputs from the edited Plan instead of silently recreating the original sequence-based plan.

### 2. Recorded history is not the same as a planned condition

A condition shown in the Planner is a plan. It becomes experimental evidence only after an actual Result, Issue, Outcome, or other reviewed record is attached to the corresponding run.

### 3. Exact chemistry identity matters

Protected amino-acid and reagent identity is not intentionally collapsed when the chemistry depends on the actual bottle-level form. D-form, non-natural residues, branch handles, labels, linkers, and terminal modifiers are preserved as meaningful units.

### 4. Evidence must remain attributable

Observed historical evidence, operator rules, empirical estimates, and model predictions are intentionally distinguishable. The software should not present an estimate as if it were a measured experiment.

### 5. No hidden online retraining

Adding a result does not silently retrain a model. Loading-model rebuild is explicit, validated, versioned, and rollback-capable.

### 6. Public data must remain public-safe

The GitHub distribution contains no bundled internal experimental database. Users build their own local evidence base from data they are authorized to use.

### 7. Scientific decisions remain operator-reviewed

Recommendations assist planning and prioritization. They do not replace an approved SOP, SDS, institutional safety requirements, qualified analytical methods, or an experienced operator's review.

---

## What V5.0.0 adds

V5.0.0 is primarily an **evidence and workflow refinement release** rather than a rewrite.

Major V5 additions include:

- target-loading recommendations using **bounded inverse interpolation** from same-resin / same-loaded-amino-acid evidence;
- a verified-data Loading model registry with explicit rebuild, validation, promotion, and rollback;
- evidence-aware Cleavage recommendations with a public-safe empirical fallback;
- an operator-defined Cys cleavage-equivalent hard rule;
- optional post-cleavage **NH4I Reduction** workflow separated from the cleavage cocktail;
- a compact **Recommendations & Lab History** window;
- simplified **Add Result** and **Add Issue** workflows;
- bilingual Korean/English natural-language synthesis issue parsing;
- Run ID and Planner-condition snapshot linkage for experimental records;
- History, Risk & Evidence, and Data Health grouped under Advanced rather than cluttering the daily workflow;
- improved Batch material grouping and classification;
- fast-path experimental-database initialization and delayed heavy data refresh so the recommendation window can appear promptly;
- public/private source parity with a sanitized public experimental seed area.

---

## Feature overview

| Area | What it does |
| --- | --- |
| Sequence processing | Parses natural residues, terminal groups, D/non-natural residues, modifiers, linkers, labels, tags, and branch-capable units |
| Resin / loading | Supports established resin families, loading parameters, resin-dependent volume behavior, and editable loading settings |
| Plan generation | Builds the editable synthesis sequence and reagent/solvent workflow |
| Apply Change | Recalculates linked outputs from the current visible Plan |
| Materials | Calculates resin, amino-acid/chemical units, coupling reagents, bases, additives, solvents, and workflow materials |
| Checklist | Produces operator-oriented synthesis steps and compact/full checklist views |
| Cleavage | Provides editable cleavage settings, empirical/evidence advice, component calculations, and workup separation |
| Project Manager | Maintains multiple peptide work items and the selected/active work context |
| Batch Manager | Calculates multiple peptide items and combined material requirements |
| Custom DB | Supports user-defined amino acids, chemicals, reagents, additives, bases, solvents, resins, and other materials |
| Data / HPLC | Maintains run-linked data and analytical file references |
| Experimental Data | Stores Loading, Cleavage, Sequence, Outcome, Issue, and usage/history records |
| Recommendations | Uses exact history, reviewed evidence, bounded interpolation, and explicit models without pretending they are equivalent |
| Risk & Evidence | Explains sequence/stage risks and surfaces relevant historical evidence |
| Model Registry | Rebuilds Loading models explicitly from eligible Verified measured records and keeps model versions |
| Export | Exports active planning/data state through the existing release workflow |
| Windows release | Includes PyInstaller and Inno Setup build/verification tooling |

---

## Core workflow

### Typical single-peptide workflow

1. Open or create a project/work item.
2. Enter the peptide sequence.
3. Select the resin and synthesis scale.
4. Review loading and chemistry defaults.
5. Select **Generate**.
6. Review the generated Plan.
7. Edit Plan rows when the real bench workflow differs.
8. Select **Apply Change** after Plan edits.
9. Review Materials, Checklist, Total Materials, and Cleavage.
10. Perform the synthesis under your approved laboratory workflow.
11. Record measured outcomes with **Add Result**.
12. Record problems or interventions with **Add Issue**.
13. Review accumulated evidence in Recommendations / Advanced when useful.

### Why Generate and Apply Change are separate

This separation is important.

- **Generate** means: build a new Plan from the current setup.
- **Apply Change** means: preserve the currently edited Plan and recalculate linked outputs from it.

This prevents a manual correction in the visible Plan from being lost simply because the user wants refreshed Materials or Checklist values.

---

## Quick start

### Requirements

Recommended source-run environment:

- Windows 10 or Windows 11
- 64-bit Python 3.11 or 3.12
- a normal desktop environment with Tk support

Core Python packages are listed in [requirements.txt](requirements.txt).

### Run from source

From the repository root:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

### Development / verification environment

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

### Main keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+O` | Load Project |
| `Ctrl+N` | Add Work Item |
| `Ctrl+D` | Duplicate Work Item |
| `Ctrl+G` | Generate |
| `Ctrl+Enter` | Apply Change |
| `Ctrl+E` | Export current work |
| `Ctrl+-` | Compact display density |
| `Ctrl+0` | Standard display density |
| `Ctrl+=` | Comfortable display density |
| `F5` in Work Item window | Refresh |
| `Esc` in Work Item window | Save and close |

---

## Sequence input and parser behavior

The parser accepts plain peptide sequences and explicit terminal/modifier notation while avoiding silent reinterpretation of the peptide core.

### Basic examples

```text
GHTYKL
GHTYKL-NH2
-GHTYKL-NH2
Ac-GHTYKL-NH2
AcGHTYKL-NH2
FITC-GHTYKL-NH2
Biotin-GHTYKL-NH2
```

For example:

```text
Ac-GHTYKL-NH2
```

is represented conceptually as:

```text
N-terminus: Ac
Core:       G H T Y K L
C-terminus: NH2
```

### Parser safety rules

- delimiter-free natural FASTA-like chunks are split into amino-acid residues;
- bracketed or catalog-defined chemical/linker/label/tag units remain meaningful tokens;
- compact `Ac` notation is recognized only when unambiguous;
- a natural sequence beginning with `AC...` is not automatically converted into an acetylated sequence;
- non-acetyl N-terminal modifiers should be written explicitly with a dash;
- protecting groups are handled by the planner/catalog layer rather than invented by the sequence parser;
- natural matching is case-insensitive where appropriate, while D-form and modified-token meaning is preserved.

See [docs/SPPS_PARSER_CONTRACT.md](docs/SPPS_PARSER_CONTRACT.md) for the compact parser contract.

---

## Planning workflow

SPPS Planner combines sequence definition with configurable synthesis settings.

### Planning inputs include, where applicable

- project / peptide / work item;
- sequence;
- copies;
- synthesis scale;
- resin / resin family;
- resin loading;
- loaded or C-terminal amino acid;
- amino-acid equivalents;
- base equivalents;
- loading time;
- coupling system;
- reagent / additive / base / solvent settings;
- terminal modification;
- branch settings;
- repeat / doubling decisions;
- cleavage equivalents, composition, and time.

### Editable Plan

The Plan is not merely a report. It is an editable workflow representation. The release keeps direct Plan editing and downstream recalculation as first-class behavior.

Typical step categories include:

- resin swelling;
- loading;
- Fmoc deprotection;
- pre-coupling wash;
- amino-acid or chemical coupling;
- post-coupling wash;
- repeat coupling / doubling where configured;
- N-terminal modification;
- final washes;
- cleavage / workup planning in the connected workflow.

### Process-rule examples

The bundled process-rule layer includes explicit repeated-step defaults such as:

- 20% piperidine / 80% DMF deprotection basis;
- repeated deprotection cycles;
- resin-family-dependent loading/swell behavior;
- coupling and post-coupling wash counts;
- final wash handling.

These are editable planning defaults, not a substitute for the user's SOP.

---

## Materials, checklist, and batch calculations

### Materials

Material calculations are connected to the active Plan and can include:

- resin;
- L-amino acids;
- D-amino acids;
- non-natural amino acids;
- branch handles;
- chemical modifiers;
- labels / tags / linkers;
- coupling reagents;
- catalysts / additives;
- bases;
- solvents;
- deprotection reagents;
- cleavage components;
- workup-related materials where appropriate.

Where molecular weight, density, or volume basis is known, the planner reports mass or volume using the appropriate material representation. Unknown/unresolved units are not supposed to be silently guessed.

### Batch material ordering

The V5 combined material presentation follows this operator-facing grouping:

1. L-AA
2. D-AA
3. Non-natural AA
4. Chemical

Each section is sorted internally. Chemical-type presentation includes relevant modifiers/caps, tags, labels, and terminal chemical units. `Fmoc-Cit-OH` is treated as a **Non-natural AA**, not as a generic chemical.

### Checklist

Checklist views are generated from the Plan and provide full and shorter operational views. They are intended to help execution and review, not to replace institutional batch records or GMP documentation where those are required.

### Batch Manager

Batch Manager can calculate multiple peptide items together while keeping each work item traceable. It provides selected-item views and combined totals rather than forcing the user to manually merge individual calculations.

---

## Loading Advisor

The V5 Loading feature is designed around a practical operator question:

> **What amino-acid equivalent should I use to target a desired resin loading?**

The operator-facing flow is conceptually:

```text
Target Loading (mmol/g)
        ↓
Recommended AA eq
        ↓
Expected Loading
        ↓
Expected Range
        ↓
Confidence / evidence
        ↓
Apply when eligible
```

### What counts as strong loading evidence

The highest-value records are actual measured loading outcomes linked to the condition that produced them.

Relevant features can include:

- resin;
- same loaded / C-terminal amino acid;
- amino-acid equivalents;
- base equivalents;
- loading time;
- measured loading rate (`mmol/g`).

### Evidence priority

The V5 logic is intentionally conservative:

1. Verified measured loading records;
2. same resin + same loaded/C-terminal amino-acid evidence;
3. bounded interpolation **inside** the observed range;
4. explicit trained model as supporting/cross-check evidence;
5. parsed historical fallback only when stronger verified evidence is insufficient;
6. `INSUFFICIENT EVIDENCE` rather than fabricated extrapolation.

### Bounded inverse recommendation

The target-loading inverse workflow is designed to avoid a common small-data failure mode: fitting a model and extrapolating beyond what was ever observed.

The advisor therefore does **not** treat different resin/amino-acid categories as interchangeable merely to increase sample count. It attempts to stay within category-relevant evidence and within observed ranges.

### Quick measured loading

The Loading workflow can save a measured loading value as a verified result while automatically attaching known Planner conditions and active run context.

### Explicit model registry

Loading-model rebuilding is separate from data entry.

Current model policy includes:

- Verified measured loading records only;
- at least 12 eligible records;
- at least 3 distinct measured loading values;
- categorical features for resin and normalized amino acid;
- numeric features for AA eq, base eq, and loading time;
- cross-validated MAE recording;
- versioned model files;
- candidate-versus-active comparison;
- automatic promotion only when the candidate is not materially worse than the active model under the implemented tolerance;
- explicit candidate promotion and rollback controls;
- no automatic application of model-only output.

After an active model exists, the UI can notify the user when approximately five new verified measured loading results have accumulated since the active model. The notification suggests rebuilding; it does not retrain automatically.

---

## Cleavage Advisor

Cleavage recommendations distinguish **observed history**, **operator rules**, and **empirical fallback**.

### Cys hard rule

When the parsed sequence contains Cys, the current operator rule is:

```text
TFA equivalent = 100 eq × number of Cys residues
```

Examples:

| Cys count | Cleavage equivalent |
| ---: | ---: |
| 1 | 100 eq |
| 2 | 200 eq |
| 3 | 300 eq |
| 4 | 400 eq |

Important implementation behavior:

- the rule is independent of peptide length;
- it replaces the normal length-based equivalent estimate rather than adding to it;
- a manual/operator override is not supposed to receive another hidden `+100 eq/Cys` increment;
- the Cys rule controls the equivalent amount; cocktail composition is handled separately;
- the public Cys-sensitive generic composition currently uses a `95 / 2.5 / 2.5` TFA / TIS / Water fallback unless a stronger eligible condition applies.

### Public-safe non-Cys empirical baseline

When no stronger eligible evidence exists and the sequence has no Cys hard-rule override, V5 contains a monotonic public-safe peptide-length baseline.

| Length | Baseline TFA eq |
| ---: | ---: |
| 1 | 8 |
| 2 | 10 |
| 3 | 15 |
| 4 | 18 |
| 5 | 20 |
| 6 | 30 |
| 8 | 35 |
| 10 | 45 |
| 12 | 50 |
| 14 | 60 |
| 15 | 80 |
| 18 | 88 |
| 21 | 95 |
| 22+ | 100 |

Intermediate lengths are interpolated monotonically. This curve is an **empirical software baseline**, not a universal chemistry law.

### Cleavage evidence principles

- exact/repeated historical evidence can outrank a generic fallback;
- public builds do not contain bundled private exact-sequence anchors;
- similar-sequence information can support empirical context without being relabeled as an exact historical observation;
- unitless material-usage values remain unresolved until reviewed;
- aggregate/multi-product usage records are reference-only for automatic scaling;
- workup solvents and cleavage cocktail components remain separate concepts.

### Workup separation

Ethyl ether and n-hexane are treated as workup / precipitation materials, **not** as cleavage-cocktail ingredients. The software intentionally keeps cleavage composition, current-scale amount, and precipitation/workup evidence separate.

---

## Post-cleavage NH4I rescue

V5 includes an optional post-cleavage rescue workflow for situations where oxidation or a relevant characteristic impurity has actually been observed or judged relevant.

The default is:

```text
Post-cleavage Rescue: None
```

Optional mode:

```text
Post-cleavage Rescue: NH4I Reduction
```

Current operator preset:

| Parameter | Default |
| --- | ---: |
| NH4I equivalent | 2 eq relative to peptide |
| Final NH4I concentration | 0.2 M |
| Reaction time | 1 h |
| Solvent context | TFA / Water |

The calculator derives NH4I mmol, mass, and approximate final solution volume from peptide scale.

A concentration above **0.2 M** is blocked/warned by the implemented operator protocol because precipitation can make the condition unusable.

NH4I is deliberately **not** inserted automatically into the normal cleavage cocktail and is not automatically enabled merely because a sequence contains Met. A recorded oxidation issue can make the rescue option relevant, but the user still decides whether to use it.

---

## Recommendations and Lab History

The V5 recommendation window is intentionally compact and split into daily-operation and advanced areas.

### Recommendations

Current recommendation tabs include:

- Loading;
- Cleavage;
- All Conditions.

The goal is to answer the immediate planning question first without making the operator navigate through database internals.

### Advanced

Advanced contains:

- History;
- Risk & Evidence;
- Data Health.

History includes record views for areas such as:

- Issues;
- Loading;
- Cleavage;
- Sequence STD;
- Cleavage Usage;
- Outcomes.

These views remain available for audit and review, but they are intentionally not the primary data-entry path.

### Add Result

`Add Result` is meant for actual measured outcomes. Planner-known context is attached automatically where available, reducing repeated manual entry.

Depending on result type, measured fields can include:

- measured loading;
- yield;
- purity;
- crude weight;
- outcome;
- notes.

### Add Issue

`Add Issue` is natural-language-first. The raw sentence is preserved even when structured parsing succeeds.

The system can attach:

- stage;
- issue type;
- position;
- residue;
- severity;
- action taken;
- resolution;
- parse confidence;
- parser status/version;
- detected language.

Ambiguous text can remain `needs_review` instead of contaminating ML/risk evidence.

---

## Natural-language Issue Log

The issue parser recognizes common Korean, English, and mixed-language operator descriptions.

Examples of issue families it can identify include:

- abnormal Kaiser / chloranil result;
- precipitation failure or partial precipitation;
- aggregation / resin clumping;
- oxidation;
- incomplete deprotection;
- incomplete coupling;
- poor swelling;
- filtration difficulty;
- reagent solubility problems;
- side products;
- low crude recovery;
- cleavage problems;
- equipment / process problems.

It can also recognize intervention language such as:

- repeat coupling;
- repeat deprotection;
- longer reaction;
- solvent or reagent change;
- additional wash;
- re-cleavage / extended cleavage;
- re-precipitation;
- NH4I reduction;
- manual intervention.

The parser is intentionally lightweight and deterministic. It does not invent chemistry. High-confidence structured interpretation may be immediately useful, while generic/ambiguous notes remain available for human review.

A useful outcome chain can therefore remain traceable as:

```text
Issue observed
   ↓
Intervention performed
   ↓
Resolution recorded
   ↓
Final result recorded
```

An issue is not automatically a failed synthesis.

---

## Run traceability

V5 reuses the application's existing Work Item / Run hierarchy rather than adding a second independent run system.

Experimental records can carry:

```text
work_item_id
run_id
```

The important behavior is operator-facing rather than ID-facing: the user should not have to type a technical Run ID every time.

When the Planner already knows the current work item and active run, that context can be attached automatically to Result, Issue, Cleavage, and Outcome records.

This makes it possible to answer a later question such as:

> Which exact planned conditions produced this measured loading or this issue?

without relying on memory or manually duplicated notes.

---

## Evidence and model policy

SPPS Planner deliberately separates evidence classes.

### Evidence classes

| Type | Meaning |
| --- | --- |
| Observed / Verified | Operator-reviewed experimental measurement or outcome |
| Parsed | Imported/interpreted record awaiting stronger review |
| Incomplete | Preserved record missing information required for a target/use |
| Excluded | Retained for audit but intentionally excluded from recommendation/training use |
| Operator rule | Explicit rule approved for the workflow |
| Empirical estimate | Public-safe fallback derived from implemented heuristic logic |
| Model output | Prediction generated by an explicitly built local model |
| Literature / chemistry reference | General reference or warning evidence; not private experimental truth |

### Recommendation order

The exact route varies by advisor, but V5 follows an evidence-first principle:

1. repeated successful relevant history;
2. exact bottle-/sequence-/product-level evidence where eligible;
3. coherent category-level evidence;
4. bounded interpolation inside observed ranges;
5. chemistry/risk reference or empirical fallback;
6. insufficient evidence.

### What the system intentionally avoids

- silent extrapolation presented as reliable evidence;
- mixing incompatible resin/amino-acid categories merely to inflate sample size;
- automatically verifying imported rows;
- treating a generated plan as if it were an experiment;
- automatic retraining after each result;
- automatic application of model-only recommendations;
- guessing unresolved units;
- synthesizing a fake historical cocktail by combining unrelated records.

---

## Public data and privacy model

The GitHub package is a **sanitized public build**.

It includes:

- the experimental-data schema;
- recording UI;
- import workflow;
- recommendation logic;
- similarity / evidence logic;
- model-management code;
- public-safe generic rules;
- empty public experimental seed instructions.

It does **not** intentionally include:

- internal/company/user experimental history;
- private product-to-sequence mappings;
- private exact-sequence cleavage anchors;
- internal operator records that reveal confidential experimental conditions.

The public experimental seed directory contains only public-safe guidance. Users add their own authorized data locally after installation.

See [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md).

---

## Runtime data locations

The public build keeps user-generated runtime information outside the source repository.

On Windows, the core public-build application directory is based on:

```text
%LOCALAPPDATA%\SPPS_Planner_PUBLIC\
```

Related session/runtime components use the public-build-specific user directory configured by the release profile.

Runtime data may include:

- projects / sessions;
- experimental SQLite databases;
- imported lab data;
- model files and registry metadata;
- runtime logs;
- generated outputs / exports;
- linked analytical-file metadata.

These files should not be committed to a public Git repository unless the user has deliberately reviewed and authorized them for publication.

The included `.gitignore` blocks common runtime databases, private-data directories, build outputs, archives, logs, virtual environments, and generated artifacts.

---

## Repository structure

```text
SPPS-PLANNER/
├─ main_launcher.py
│  Desktop entry point
│
├─ suite_gui/
│  Tkinter GUI, workflow controllers, experimental-data integration,
│  recommendation logic, risk/evidence, model registry, batch/project UI
│
├─ apps/spps_planner_app/
│  ├─ spps_planner/
│  │  Parser, calculation engine, CLI/core utilities, database/export logic
│  └─ data/
│     Public reagent/process defaults, catalogs, templates,
│     public-safe experimental seed area
│
├─ peptiforg_core/
│  Shared UI/helper layer retained by the release
│
├─ tests/
│  Regression, behavior, safety, release, and V5 decision-support tests
│
├─ tools/
│  Release verification, packaged-runtime verification, database/source audits
│
├─ docs/
│  User manuals, architecture, parser/data contracts, V5 decision-support docs
│
├─ assets/
│  Application icons
│
├─ installer/
│  Inno Setup configuration and version metadata
│
├─ BUILD_EXE_ONLY.bat
├─ BUILD_INSTALLER.bat
├─ INSTALL_BUILD_TOOLS_AND_BUILD.bat
├─ SPPS_Planner.spec
├─ requirements.txt
├─ requirements-dev.txt
├─ PUBLIC_DATA_POLICY.md
├─ CONTRIBUTING.md
├─ CHANGELOG.md
├─ CITATION.cff
├─ LICENSE
├─ VERSION
└─ README.md
```

### Important implementation areas

| Area | Key files |
| --- | --- |
| Desktop entry / release contract | `main_launcher.py`, `suite_gui/release.py`, `suite_gui/release_contract.py` |
| Planner UI / controller | `suite_gui/controller.py`, `suite_gui/classic_base.py`, `suite_gui/ui_build.py` |
| Generate / Apply Change | `suite_gui/synthesis_workflow.py`, `suite_gui/modules/plan_workflow.py` |
| Project / state | `suite_gui/project_workflow.py`, `suite_gui/peptide_item_state.py`, `suite_gui/state_persistence.py` |
| Experimental DB | `suite_gui/experimental_data.py` |
| Loading / Cleavage advice | `suite_gui/ml_advisor_v5.py`, `suite_gui/empirical_cleavage_v5.py` |
| Explicit Loading model | `suite_gui/model_registry_v5.py` |
| Natural-language Issue Log | `suite_gui/natural_language_issue_v5.py` |
| Recommendations window | `suite_gui/modules/experimental_data_panel.py` |
| Cleavage UI / NH4I rescue | `suite_gui/modules/cleavage_panel.py` |
| Batch materials | `suite_gui/material_presentation.py`, `suite_gui/modules/batch_manager_panel.py` |
| Core engine | `apps/spps_planner_app/spps_planner/engine.py` |
| Parser | `apps/spps_planner_app/spps_planner/parser.py` |

For a deeper view, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## Windows build

SPPS Planner is Windows-first and includes a reproducible release workflow.

### Portable EXE

```bat
BUILD_EXE_ONLY.bat
```

Expected output:

```text
dist\SPPS_Planner\SPPS_Planner.exe
```

The EXE build runs packaged-runtime validation and does not treat successful PyInstaller file creation alone as proof that the packaged application works.

### Installer

With Inno Setup available:

```bat
BUILD_INSTALLER.bat
```

Expected output:

```text
installer\output\SPPS_Planner_Setup_V5.0.0.exe
```

### Install/check build tools and build

```bat
INSTALL_BUILD_TOOLS_AND_BUILD.bat
```

This workflow checks the supported Python environment and Windows build tooling, installs/checks dependencies, builds the portable application, validates the packaged runtime, and builds/validates the installer.

For the Windows release checklist, see [docs/WINDOWS_BUILD_KO.md](docs/WINDOWS_BUILD_KO.md).

---

## Verification and regression testing

### Full release verification

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

For repeated verification passes:

```bat
python tools\verify_release.py --passes 5
```

The release verifier checks required release files and version identity, validates the active controller contract, runs Windows release checks, audits prohibited runtime GUI rebinding, compiles the active source, and runs the complete pytest suite.

### Windows release contract

```bat
python tools\verify_windows_release.py
```

### Runtime rebinding / monkey-patch audit

```bat
python tools\audit_monkey_patches.py --active-release
```

The active release is expected to avoid runtime monkey-patch composition, duplicate release-controller routes, and placeholder feature substitution.

### Important V5 regression areas

The test suite includes contracts for:

- sequence/parser behavior;
- Generate / Apply Change synchronization;
- 2-CTC and amide-family loading behavior;
- C-terminal handling;
- repeats and doubling;
- material ordering and totals;
- project/session persistence;
- batch workflows;
- custom database behavior;
- public release identity;
- Cys 100 eq-per-Cys hard rule;
- prevention of double-adding Cys equivalents;
- empirical cleavage fallback;
- bounded target-loading inversion;
- explicit Loading-model rebuild/promotion/rollback;
- run linkage;
- bilingual natural-language issue parsing;
- NH4I concentration limit;
- experimental DB fast initialization;
- public data/release contracts.

---

## Performance design

V5.0.0 includes a focused fix for a visible delay when opening the Recommendations / Lab History window.

The experimental database stores a schema/meta marker for canonical-key backfill work. Expensive canonical-key backfilling is therefore not intended to repeat on every ordinary database initialization once the required migration has already been completed.

The process also keeps a safe per-process initialization fast path, and the recommendations UI schedules heavier data refresh after the window is created so the window can become visible without waiting for every history/data-health view to populate first.

The design goal is:

```text
Button click
   ↓
Window becomes visible promptly
   ↓
Advisor / heavier history data populate without blocking initial appearance
```

This optimization is deliberately implemented without replacing real content with fake placeholder results and without deleting evidence/history functionality.

---

## Scientific scope and limitations

SPPS Planner is a research/planning tool. It is not a validated manufacturing control system and is not a substitute for professional chemical safety practice.

### The user remains responsible for

- verifying sequence identity and modifications;
- confirming the selected protecting-group form and bottle identity;
- checking resin loading and scale units;
- reviewing reagent equivalents and concentrations;
- verifying coupling and deprotection chemistry;
- reviewing repeat/doubling decisions;
- checking cleavage composition and amount;
- confirming precipitation/workup conditions;
- confirming compatibility with the actual reactor, resin, solvent volume, and equipment;
- reviewing current SDS and institutional safety procedures;
- validating predicted/recommended conditions experimentally.

### Recommendations are not universal chemistry laws

Empirical curves and decision-support rules are implementation baselines. They may be inappropriate for a particular peptide, protecting-group set, resin, scale, reactor, scavenger system, or laboratory SOP.

### Historical evidence can be biased

A local evidence base reflects what was recorded. It may contain selection bias, operator effects, scale effects, incomplete records, changing analytical methods, or hidden confounders. More records do not automatically imply causal truth.

### Model output is advisory

The Loading model is a local regression aid built from reviewed data. Cross-validation metrics help evaluate the candidate but do not guarantee future performance or transferability to unobserved chemistry.

### Cleavage / rescue guidance requires review

The Cys hard rule, empirical length curve, cocktail fallback, and NH4I rescue settings are explicit software/operator rules. They must still be checked against the actual chemistry and approved local procedure.

---

## Documentation map

### Start here

- **[README.md](README.md)** — full English project overview
- **[README_KO.md](README_KO.md)** — full Korean project overview
- **[docs/USER_MANUAL_EN.md](docs/USER_MANUAL_EN.md)** — concise English operator manual
- **[docs/USER_MANUAL_KO.md](docs/USER_MANUAL_KO.md)** — Korean operator manual

### Technical documentation

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — active runtime architecture and workflow ownership
- **[docs/SPPS_PARSER_CONTRACT.md](docs/SPPS_PARSER_CONTRACT.md)** — sequence parser contract
- **[docs/SPPS_REAGENT_DATABASE_SCHEMA.md](docs/SPPS_REAGENT_DATABASE_SCHEMA.md)** — reagent database schema recommendation
- **[docs/V5_DECISION_SUPPORT_EN.md](docs/V5_DECISION_SUPPORT_EN.md)** — V5 evidence-driven decision-support summary
- **[docs/V5_DECISION_SUPPORT_KO.md](docs/V5_DECISION_SUPPORT_KO.md)** — Korean V5 decision-support detail
- **[docs/DATA_SYSTEM_KO.md](docs/DATA_SYSTEM_KO.md)** — project/run/data-system notes
- **[docs/WINDOWS_BUILD_KO.md](docs/WINDOWS_BUILD_KO.md)** — Windows build/release guide

### Historical design reference

- **[docs/V4_EXPERIMENTAL_ML_KO.md](docs/V4_EXPERIMENTAL_ML_KO.md)** — retained V4 experimental-data/ML design background. It is a historical reference; current behavior is documented by the V5 files and code.

### Project policy

- **[PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md)** — public/private data boundary
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — contribution and validation rules
- **[CHANGELOG.md](CHANGELOG.md)** — release changes
- **[LICENSE](LICENSE)** — custom academic citation license
- **[CITATION.cff](CITATION.cff)** — GitHub-compatible citation metadata

---

## Contributing

Contributions are welcome when they preserve the release's key contracts.

Before proposing a change, please read [CONTRIBUTING.md](CONTRIBUTING.md).

In particular:

- do not rewrite the application from scratch to solve a local issue;
- do not replace working workflows with simplified imitation screens;
- do not add runtime monkey patches;
- do not add placeholder/dummy training data to make a feature appear functional;
- do not silently change the scientific meaning of protected reagents or sequence tokens;
- keep planned conditions separate from measured evidence;
- keep model rebuilding explicit;
- keep public distributions free of confidential experimental history;
- add or update regression tests for behavior changes.

A pull request that changes calculation or recommendation behavior should explain:

1. the user-facing problem;
2. the old behavior;
3. the new behavior;
4. why the change is scientifically/operationally justified;
5. which regression tests demonstrate that unrelated behavior was preserved.

---

## Citation

If SPPS Planner, SPPS Planner-generated outputs, derived workflows, or modified versions are used in academic work, the included license requires citation/attribution.

Recommended repository citation:

> Woo, S. **SPPS Planner: Solid-Phase Peptide Synthesis Planning and Evidence-Driven Decision Support.** GitHub repository, Version 5.0.0. https://github.com/SanghunWoo-23/SPPS-PLANNER

GitHub can also read the included [CITATION.cff](CITATION.cff) and provide a **Cite this repository** interface.

If a release DOI becomes available, use the DOI for the corresponding release in addition to the repository citation as required by the license.

---

## License

SPPS Planner is distributed under the included **SPPS Planner Public Academic Citation License, Version 1.0**.

It is a custom public-source license intended to permit academic, educational, research, portfolio-review, and non-commercial use under its stated conditions, including attribution/citation requirements.

It is **not** an OSI-approved open-source license unless the license is changed to an OSI-approved license in a future release.

Read [LICENSE](LICENSE) before redistribution or reuse.

---

## Troubleshooting

### The application does not start from source

Confirm the supported Python version and reinstall dependencies inside a clean virtual environment:

```bat
python --version
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

### Tkinter window does not appear

Use a normal desktop Python installation that includes Tk support. Headless/server Python environments are not the intended operator environment.

### Build script creates files but validation fails

Treat the validation failure as a real release failure. The build scripts intentionally distinguish file creation from packaged-runtime correctness.

Run:

```bat
python tools\verify_release.py
python tools\verify_windows_release.py
```

and review the first failing check.

### Recommendation window has little or no useful history

That is expected in a new public installation. The public build starts without private experimental history. Record/import authorized local data and review it before expecting history-driven recommendations.

### Loading model is unavailable

The model registry requires enough eligible Verified measured loading rows. A model is not built merely because records exist. The current minimum is 12 eligible Verified rows with at least 3 distinct measured loading values.

### A Loading recommendation is not applied

The advisor may have evidence to display while still refusing automatic Apply. This is intentional when the requested target would require extrapolation or when an exact/eligible condition is not sufficiently supported.

### Cleavage recommendation seems high for a Cys-containing peptide

Check the Cys count. V5.0.0 implements an explicit `100 eq × Cys count` operator hard rule, independent of peptide length.

### NH4I concentration above 0.2 M is rejected

This is deliberate. The current operator rescue protocol blocks/warns concentrations above 0.2 M because precipitation can make the rescue condition unusable.

### Imported numeric usage has no mL/L interpretation

If the source record has no reliable unit, the software preserves it as unresolved instead of guessing. Review and assign the correct unit manually.

### Public repository contains no experimental seed data

That is intentional and is part of the public data policy.

---

## FAQ

### Is SPPS Planner an automated synthesis controller?

No. It is a planning, calculation, traceability, and decision-support desktop application. It does not directly control synthesis hardware in this release.

### Does the software automatically optimize synthesis conditions?

It can recommend conditions from eligible history, bounded evidence, empirical rules, and an explicitly built local Loading model. It intentionally avoids presenting unsupported extrapolation as optimization truth.

### Does adding an experimental result retrain the model?

No. Rebuild is explicit.

### Can I use it with no historical data?

Yes. The public package is designed to remain useful with an empty experimental database through the core planner, public-safe defaults, and generic evidence-aware fallbacks.

### Can I import my own laboratory data?

Yes. The experimental-data system supports local recording/import workflows. Only use data you are authorized to process and publish.

### Does the public repository include the developer's internal experimental history?

No. The public package intentionally excludes internal/private experimental seed history and private product mappings.

### Are recommendations automatically written into the Plan?

No. Apply behavior is explicit and evidence-gated. Model-only outputs are not silently applied.

### Why are History and Data Health under Advanced?

They are important for audit and evidence management but are not the primary action during every synthesis. The main V5 operator flow prioritizes Add Result, Add Issue, and the current recommendation.

### Why does the program preserve raw notes as well as parsed fields?

Because structured interpretation can be wrong. Keeping the original observation provides auditability and allows later review without losing what the operator actually wrote.

### Why keep a V4 design document in a V5 repository?

Some of the current experimental-data architecture evolved from the V4 design. The V4 document is retained as historical background, while current behavior is defined by V5 documentation, code, and tests.

### Is this open source?

The source is publicly available under a custom academic citation license. That license is not OSI-approved, so the project should not be described as OSI open source unless the licensing changes.

---

## Version

Current public release:

```text
V5.0.0
```

Version identity is also stored in [VERSION](VERSION) and [VERSION.txt](VERSION.txt) and is checked by the release verification tooling.

---

<div align="center">

**SPPS Planner V5.0.0**  
Planning should stay editable. Evidence should stay attributable. Models should stay advisory.

</div>
