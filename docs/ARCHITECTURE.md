# SPPS Planner V4.0.0 Architecture

## Stable entry points

- `main_launcher.py` prepares the packaged runtime and calls
  `suite_gui.spps_tk_gui`.
- `suite_gui.spps_tk_gui` re-exports the canonical API from
  `suite_gui.release`.
- `suite_gui.release` imports and validates the statically defined
  `suite_gui.controller.SPPSGui` before launch.

Existing imports through `suite_gui.classic_2094_tk_gui` remain supported.

## Direct controller migration

`suite_gui.controller.SPPSGui` is now the public runtime identity. Its
operator-facing routes are regular class methods; `suite_gui.release` no
longer runs the release-composition registry.

The active UI construction path is also explicit:

```text
controller.SPPSGui._build
  -> ui_build.build_base_interface
  -> ui_build.apply_plan_workspace
  -> ui_build.apply_operator_workspace
  -> ui_build.apply_final_release_ui
  -> ui_build.apply_custom_database_ui
  -> ui_build.bind_direct_workspace_actions
  -> ui_system.apply_theme / fit_window / bind_shortcuts
  -> v3_menu.install_menu
```

This replaces the active nested `_build` closures with one readable,
testable sequence. The retained base widget builder is called exactly once.

The active synthesis commands are explicit as well:

```text
Generate / pm_generate_selected / pm_calculate_all
  -> synthesis_workflow.generate
  -> synchronise unified unit defaults
  -> plan_workflow.generate

Apply Change / pm_apply_change / apply_plan_mw_density
  -> synthesis_workflow.apply_change
  -> synchronise unified unit defaults
  -> plan_workflow.apply_change

Live correction / doubling
  -> execution_workflow
  -> visible Plan value
  -> controller.apply_change
  -> synthesis_execution append-only event ledger

Step status / actual material / revert
  -> execution_workflow
  -> synthesis_execution append-only event ledger
  -> persistence_workflow autosave

Reviewed outcome / dataset / model
  -> ml_workflow
  -> ml_dataset feature projection + review revisions
  -> immutable dataset CSV + fingerprint manifest
  -> spps_planner.ml leakage-safe preprocessing, training and prediction

Project / Work Item / Run / HPLC
  -> data_workflow controller orchestration
  -> data_system hierarchy, HPLC CRUD and append-only changes
  -> persistence_workflow atomic JSON + backup/recovery/conflict guard
  -> data_workbook multi-sheet XLSX + Column_Map round-trip

Synthesis risk review
  -> risk_workflow controller orchestration
  -> risk_engine deterministic explained findings
  -> optional reviewed-data classifier probability + dataset fingerprint
  -> risk_assessment version and acknowledgement ledger
```

The visible Generate and Apply Change buttons bind to those controller methods,
so the UI and programmatic routes cannot drift into different calculation
pipelines.

Project and data routes follow the same rule:

```text
Project item actions
  -> project_workflow
  -> plan_workflow / project_manager_workflow state helpers

Save Project / Load Project / autosave / restore
  -> persistence_workflow
  -> state_persistence atomic JSON

Batch calculate / refresh / export
  -> batch_workflow
  -> accepted connected Batch calculator
```

The session/project envelope remains backward compatible and now has one
explicit owner for Project items, selected index, Setup defaults, editable
Batch rows, and Custom DB data.

The retained Classic widgets now live in `suite_gui.classic_base` as ordinary
class definitions and static method bindings. `suite_gui.controller.SPPSGui`
inherits that base and declares every contracted public route directly.

There is no runtime release composition, numbered compatibility-module import,
or `legacy_controller` superclass. UI construction is an explicit sequence in
`suite_gui.ui_build`; calculations and state changes enter through semantic
workflow modules. Runtime controller bindings and nested `_build` wrappers are
forbidden by the release audit.

## Extracted responsibilities

- `plan_input_factory.py`: Project/Batch calculation inputs
- `resin_profiles.py`: resin and loading rules
- `material_presentation.py`: user-facing material rows and ordering
- `peptide_item_state.py`: editor/output snapshots
- `peptide_item_collection.py`: add, duplicate, delete, and reorder operations
- `state_persistence.py`: atomic JSON persistence
- `session_state.py`: desktop autosave lifecycle
- `project_workflow.py`: direct Project Manager item routes
- `persistence_workflow.py`: direct project/session save and restore
- `batch_workflow.py`: direct Batch calculate, refresh, and export routes
- `custom_db_workflow.py`: custom material CRUD, lookup, selector refresh, and UI
- `ml_workflow.py`: reviewed dataset versioning, legacy observed-run compatibility, model training, prediction, and anomaly detection
- `ml_dataset.py`: execution-history feature engineering, outcome review revisions, inclusion/exclusion and dataset fingerprinting
- `data_system.py`: Project/Work Item/Run compatibility hierarchy, Run snapshots, HPLC records and change history
- `data_workflow.py`: GUI-facing Run/HPLC/search/recent-file/workbook operations
- `data_workbook.py`: multi-sheet XLSX export/import, automatic aliases and explicit Column_Map handling
- `risk_engine.py`: deterministic sequence/Plan/execution risk triage without automatic Plan mutation
- `risk_assessment.py`: content-addressed assessment revisions and acknowledgement audit events
- `risk_workflow.py`: GUI, valid real-model signal and risk-report orchestration
- `ui_system.py`: shared palette, display density, responsive geometry and keyboard bindings
- `export_workflow.py`: direct accepted visible-state export route
- `modules/plan_workflow.py`: Generate and Apply Change plan workflow
- `position_rules.py`: blank/single/range C-terminal eq and repeat rules
- `classic_base.py`: retained Classic UI implementation without runtime patching
- `synthesis_workflow.py`: direct Plan route and unified-default sequencing
- `execution_workflow.py`: live Plan correction, doubling, status, actual material, and compensating revert orchestration
- `synthesis_execution.py`: UI-independent append-only execution ledger and ML-ready row projection
- `modules/project_manager_workflow.py`: Project Manager operator workflow
- `release_contract.py`: active runtime route validation
- `tools/verify_windows_release.py`: V4 identity, PyInstaller, Installer and optional PE artifact contract

## Behaviour compatibility

The V4 release preserves the validated planner behavior, resin choices, project/session
JSON keys, visible Plan editing behaviour, Apply Change synchronization,
materials/checklist/total outputs, Batch calculation, CSV/XLSX export, Custom
DB, and Windows build entry points.

Calculation contracts are covered by fixed engine snapshots and focused tests
for 2-CTC loading, C-terminal behaviour, doubling, repeat cycles, material
ordering, resin volume, preset buttons, project item state, and persistence.

## Verification

Run the complete release verification from the repository root:

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py --passes 5
```

Audit only the routes that are active in the final controller:

```bat
python tools\audit_monkey_patches.py --active-release
```

The historical source-binding count is intentionally separate from the active
runtime audit.
