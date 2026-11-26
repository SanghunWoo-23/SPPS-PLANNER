# SPPS Planner V9.0.0 — AI / ML Evolution (Development Build)

This update improves the **local Excel AI assistant**, without replacing the established SPPS chemical calculation engine. It does **not** connect to a hosted LLM or automatically alter an approved synthesis plan.

- **Non-executable model persistence:** the Excel-specific RandomForest is exported to bounded, validated JSON tree data with SHA-256 checking. It does not invoke `joblib.load()` for this assistant. Retrain previously saved `.joblib` Excel models. Other historical ML modules still use their existing persistence and are outside this change.
- **Guided Excel ingestion:** create a blank workbook (`Runs` + `GUIDE`) directly from the assistant; detect Korean/English columns; import multiple files after per-file review; append or replace intentionally; audit duplicates and Run-ID collisions.
- **Training-readiness guidance:** report labeled rows, unique sequence groups, positive Scale/Loading coverage, unparseable residues, and blocking quality issues before initiating a model.
- **Product-path awareness:** `Product path` and `Reaction step` are importable fields. Cyclic, protected and branched observations remain accessible as records but do not silently train the current legacy linear/deprotected outcome model. Annotated chemistry sequences also withhold unqualified linear ML predictions.
- **More transparent evaluation:** three sequence-group holdouts versus a median baseline; descriptive absolute-residual quantiles and held-out permutation importance. The displayed error band is **not** a calibrated prediction interval, confidence interval or guarantee.
- **Stricter domain-of-applicability checks:** previously unseen residue identities and unsupported conditions withhold numeric predictions.

User workflow: `Project Manager → Auto Plan (Optional) → AI · Import Excel / CSV... → review → Audit data quality → Save → Train → Compare → Attach evidence`. AI results are read-only review evidence: they do not change reagent, cleavage or cyclization calculations.

Support status: source regression and Linux/Xvfb GUI checks are distinct from Windows-native EXE/Installer and wet-lab verification. The latter remain **not verified**. Public source must exclude all private experiment records and locally trained models.

Official references: [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html), [feature importance](https://scikit-learn.org/stable/modules/permutation_importance.html), [model persistence](https://scikit-learn.org/stable/model_persistence.html). Conformal prediction concepts, which are **not** claimed for the heuristic interval, are documented by [MAPIE](https://mapie.readthedocs.io/en/latest/).
