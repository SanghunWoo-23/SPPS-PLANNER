# SPPS Planner V9.0.0 — Input Integrity and Runtime Refinement

**Development build · 2026-11-08 · not native-Windows or experimental validation.** The application version remains `V9.0.0`; the internal `SPPS data v6.0.0` schema identifier is retained for compatibility.

## Changes

1. Strict positive integer checks for Copies and coupling steps; fractional values, booleans, NaN and infinity cannot silently truncate.
2. Recompute imported/saved head-to-tail reaction records before reuse, export or application, checking sequence, resin, protection policy, scale, copies, reagent mmol and all stored method fields. Modified/stale drafts require operator review.
3. Preserve nonzero small mmol/solution-volume values using significant figures, and reject arithmetic overflow rather than serializing infinity.
4. Preserve unsaved reagent-equivalent inputs when switching among head-to-tail reagent systems.
5. Add dialog-scoped Auto Plan mouse-wheel scrolling without global Tk event or Treeview styling changes.
6. Restore an operator yield scenario only if stored sequence/resin/scale/copies/product path context matches; this is scenario arithmetic, not a predictive model.
7. Extend the packaged `--self-test` to exercise V9 protected mass and reaction integrity.

## Invariants

- Original `engine.py` Plan and Materials chemistry authority remains unchanged.
- Protection retention after mild selective cleavage is theoretical and conditional on experimental chemistry.
- Branch/Cyclic support remains explicitly limited; unsupported chemical topologies fail closed.
- Methods are unapproved review drafts and never overwrite Plan/Materials invisibly.
- Public/Private source and data remain separated.

## Checks

```bash
PYTHONPATH=.:apps/spps_planner_app python -m pytest -q
PYTHONPATH=.:apps/spps_planner_app python tools/verify_windows_release.py
PYTHONPATH=.:apps/spps_planner_app python main_launcher.py --self-test
```

Native Windows 3.11/3.12, PyInstaller EXE, Installer, and wet-lab qualification require separate evidence. Exact test counts are recorded in the external release handover report.
