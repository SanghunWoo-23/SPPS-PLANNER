# SPPS Planner V7.0.0 Final R2 Release Notes

**Date:** 2026-10-08  
**Release:** V7.0.0 Final R2

Final R2 is a focused bug-fix/usability revision of V7 Final R1. It restores the intended direct-loading behavior in the Project Manager Add/Edit workflow without changing the locked chemistry engine.

## Direct resin loading behavior

- Add/Edit STEP 1 now shows **Direct resin loading (2-CTC only)**.
- Selecting `2-CTC` automatically enables and checks direct loading.
- Selecting `Rink Amide AM`, `CTC(합성기)`, or another non-direct-loading resin forces the option OFF and disables it.
- A 2-CTC operator may still uncheck the option for an exceptional already-loaded resin.
- Legacy 2-CTC project rows that have no saved `apply_loading_calc` field open with direct loading enabled.
- The saved Project item now carries `apply_loading_calc`, `loading_aa_eq`, `loading_diea_eq`, and `loading_time_h`, so Add/Edit and Project calculation use the same direct-loading state.

The standard direct-loading defaults remain resin : amino acid : DIEA = **1 : 2 : 4** unless the operator changes the established setup values.

## R1 behavior retained

- Larger Recommendations/Lab History workspace.
- Ether / n-Hexane post-cleavage workup in Project workflow.
- Generate / Apply recalculates Plan, Materials, Checklist, Total Materials, Cleavage and Workup from one current snapshot.
- Exact bottle identities, My recipes, Favorites, backup/import, recent bottles, edit-change feedback, and Public/Private separation remain unchanged.

## Chemistry lock

No locked chemistry-engine behavior was changed.

- `engine.py`: `5cf59ad71ea1637df4768d812612a86635b31c691efc153f93ef328d736108de`
- `tests/test_engine_behavior_snapshots.py`: `47ea8329033c5ff88ce8cbf705d3385b20455a7872ba01bbddad88bc726cd886`
