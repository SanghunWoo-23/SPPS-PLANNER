# V3.0.0 Monkey-Patch Removal History

This historical record describes the V2 refactor that became the static
V3.0.0 controller. The current visible and internal release identity is V3.0.0.
Working UI, calculation, editable Plan, Apply Change propagation, Project
Manager, Batch, Custom DB, ML, persistence, and exports are compatibility
requirements.

## Eight-stage migration

1. **Complete** — baseline ZIP, behavior contracts, and patch audit
2. **Complete** — direct Controller and static public launch route
3. **Complete** — move UI build chain into direct methods
4. **Complete** — move Plan, Apply Change, and Doubling workflows
5. **Complete** — move Project, Batch, and persistence workflows
6. Pending — move Custom DB, ML, and Export panels
7. Pending — remove legacy controller, compatibility routers, and numbered patches
8. Pending — zero-patch audit, five-pass regression, and clean release ZIP

## Stage 2 result

The public path is now:

```text
main_launcher.py
  -> suite_gui.spps_tk_gui
  -> suite_gui.release
  -> suite_gui.controller.SPPSGui
```

`suite_gui.controller.SPPSGui` declares the operator-facing methods directly.
`suite_gui.release` no longer invokes the release-composition registry.

The legacy controller is still used as a temporary behavior superclass. This
is intentionally not described as final monkey-patch removal: the following
stages must move each `super()` implementation before that source can be
deleted.

## Stage 2 verification

- 63 non-GUI tests passed
- 21 display-dependent Tk tests were collected and skipped because the
  validation host has no graphical display
- release verification passed twice
- all ten audited public routes resolve to `suite_gui.controller`
- the direct controller source contains no `SPPSGui.method = ...`,
  `gui_cls.method = ...`, or `setattr(...)` runtime binding

## Stage 3 result

The active `_build` method no longer calls the inherited wrapper chain.
`suite_gui.ui_build.build_ui()` owns five explicit stages:

1. build the retained classic interface once
2. apply the editable Plan workspace
3. apply operator-facing layout corrections
4. apply the accepted resin/cleavage/title controls
5. restore persisted Custom DB values and its real editor tab

The order is covered by a dedicated contract test. Both `controller.py` and
`ui_build.py` are audited to reject runtime controller rebinding.

## Stage 3 verification

- 66 non-GUI tests passed
- 21 display-dependent Tk tests were collected and skipped on the headless host
- complete release verification passed twice
- all ten public routes still resolve to `suite_gui.controller`

## Stage 4 result

The six Plan calculation entry points now call
`suite_gui.synthesis_workflow` directly:

- `generate_update_plan`
- `pm_generate_selected`
- `pm_calculate_all`
- `apply_change`
- `pm_apply_change`
- `apply_plan_mw_density`

The direct service preserves the accepted final order: first synchronise the
unified AA/modifier/chemical defaults, then run the established Plan Generate
or Apply Change calculation. The visible Generate and Apply Change buttons
also call these controller methods instead of capturing workflow lambdas.

Focused headless contracts cover blank Doubling rules, a single `7:2` rule,
the `4-7:3` range, and the shared position system for natural AA, d-AA,
chemical, label, tag, and linker rows. Existing display-dependent tests retain
the full Materials/Checklist/Total and repeated-coupling checks.

## Stage 4 verification

- 72 non-GUI tests passed
- 21 display-dependent Tk tests were collected and skipped on the headless host
- the six Plan routes contain no inherited `super()` call
- Generate/Apply Change UI controls resolve through the direct controller

## Stage 5 result

Project Manager item actions now use `suite_gui.project_workflow` directly:
single-select, double-click restore, Add, Duplicate, multi-delete, and the
existing drag/reorder behavior all share the same item state helpers.

