# Changelog

All notable public release changes are summarized here.

## V5.0.0 — 2026-09-02

### Core planner compatibility

- Preserves the validated editable Plan workflow and established Generate / Apply Change separation.
- Preserves Project, Batch, Materials, Checklist, Total Materials, Custom DB, persistence, export, parser, and Windows release paths.
- Keeps the visible edited Plan as the source for Apply Change recalculation.

### Loading decision support

- Added target-loading inverse recommendation workflow.
- Uses same-resin / same-loaded-amino-acid evidence where available.
- Restricts interpolation to observed evidence ranges and avoids treating extrapolation as reliable evidence.
- Keeps Parsed data provisional and prioritizes Verified measured loading records.
- Added quick measured-loading result recording with Planner/run context attachment.

### Loading model registry

- Added explicit Verified-data Loading model rebuild.
- Added cross-validation metadata and model version storage.
- Added candidate-versus-active validation comparison.
- Added explicit Promote Candidate and Rollback behavior.
- Added rebuild notification after approximately five new eligible measured loading results since the active model.
- Result entry does not silently retrain the model.

### Cleavage decision support

- Added public-safe empirical non-Cys peptide-length baseline.
- Added Cys hard rule: `100 TFA eq × Cys count`, independent of peptide length.
- Prevented the historical double-add regression where Cys equivalents could be applied twice.
- Kept manual/operator override behavior separate from automatic Cys increment logic.
- Kept cleavage cocktail and precipitation/workup evidence separate.
- Preserved unresolved units rather than guessing mL/L.

### Post-cleavage rescue

- Added optional `NH4I Reduction` under Post-cleavage Rescue.
- Default remains `None`.
- Added 2 eq / 0.2 M / 1 h operator preset and scale-based mmol/mass/volume calculation.
- Added block/warning for NH4I concentration above 0.2 M.
- NH4I is not automatically inserted into the normal cleavage cocktail.

### Experimental records and issue logging

- Simplified operator entry around Add Result and Add Issue.
- Added automatic Planner-condition snapshot and active Run linkage where available.
- Added bilingual Korean/English/mixed natural-language issue parser.
- Preserves raw observation text alongside structured interpretation.
- Keeps ambiguous notes reviewable instead of automatically treating them as ML-ready evidence.

### Recommendations UI

- Consolidated Recommendations and Lab History into a compact window.
- Daily workflow prioritizes Loading / Cleavage / All Conditions.
- History, Risk & Evidence, and Data Health remain available under Advanced.
- Add Result / Add Issue use compact operator-facing dialogs.

### Batch materials

- Uses one combined grouped material presentation.
- Operator-facing group order: L-AA → D-AA → Non-natural AA → Chemical.
- `Fmoc-Cit-OH` is classified as Non-natural AA.

### Performance

- Added experimental-database migration/meta tracking for canonical lookup-key backfill.
- Prevents repeating full lookup-key backfill during ordinary repeated initialization after migration is complete.
- Added process-level initialization fast path.
- Defers heavier recommendation/history refresh until after the recommendation window is created.

### Public release / privacy

- Public package contains no bundled private experimental history.
- Public experimental seed directory remains documentation-only/public-safe.
- Shared functional source remains aligned with the corresponding development code; build profile and data/policy content define public behavior.

### Documentation / release packaging

- Expanded English and Korean README files.
- Corrected the project-specific academic citation license metadata for SPPS Planner.
- Added `CITATION.cff` for GitHub citation support.
- Updated contribution and public-data policies.
- Retained V4 experimental-data design notes as clearly marked historical reference.
