# SPPS Planner V5.0.0 User Manual

SPPS Planner turns a peptide sequence plus resin, scale, loading and chemistry
settings into an editable synthesis Plan connected to Materials, Totals,
Checklist, Cleavage, execution records, HPLC, reviewed outcomes and risk review.
It supports planning and traceability; it does not replace an approved SOP,
SDS, instrument qualification or operator approval.

## Core workflow

1. Add or select a Work Item and enter project, peptide, sequence, scale, copies,
   resin, loading and chemistry.
2. Keep using the retained Classic setup controls for resin, amino-acid/unit,
   reagent, base and solvent defaults.
3. Select Generate (`Ctrl+G`) to create Plan, Materials, Totals and Checklist together from the inputs.
4. Double-click Plan cells to edit conditions or Repeat.
5. Select Apply Change (`Ctrl+Enter`) to recalculate from the visible Plan.

Generate recreates Plan, Materials, Totals and Checklist in one action without
changing Cleavage. Apply Change preserves the edited visible Plan and updates
Materials, Totals, Checklist, Cleavage and Export. Chemistry presets do not
silently generate a Plan. Empty sequences stay empty.

## Work Item workspace

Double-click a Work List item or press Enter to open its independent window.
The Plan is the source of truth. Run / Corrections stores append-only status,
actual material, Plan correction and doubling events with reasons and operator
notes. Revert appends a compensating event instead of deleting history.

Outcome / ML stores reviewed yield, crude purity, failure and doubling outcomes.
Training requires at least five included reviewed values for the target;
classification also requires two observed classes. Immutable dataset versions,
fingerprints and model metadata prevent untraceable training and target columns
are excluded from features.

Risk Review reports explained aspartimide, aggregation, difficult-coupling,
Cys protection/oxidation, Met/Trp oxidation, early-Pro, planned-repeat and
failed/held execution patterns. Its rule score is a triage score, not failure
probability. ML probabilities appear only when a valid real reviewed-data model
and metadata exist. Findings never modify the Plan automatically.

Data / HPLC manages multiple independent Runs and HPLC records. Data and method
files are linked with path, existence, size, modification time and SHA-256.
Deletion is soft and auditable.

## Data safety and interchange

Project JSON writes are atomic, retain a last-good `.bak`, reject external-edit
hash conflicts and track up to 12 recent projects. The multi-sheet Data Workbook
round-trips the Project → Work Item → Run hierarchy, plans, execution, ML, HPLC,
materials, checklists, cleavage, change history and risk-review records. The
Column Map supports instrument/user column aliases.

## Keyboard shortcuts

| Shortcut | Action |
| --- | --- |
| Ctrl+S / Ctrl+Shift+S | Save / Save As |
| Ctrl+O | Load Project |
| Ctrl+N / Ctrl+D | Add / duplicate Work Item |
| Ctrl+G / Ctrl+Enter | Generate / Apply Change |
| Ctrl+E | Export current work |
| Ctrl+- / Ctrl+0 / Ctrl+= | Compact / Standard / Comfortable density |
| Work Item F5 / Esc | Refresh / save and close |

Use View → Display Density for screen-space control. Windows are automatically
fitted within the available display at 1024×680 or above. Before experimental
use, verify the sequence, resin/loading, scale units, Repeat, totals, checklist,
cleavage composition, risk findings and analytical links.