Project and autosave JSON now use `suite_gui.persistence_workflow`. The same
portable envelope retains `pm_items`, the selected index, Setup defaults,
editable Batch rows, and `custom_materials`. Writes remain atomic. Project
load and autosave restore accept the existing session shape and legacy
single-project JSON; removed `CTC(합성용)` values are migrated to
`CTC(합성기)` during restore.

The direct controller also owns Batch calculate, refresh, and export routes
through `suite_gui.batch_workflow`. Stage 7 subsequently extracted the Batch
internals into that service and removed the temporary legacy source. Retained
Save Session, Save Project, Load Project, Batch refresh, and Batch export
buttons are bound to the direct controller.

## Stage 5 verification

- 76 non-GUI tests passed
- 21 display-dependent Tk tests were collected and skipped on the headless host
- Project, save/load/autosave, and Batch controller routes contain no inherited
  `super()` calls
- a headless save/load round trip preserves Project items, defaults, Doubling
  rules, and Custom DB data
- legacy saved resin aliases are migrated during load

## Stage 6 result

Custom material management, observed-run ML data handling, and the accepted
visible-state export are now direct controller services:

- ``suite_gui/custom_db_workflow.py`` owns validation, lookup, class-filtered
  selector options, immediate setup refresh, autosave, and the existing
  ``Custom DB`` tab construction.
- ``suite_gui/ml_workflow.py`` atomically records actual yield, purity, failure
  state, doubling corrections, and notes; the same real CSV is used for model
  training and anomaly detection. Training requires at least five observed
  target values and does not create a placeholder model.
- ``suite_gui/export_workflow.py`` synchronizes the current modifier editor and
  exports the accepted visible Plan/Materials/Total/Checklist/Cleavage state.
- The public controller no longer delegates Custom DB, ML, or general export
  routes through ``super()``.

## Stage 6 verification

The regression suite adds direct checks for custom MW/density lookup and
selector reflection, atomic actual-run logging including doubling changes,
minimum real-data enforcement for ML, model-service routing, visible export
ordering, and controller routes without inherited patch calls.

- 83 non-GUI tests passed
- 21 display-dependent Tk tests were collected and skipped on the headless host
- complete release verification passed twice
- all 22 contracted public routes resolve to ``suite_gui.controller``
- no contracted active route resolves to ``legacy_controller``

## Stage 7 result

The temporary compatibility baseline has been removed from the source tree:

- `suite_gui/legacy_controller.py`, `suite_gui/release_composition.py`, the
  `suite_gui/compat` Python modules, and every numbered `modules/v*.py` patch
  module were deleted.
- `suite_gui/classic_base.py` is the static Classic UI source of record.
- Generate and Apply Change call `suite_gui.position_rules` directly, including
  blank rules, `7:2`, `4-7:2`, all synthesis-unit classes, and rule changes
  made after generation.
- Repeat=N now changes mmol, amounts, solvent, Materials, Totals, and Checklist
  as N actual coupling cycles with the accepted DMF wash order.
- Cleavage components are merged into Materials and Totals during Apply Change.
- Resin-family working-volume controls and live preview are constructed and
  updated directly without a legacy namespace callback.
- Public release import loads neither a numbered module nor a compatibility
  controller.

Stage 8 performs the final zero-rebinding cleanup and five complete repeated
release verifications.

## Stage 8 result

The refactor is complete:

- all obsolete workflow `install()` functions and nested `_build` wrappers
  were removed;
- the source audit reports **0 runtime controller bindings** and **0 build
  wrappers**;
- Ac-AA modifier parsing now lives directly in `spps_planner.parser`;
- unified AA/modifier chemistry and the accepted Total ordering now live
  directly in `modules.plan_workflow`;
- scheduled Tk callbacks are cancelled by the controller's declared
  `destroy()` method;
- no source import, class mutation, or release composition is required to
  assemble the accepted controller that became the V3.0.0 baseline.

`tools/verify_release.py` now checks the version/release contract, zero-patch
audit, compilation, and complete regression suite on every requested pass.
