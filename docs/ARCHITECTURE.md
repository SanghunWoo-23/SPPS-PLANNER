# SPPS Planner v7.0.0 Architecture

This document gives a concise map of the public source tree. It intentionally omits historical implementation notes and private/internal data details.

## Entry points

```text
main_launcher.py
  → suite_gui.spps_tk_gui
  → suite_gui.release
  → suite_gui.controller.SPPSGui
```

The application uses direct canonical owners rather than a runtime monkey-patch stack.

## Main UI workflow

```text
Project Manager
  → Add/Edit peptide setup
  → Generate
  → editable Plan
  → Materials / Checklist / Cleavage / Export

Project Manager sequences/copies
  → Batch Manager
  → solution-preparation totals
```

Project-specific exact bottle selections do not rewrite Batch Manager solution-preparation defaults.

## Important modules

- `suite_gui/modules/` — current Project/Batch UI workflow modules.
- `suite_gui/controller.py` — main GUI controller.
- `suite_gui/project_workflow.py` — project-level planning workflow.
- `suite_gui/batch_workflow.py` — batch preparation workflow.
- `suite_gui/experimental_data.py` — local experimental data storage.
- `suite_gui/recommendation/` — recommendation logic.
- `apps/spps_planner_app/spps_planner/engine.py` — SPPS calculation engine.
- `suite_gui/reagent_library.py` — reagent/bottle metadata support.

## Project Add/Edit ownership

V7 peptide setup is owned by the Project Manager Add/Edit dialog.

It handles:

- sequence, scale, copies, resin, loading and LOT;
- coupling reagent / additive / base / solvent identity;
- My recipes and recent bottle convenience state;
- pre-save validation and setup review;
- edit-change detection and stale-result invalidation.

## Chemistry engine boundary

The calculation engine is treated as a separately validated core. UI refactoring should not change engine behavior incidentally.

Regression coverage includes behavior snapshots and release/integrity checks under `tests/` and `tools/`.

## Public / Private boundary

The public source tree contains application code but no bundled company experimental history, private seed database, original laboratory photographs, or confidential sample records.

Private and Public builds use separate ancestry and profile configuration. Do not reconstruct a Private build from the Public repository.

## Runtime user data

User-created projects, local experimental data, and My recipes are written to user-writable runtime locations rather than the installed source tree.

Release ZIPs should not bundle runtime output or user recipe files.

## Verification

Primary public verification commands:

```bat
python -m pytest -q
python tools\verify_v7_integrity.py
python tools\verify_windows_release.py
python tools\verify_release.py
```

See `CONTRIBUTING.md` for development guidance and `docs/WINDOWS_BUILD_KO.md` for packaging.
