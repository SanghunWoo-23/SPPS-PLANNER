# Changelog

## v6.0.0 R19 Batch sequence-prep correction — 2026-09-21

- Kept the tab name **Batch Manager**.
- Re-scoped compact Batch Manager to read Project Manager peptide sequences while calculating preparation quantities only from visible `Solution prep defaults`.
- Added visible `Scale mmol` to the Batch preparation defaults.
- Project-specific DIC/HOBt/HBTU choice, reagent equivalents, resin/loading conditions, and project scale no longer leak into compact Batch calculations.
- Compact coupling preparation now reports HBTU stock from Batch defaults; DIC/HOBt rows are not generated from Project history.
- AA and HBTU/NMP volumes use the selected concentration/equivalent defaults plus `Round-up mL` and `Extra reserve mL`.
- Removed the empty compact Catalyst/additive tab and simplified the Project summary to sequence/preparation-relevant fields.
- Dashboard numeric values are formatted for operator readability while exports retain calculation precision.
- Legacy editable Batch-table behavior remains available for compatibility.
- Chemistry engine and Loading/Cleavage recommendation rules are unchanged.
- Validation: Public 370 passed / 28 skipped headless and 395 passed / 3 skipped with Real Tk/Xvfb; Private 381 passed / 25 skipped headless and 406 passed with Real Tk/Xvfb.

## v6.0.0 R18 Batch auto-sync + package cleanup — 2026-09-21

- Restored automatic Project Manager → Batch Manager total-usage aggregation.
- `Refresh totals` is a force-recalculate action rather than an activation gate.
- Prevented blank/default Project placeholders from producing terminal-only phantom sequences.
- Kept Batch summaries traceable to the current Project Manager collection; no bundled sample/demo sequence is injected.
- Removed old per-checkpoint development-note files from release roots; retained only current release/user/build/data-policy documentation.
- Chemistry engine and Loading/Cleavage recommendation rules remain unchanged.
- Validation: Public 368 passed / 28 skipped headless and 393 passed / 3 skipped with Real Tk/Xvfb; Private 379 passed / 25 skipped headless and 404 passed with Real Tk/Xvfb.

## v6.0.0 R17 final polish — 2026-09-21

- Batch Manager now starts visually empty even when Project Manager contains previously saved projects.
- `Refresh totals` is the explicit activation point for the compact Project → Batch dashboard; opening the tab alone no longer displays a saved sequence.
- Preserved saved Project data while preventing a legacy active-index alias from turning an intentional `None` selection back into Project index 0.
- Persisted Batch rows remain restorable where the editable Batch path is used; absent Batch rows are no longer inferred from Project data.
- Chemistry engine, Loading/Cleavage recommendation rules, Public/Private data boundary, and R16 loaded-AA identity behavior remain unchanged.
- Validation: Public 368 passed / 27 skipped headless; 392 passed / 3 skipped with Real Tk/Xvfb. Private 379 passed / 24 skipped headless; 403 passed with Real Tk/Xvfb.

## v6.0.0 public release — 2026-09-18

- Prepared the validated R16 source line for public GitHub release.
- Refreshed README/README_KO, public release notes, citation metadata, data-policy status, and academic citation text.
- No chemistry-engine or recommendation-decision logic changes were introduced by this documentation/release-packaging refresh.

## V6.0.0 FINAL R16 — 2026-09-16

- Loading Advisor now recognizes data-supported special/non-natural loaded-building-block aliases such as `Cit`, `Hyp`, and `Dab` as explicit canonical identities rather than collapsing them into standard amino acids.
- D-form shorthand (`dL`, `D-Leu`, `(D)Leu`, protected short forms such as `D-His(Trt)`) resolves to explicit Fmoc-D identities while remaining strictly separated from the corresponding L-form evidence.
- Gly is treated as achiral; a synthetic `D-Gly` loading identity is not created.
- Existing user databases receive a lookup-key migration so legacy shorthand records can join the new exact-identity lookup without rewriting raw historical text.
- The Loading identity pick-list is derived from identities actually present in the active Loading database. Recognition alone is explicitly not treated as experimental support.
- Recommendation evidence shown to the operator is restricted to exact resin + exact normalized loaded-AA records; broad similarity remains diagnostic context only.
- Evidence tracing now labels `OBSERVED REPEATED CONDITION` as an exact experimental match and `CHEMISTRY DEFAULT` as a default fallback, even when broader similarity diagnostics are also present.

## V6.0.0 final source release — 2026-09-15

- Closed the R12/R13 stabilization line and promoted the tree to the final V6.0.0 source release.
- Loading CSV import now uses resin-aware base defaults: omitted Trityl/2-CTC base labels can resolve to DIEA, while Wang/Rink loading rows are not silently relabelled as DIEA.
- Historical loading seed review can enrich exact duplicate canonical rows with recovered source provenance without creating duplicate experiments.
- Public release remains data-sanitized and contains no Private experimental seed/history, manifests, staging ledgers, or source photographs.
- Final regression, Tk smoke, source integrity, Windows release contract, archive hygiene, and fresh-unzip validation are release gates.

## V6.0.0 development checkpoint R13 — 2026-09-15
- Preserved legitimate repeated Loading/Cleavage imports by limiting semantic de-duplication to bundled historical seed revisions.
- Added Loading source provenance display/import support and review-gated loading seed staging tooling.
- Kept chemistry engine behavior unchanged.


All notable public release changes are summarized here.

## V6.0.0 R11 development checkpoint — 2026-09-14

- Added pre-merge SQLite backup before importing new same-profile legacy experimental rows.
- Added read-only SQLite integrity checks and atomic per-source legacy merge rollback/audit state.
- Added explicit **Backup DB** operator action and Data Store recovery/backup diagnostics.
- Data Store counts now use SQL COUNT queries instead of materializing full history tables.
- Removed the redundant adjacent-V4 clone path for explicitly supplied experimental DBs.
- Coupling review + experimental outcome persistence is transactional: DB failure restores the Work Item review.
- Recommendation/Lab History callbacks are tracked and canceled on window destruction.
- Root shutdown cancels Tk callbacks to a fixed point; Public/Private monolithic Xvfb regression exits cleanly.
- Chemistry engine and golden behavior snapshots remain unchanged.

## V6.0.0 R10 development checkpoint — 2026-09-10

- Preserves the validated chemistry engine and golden snapshot behavior.
- Hardens Private experimental data discovery, same-profile legacy DB recovery, seed retry, and write/read verification.
- Adds Data Store diagnostics showing the actual SQLite path and record counts.
- Aborts Project save when the active Plan/Run state cannot be captured; revision/history advance only after successful publication.
- Requires manual confirmation for proxy/approx protected-reagent identities.
- Adds Recommendation → operator decision → Result linkage and history.
- Adds structured LC-MS/MALDI/Other records, frozen-Run theoretical mass loading, and analytical completeness review.
- Adds descriptive matched-repeat purity/yield deltas with explicit non-causal/small-N warnings.
- Moves active menu, Issue parser, material-usage importer and decision-support owners to version-neutral modules while retaining compatibility shims.
- Removes unused alternate GUI/data residues and moves the compound template under `docs/templates/`.
- Adds deterministic FAST_OPEN initialization/backfill counters and regression coverage.

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
