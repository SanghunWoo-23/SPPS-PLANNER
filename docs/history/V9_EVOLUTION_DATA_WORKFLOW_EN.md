# SPPS Planner V9.0.0 — Evolution: Reviewed Multi-file AI Data Workflow

**Source development update, November 9, 2026.** The application version remains **V9.0.0**. The SPPS chemistry engine and its existing calculations are unchanged.

## New functionality

- **Multi-file Excel/CSV:** select several `.xlsx`, `.csv`, `.tsv`, or `.txt` files. Verify the sheet, mapped columns and percentage convention independently for **each** file. Use **Check & clean → approve → Stage reviewed file / Next** until all files are staged.
- **Append or Replace:** append reviewed observations to the existing local dataset, or explicitly replace it. Observations are never silently averaged or removed.
- **Data quality audit:** review invalid sequences, exact duplicate rows, repeated/conflicting experiment IDs, labeled yield/purity and missing inputs. Ambiguous IDs, exact duplicate rows or unparseable ML sequences block supervised training. A reagent LOT is not automatically treated as a unique experimental Run ID.
- **Last-good rollback:** validated previous data are backed up to `ai_excel_reviewed_v9.json.bak` before a new save. **Restore previous dataset** prompts the operator and checks backup integrity.
- **Position-sensitive evidence search:** sequence similarity now compares verified residue identities in order with edit distance, plus resin/coupling matches. A cheap composition filter screens candidates before expensive comparisons; results are **approximate** and are not validated yield analogs.
- **Scrollable review with fixed controls:** the workbook preview and mapping can scroll while Save, Train, Audit and Restore remain reachable on short windows. No shared `ttk.Treeview` style is changed.
- **Safer recommendation-window lifecycle:** the scrollable canvas list is initialized even if a plugin or test replaces the view builder.

## Operator workflow

Open **Project Manager → Auto Plan (Optional) → AI · Import Excel / CSV**. Choose files, inspect every worksheet/mapping, approve each staged file, audit data quality, select Append/Replace, then save. Training is an independent opt-in action and never updates the active synthesis plan or approved SOP.

## Scientific and security boundaries

Prediction for cyclic/protected products is withheld when imported outcome data lack explicit product pathway labels. The existing local Random Forest remains exploratory with sequence-group holdouts and out-of-distribution checks. ML outputs do not prove chemical yield, purity or optimal conditions.

`joblib` is pickle-based; a SHA-256 sidecar does not make untrusted model files safe. Only locally created models should be used. Windows native EXE/Installer acceptance and laboratory validation remain **not verified**.

Implementation: `suite_gui/ai_excel_core_v9.py`, `suite_gui/ai_excel_dialog_v9.py`, `suite_gui/modules/experimental_data_panel.py`, `tests/test_v9_evolution_multifile_quality.py`.
