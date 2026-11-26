# SPPS Planner V9.0.0 — Development Build (Not Final)

This V9.0.0 source release retains the Windows/Tkinter Project Manager, editable Step 1/2, Generate/Apply, Materials, Checklist, Cleavage, Workup, and local project/history workflows. **Do not mistake source tests for Windows native installer or scientific validation.**

## V9 functionality (cumulative)

- Nα-Fmoc-free protected AA catalog (`H-Ser(tBu)-OH`, `H-Lys(Boc)-OH`, etc.), separate reagent MW and product residue MW; `K(Dde)` distinct from `K(ivDde)`.
- Operator-selectable linear protected/deprotected and head-to-tail protected/deprotected **average neutral MW**; Checklist MW for supported linear operations, with explicit resin-bound-equivalent labeling.
- Protected selective-cleavage / head-to-tail / global-deprotection review rows, and operator-entered yield scenario (NOT a trained yield predictor).
- **New:** Head-to-tail reaction method editor (`DIC/HOBt`, `EDC·HCl/HOBt`, `HATU/DIEA`, `PyBOP/NMM`, `DIC/Oxyma`) with role-separated reagents, individual operator-entered eq, mmol and dilution volume calculations, solution solvent/time/temperature, and source-linked unapproved drafts in JSON/Checklist. No automatic validated protocol or catalyst selection for unsupported reaction types.
- **New:** One Lys ε-amide branch attached to a plain L-amino-acid arm, e.g. `K(GGEP)`, has a limited **final-product theoretical MW** with condensation and removable Lys handle accounted for. Multi-branch, D-branch, or non-Lys branch fail closed; stepwise branch Checklist MW remains unavailable.
- **New:** Auto Plan dialog vertical scrollbar; saved matching reaction draft can be restored only when sequence/resin/scale/copies/protection policy match.

## 2026-11-08 quality refinement

- Strict integer parsing for Copies/coupling steps (no silent truncation or NaN acceptance).
- Head-to-tail review JSON is independently recomputed before reuse/export/application; modified or stale numeric fields are rejected.
- Small nonzero mmol values retain significant figures; overflow is rejected rather than exported as Infinity.
- Reaction method selector retains user-entered equivalents when switching systems.
- Auto Plan mouse-wheel scroll is scoped to the dialog; no global Treeview style or bind_all mutations.
- Yield scenario may restore only when sequence, resin, scale, copies and product pathway match the saved context.
- Headless packaged `--self-test` now checks V9 protected mass, reaction review round-trip and unestimated yield.
- V9 regression additions: `tests/test_v9_input_integrity_refinement.py`.
- [Korean quality notes](docs/V9_QUALITY_REFINEMENT_KO.md) · [English quality notes](docs/V9_QUALITY_REFINEMENT_EN.md).

## Scientific and deployment limitations

- This is a **review planner**, not an autonomous synthesis optimizer, validated cyclization SOP, or experimental yield prediction. All reagent eq/concentration/time originate with the operator.
- Only solution-phase head-to-tail amide bond mass is quantitatively supported for cyclization (−H2O). On-resin head-to-tail, disulfide, lactam, RCM and click require explicit atomic graphs and remain unsupported in this module. C-terminal amidation and N-terminal caps block automatic head-to-tail calculation.
- Retained side-chain protection after selective cleavage is a conditional assumption, not a measured result. The original global-TFA Cleavage Cocktail pane is **not** a selective-cleavage SOP. No MS adduct/m/z or exact isotopic mass is claimed.
- Selected operator methods are tagged **unapproved** and never silently overwrite the primary Plan/Materials/Batch reagent quantities. Bottle-specific masses and volumes are not inferred.
- Existing yield percentages are strictly operator-entered scenarios. No ML-derived probability or yield guarantee.
- Windows native GUI, EXE, Installer upgrade/uninstall, and laboratory chemistry have not been verified.

[Reaction & Branch guide (KO)](docs/V9_REACTION_AND_BRANCH_KO.md) · [Reaction & Branch guide (EN)](docs/V9_REACTION_AND_BRANCH_EN.md) · [Mass/Yield guide (KO)](docs/V9_PROTECTED_MW_AND_YIELD_KO.md)

## Source checks

Use `PYTHONPATH=.:apps/spps_planner_app python -m pytest -q` for headless tests and `PYTHONPATH=.:apps/spps_planner_app python tools/verify_windows_release.py` for the static Windows build contract. GUI widget smoke tests require a real display or Linux Xvfb; a successful simulated GUI run does not validate native Windows.

**Only Public belongs on GitHub. Private data, experimental seeds, local projects, and runtime DB files must not appear in the Public ZIP.**


## 2026-11-08 — Literature evidence update (still V9.0.0)

The Head-to-tail method editor now attaches reference-scoped literature risk flags; see `docs/V9_LITERATURE_REACTION_UPGRADE_KO.md` and `docs/REACTION_LITERATURE_V9.0.0.json`. Values remain operator-input only; no wet-lab/Windows native validation claimed.

## 2026-11-08: Local AI + Excel/CSV review enhancement

- New import/preview/column mapping UI and local-only ML assistant; see `docs/V9_AI_EXCEL_ASSISTANT_EN.md` and `_KO.md`.
- Operator review is required before saving user outcomes; models are evaluated on sequence-group holdout and withheld when unreliable. No chemistry default changes.
- Public/Private profiles stay separate; no uploaded experiment data is bundled in this source release.

2026-11-11 V9.0.0 advanced graph/ML supplement: Backbone-specific N-terminal detection (Lys/Pro); explicit one-Lys-branch + main-chain head-to-tail independent RDKit verification; MS exact m/z candidates; external ML run-ID leakage and independent-prediction-group validation; deterministic chemistry matrix; Windows packaged EXE CI smoke-test step. Experimental validation and native Windows installer acceptance remain unverified. See docs/V9_ADVANCED_GRAPH_MS_EXTERNAL_QA_EN.md.
