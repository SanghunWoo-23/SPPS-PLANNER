# SPPS Planner v6.0.0 — Release Notes

**Release:** v6.0.0  
**Public source baseline:** validated V6 R19  
**Platform focus:** Windows 10/11, Python 3.11–3.12

SPPS Planner v6.0.0 is the first finalized V6 public source release of the Windows-first SPPS planning and evidence-driven decision-support workflow.

## Highlights

### Evidence-aware Loading Advisor

- Uses exact **same resin + same normalized loaded-AA identity** as the direct experimental evidence boundary.
- Preserves D-form/L-form separation instead of pooling stereochemically different histories.
- Recognizes data-supported special/non-natural identities such as `Cit`, `Hyp`, and `Dab` without treating recognition itself as experimental support.
- Supports explicit D-form normalization such as `D-Leu`, `D-Phe`, and protected forms including `D-His(Trt)`.
- Prioritizes repeated observed conditions when the requested target lies inside the measured range.
- Uses bounded interpolation only within observed evidence coverage.
- Keeps `CHEMISTRY DEFAULT` visibly separate from measured prediction.
- Shows evidence count, observed range, median, date coverage, repeatability, capping/provenance notes, and nearby real conditions where available.

### Stable planning workflow

- Preserves the validated Generate / editable Plan / Apply Change model.
- Keeps the current visible Plan as the source for downstream recalculation.
- Maintains connected Materials, Checklist, Total Materials, Cleavage, Batch, Project/Work Item, and Export workflows.

### Cleavage decision support

- Preserves the established automatic Cys rule: `100 TFA eq × Cys count`.
- Prevents double-adding the peptide-length baseline when the Cys rule is active.
- Keeps cleavage cocktail identity separate from total equivalent amount.
- Keeps optional NH4I reduction in a separate post-cleavage rescue workflow and does not auto-insert it based only on Met presence.

### Experimental traceability

- Links measured results/issues to planner conditions and active runs where available.
- Preserves raw experimental text while maintaining normalized lookup keys for retrieval.
- Keeps ambiguous/provisional evidence reviewable rather than silently treating it as strong evidence.
- Model rebuild/promotion/rollback remains explicit; new records do not trigger hidden retraining.

### Public/private data boundary

The GitHub package is sanitized and intentionally contains no private laboratory history, source-image manifest, local SQLite database, or private model artifact. The public planner remains functional with an empty experimental store and builds evidence only from data the user later records/imports locally.

## R19 Batch sequence-prep correction

- Batch Manager keeps its existing name and remains synchronized with Project Manager sequences.
- The compact Batch calculator now uses **sequence + copies from Project Manager** and **Solution prep defaults for preparation quantities**.
- `Scale mmol` is visible in Solution prep defaults and is the scale used for Batch preparation calculations.
- Project-specific chemistry, reagent equivalents, resin/loading settings, and project scale are intentionally ignored by this compact preparation calculator.
- AA stock preparation follows the Batch AA concentration/equivalent defaults.
- HBTU/NMP preparation follows the Batch HBTU concentration/equivalent defaults.
- Practical volumes apply the configured round-up increment and extra reserve.
- DIC/HOBt rows are no longer produced merely because a Project Manager item was synthesized with DIC/HOBt.
- Sequence-defined modifiers remain detectable from the sequence itself.
- Empty/default Project placeholders remain excluded.
- No chemistry-engine or recommendation-decision rule changed.

## R16 identity update

The final V6 source line adds loaded-AA identity handling for D-form and data-supported special/non-natural inputs without modifying the locked chemistry engine.

Examples:

```text
Cit          -> Fmoc-Cit-OH
Hyp          -> Fmoc-Hyp(tBu)-OH when that exact historical identity is present
Dab          -> Fmoc-Dab(Boc)-OH
D-Leu / dL   -> Fmoc-D-Leu-OH
D-Phe / dF   -> Fmoc-D-Phe-OH
D-His(Trt)   -> Fmoc-D-His(Trt)-OH
```

Gly remains achiral and is not converted into a fictitious D-form identity.

## Validation

Validation was performed from fresh-unzipped final release archives.

- Public headless pytest: **370 passed / 28 skipped**
- Public Real-Tk/Xvfb pytest: **395 passed / 3 skipped**
- R19 sequence-driven Batch prep Real-Tk regression: **PASS**
- `tools/verify_v6_integrity.py`: **PASS**
- `tools/verify_windows_release.py`: **PASS**
- Public bundled experimental seed: `README.md` only
- Public SQLite/DB files: **0**
- ZIP integrity: **PASS** (`testzip = None`)
- Shared release-source parity check passed across the corresponding Public/Private builds while preserving the data boundary
- Chemistry-engine golden behavior remained unchanged through the final identity/recommendation refinements

## Installation

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

For development verification:

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

## Upgrade notes

- Existing local experimental databases are not replaced by the public package.
- The loaded-AA lookup-key migration normalizes legacy shorthand for exact lookup while preserving original raw historical text.
- D/L and protected-building-block boundaries are intentionally stricter than a simple amino-acid-letter lookup.
- Users should review Recommendation provenance after upgrading rather than assuming a recognized alias has experimental support.

## Scientific-use note

SPPS Planner is research planning and decision-support software. It does not replace approved SOPs, SDS/institutional safety requirements, qualified analytical methods, trained operator review, or experimental validation.

## Data/privacy note

Do not publish runtime DBs, imported laboratory files, models, logs, or exports without reviewing them for confidential sequences, sample names, source paths, notes, and other private experimental metadata. See `PUBLIC_DATA_POLICY.md`.

## License and citation

This release uses the custom **SPPS Planner Public Academic Citation License** for academic, educational, research, portfolio-review, and non-commercial use. It is not an OSI-approved open-source license.

Suggested citation:

> Woo, S. SPPS Planner: Solid-Phase Peptide Synthesis Planning and Evidence-Driven Decision Support. Version 6.0.0. GitHub repository, 2026. https://github.com/SanghunWoo-23/SPPS-PLANNER
