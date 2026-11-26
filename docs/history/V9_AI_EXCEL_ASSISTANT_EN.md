# SPPS Planner V9.0.0 — AI + Excel/CSV Assistant

This is an **offline/local machine-learning assistant**, not an embedded ChatGPT/LLM or web service. It does not change the established chemistry engine, original Generate/Apply Change workflow, or laboratory SOPs.

## Workflow

1. Open **Project Manager → Auto Plan (Optional) → AI · Import Excel / CSV...** (or **ML Lab → Import Excel / CSV (AI)** where available).
2. Select an `.xlsx`, `.csv`, `.tsv`, or `.txt` file, then choose an Excel worksheet if necessary. Old `.xls` must be converted to `.xlsx`.
3. Automatic header detection checks the first nine rows and recognizes supported English/Korean aliases. Review the mappings with dropdowns; override any incorrect field. **Check & clean** only previews the normalized data.
4. For Excel-native percentage-formatted cells (stored as 0.75 but displayed as 75%), automatic conversion is enabled; uncheck the explicit conversion option when source conventions differ.
5. Confirm that outcomes are **measured experiments**, and explicitly select **Save reviewed data**. One reviewed dataset per profile is replaced (never silently appended). Existing `actual_runs.csv` and chemistry records remain unchanged.
6. Select the **ML target** (measured yield % or purity %) and **Train local AI**. Training is only permitted with at least 24 measured outcomes, six distinct peptide sequences, enough Scale/Loading coverage and a better sequence-group holdout MAE than a naive median predictor. If not satisfied, no new model is deployed.
7. For an active peptide, **Compare current peptide** lists up to three similar prior runs. An exploratory yield estimate may be shown *only* if the data and model pass these checks; out-of-distribution sequences, resin, coupling, scale or loading block predictions. **Attach evidence** adds read-only advisory context to the Auto Plan and exported draft JSON.

## Supported fields

The normalization supports `sequence`, `actual_yield_percent`, `actual_purity_percent`, `scale_mmol`, `loading_mmol_g`, `resin`, `chemistry`, and `run_id`. Common English/Korean headings map automatically, with manual override.

**IMPORTANT:** Yield % is a percent outcome, not isolated mass in mg, theoretical mass, or an arbitrary 0-1 fraction unless explicitly represented with Excel percent formatting. Data must be reviewed before training; the assistant cannot determine experimentally measured vs hypothetical values by itself.

## Safety and architecture

- Uses `pandas` for import and a local `scikit-learn RandomForestRegressor` trained only on selected, reviewed user data.
- Uses a held-out split **grouped by peptide sequence** to reduce repeated-peptide leakage; the evaluation is still preliminary, not prospectively validated.
- Predictors use input-only data: peptide length and Cys/Asp/Pro/Gly counts, synthesis scale/loading, resin and coupling system. No observed outcomes or post-experiment fields enter the predictors.
- Does not modify the Plan, reagents, coupling times, cleavage cocktails, protection states or approval flags on its own.
- Stores reviewed data and app-created models only in the Public/Private **separate local user profiles**; no automatic network upload. Replacing the dataset invalidates incompatible model metadata. Never load externally sourced `.joblib` artifacts.
- The assistant **cannot** claim validated synthesis yield, optimal conditions, calibrated uncertainty, or an approved protocol.
- Limits: `.xlsx` / CSV/TSV, file size ≤12 MB, ≤20,000 rows and ≤70 columns; formula results rely on cached Excel cell values; encrypted or complex spreadsheets may need manual cleanup.

## Testing

`PYTHONPATH=.:apps/spps_planner_app python -m pytest -q tests/test_v9_ai_excel_import.py`

Actual Windows GUI/EXE/Installer execution is not verified by Linux/headless tests. **Application version remains V9.0.0.**


**2026-11-08 refinement:** Grouped holdout is now repeated three times; equivalent sequence spellings are grouped together. Exploratory yield predictions are withheld for protected/cyclic product paths when the imported outcomes lack topology labels. Older local AI models require retraining. See [Korean engineering notes](V9_AI_REFACTOR_HARDENING_KO.md).
