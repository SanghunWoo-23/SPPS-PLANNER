# SPPS Planner V6.0.0 Architecture

> Final V6.0.0 source release (2026-09-15). This document describes the current V6 implementation; V5 names are retained only where they are persisted-data or import-compatibility contracts.

## Stable entry points

- `main_launcher.py` prepares the packaged runtime and calls `suite_gui.spps_tk_gui`.
- `suite_gui.spps_tk_gui` re-exports the canonical API from `suite_gui.release`.
- `suite_gui.release` validates and launches `suite_gui.controller.SPPSGui`.
- `suite_gui.menu` is the canonical menu owner. `suite_gui.v3_menu` is compatibility-only.

The active UI construction route is explicit and does not use runtime monkey patches:

```text
controller.SPPSGui._build
  -> ui_build base/interface construction
  -> modules/ui_ownership canonical finalization
  -> release UI finalization
  -> direct controller action binding
  -> ui_system theme / geometry / shortcuts
  -> menu.install_menu
```

## Core planning path

```text
PlanInput
  -> SPPS calculation engine
  -> step/material generation
  -> one presentation/normalization layer
  -> editable operator Plan
  -> Materials / Checklist / Cleavage / Batch / Export
```

The embedded engine remains chemistry-locked by golden behavior snapshots. Plan generation remains planning state; it does not become experimental evidence until an actual Result/Issue is linked to a Run.

## Project / Run / evidence path

```text
Project -> Work Item -> Run
  -> frozen Planner snapshot at Start Experiment
  -> actual execution / correction ledger
  -> Loading / Cleavage / Outcome / Issue / HPLC / Analytical records
  -> reviewed evidence
  -> explicit recommendation/model lifecycle
```

There is one Run hierarchy. Repeat Run uses `repeat_of_run_id`; measured Results/HPLC/Analytical records are never copied into a new repeat.

## Experimental data store

`suite_gui.experimental_data` owns the SQLite schema and canonical record operations.
`suite_gui.experimental_workflow` owns GUI-facing initialization, Private seed loading, same-profile legacy DB recovery, read/write routing, data-store diagnostics, advisors and model lifecycle.

R11 data-store rules:

- every controller read/write initializes the same resolved database path;
- Private historical data is recovered only from same-profile locations;
- explicit operator/test DB paths never absorb unrelated global history;
- a failed Private seed import is not cached as successful;
- Loading/Cleavage writes must be observable by record ID before being reported as successful;
- Public remains useful with an empty local DB and ships no Private SQLite/history.

Persisted names such as `experimental_v5.sqlite`, `planner_snapshot_v6`, `model_registry_v5.json`, and existing evidence-source strings are compatibility contracts. They may retain their historical names until an explicit migration is implemented and tested.

## Recommendation layer

The real implementations are version-neutral owners under `suite_gui/recommendation/`:

- `loading.py`
- `cleavage.py`
- `coupling.py`
- `history_base.py`
- `coupling_base.py`
- `decision_support.py`
- `empirical_cleavage.py`
- `model_registry.py`

Legacy V4/V5 import modules are compatibility surfaces only. No V6 wrapper stack is added. Recommendation traces record operator decisions separately from supervised Loading/Cleavage evidence and never trigger automatic retraining.

## Version-neutral runtime state

`suite_gui.runtime_state.PlannerUIState` owns active UI state. Current execution modules use stable accessors for active index, switching, editors, Generate/Apply guards, drag state, batch state, density, Work Item window, and preview state. Historical `_v###` attributes exist only inside the compatibility boundary so older tests/extensions/project state can still be read intentionally.

## Canonical support modules

- `menu.py`: menu construction
- `issue_parser.py`: deterministic Korean/English Issue parser
- `material_usage.py`: unit-preserving material-usage import/review
- `decision_support.py`: provenance, A/B, analytics and quality helpers
- `persistence_workflow.py`: atomic project/session persistence
- `data_system.py`: Work Item/Run/HPLC/Analytical hierarchy
- `data_workbook.py`: workbook round-trip
- `execution_workflow.py` / `synthesis_execution.py`: actual execution ledger
- `risk_engine.py` / `risk_workflow.py`: warning/review-only risk triage
- `ui_system.py`: theme, geometry and shortcuts

Historical files `v3_menu.py`, `natural_language_issue_v5.py`, `v5_material_usage.py`, and `v6_features.py` are compatibility shims and do not own current implementation.

## Current analytical and feedback extensions

- Recommendation trace: recommendation -> operator decision -> actual condition -> Result links.
- Matched Repeat: descriptive changed variables plus yield/purity deltas; single pairs never imply causation.
- Structured LC-MS/MALDI/Other records linked to Runs.
- Expected mass can be loaded from the frozen Run Planner snapshot; observed m/z is never used to invent missing neutral mass identity.
- Analytical completeness reports whether HPLC, MS identity and yield have been recorded; it is not an automatic scientific pass/fail.

## Performance policy

FAST_OPEN is protected with deterministic initialization counters rather than fragile wall-clock gates. Repeated `initialize()` must not redo full schema migration/backfill when the DB has already been initialized and remains healthy. Heavy history views remain candidates for lazy population.

## Public / Private boundary

Public and Private use the same functional source wherever practical. Private may contain operator seed/history and Private-only regression data. Public must contain no Private DB, seed rows, model files, secrets or local paths.

## Verification

From repository root:

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
pytest -q
python tools\verify_v6_integrity.py
python tools\verify_windows_release.py
python tools\verify_release.py --passes 1
python tools\audit_monkey_patches.py --active-release
```

The governing rule is: **fix the canonical owner; do not stack another patch/version layer.**
