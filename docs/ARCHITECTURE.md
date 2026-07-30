# SPPS Planner V2.0.0 Architecture

## Stable entry points

- `main_launcher.py` prepares the packaged runtime and calls
  `suite_gui.spps_tk_gui`.
- `suite_gui.spps_tk_gui` re-exports the canonical API from
  `suite_gui.release`.
- `suite_gui.release` validates the fully composed controller before launch.

Existing imports through `suite_gui.classic_2094_tk_gui` remain supported.

## Controller composition

`suite_gui.release_composition` owns the accepted layer order. New code uses
semantic workflow boundaries rather than importing numbered compatibility
modules directly:

1. `classic_workflow`
2. `workbench_workflow`
3. `planner_workflow`
4. `final_release_workflow`

The active build path contains only the composed planner and final-release
layers. Historical patches remain in `legacy_controller.py` solely as the
accepted UI/behaviour baseline and compatibility surface.

## Extracted responsibilities

- `plan_input_factory.py`: Project/Batch calculation inputs
- `resin_profiles.py`: resin and loading rules
- `material_presentation.py`: user-facing material rows and ordering
- `peptide_item_state.py`: editor/output snapshots
- `peptide_item_collection.py`: add, duplicate, delete, and reorder operations
- `state_persistence.py`: atomic JSON persistence
- `session_state.py`: desktop autosave lifecycle
- `modules/plan_workflow.py`: Generate and Apply Change plan workflow
- `modules/project_manager_workflow.py`: Project Manager operator workflow
- `release_contract.py`: active runtime route validation

## Behaviour compatibility

The refactor preserves the V2.0.0 window title, resin choices, project/session
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
