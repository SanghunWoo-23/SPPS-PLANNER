# SPPS Planner V2.0.0 — Detailed User Manual

**Language:** English  
**Korean manual:** [USER_MANUAL_KO.md](USER_MANUAL_KO.md)  
**Project overview:** [README.md](../README.md)

---

## 1. About this manual

This manual explains how to operate SPPS Planner V2.0.0 from initial setup to
final material export. It is written for users who understand the basic
principles of solid-phase peptide synthesis but may not be familiar with this
program.

SPPS Planner is a planning and calculation tool. It does not replace laboratory
SOPs, risk assessments, reagent specifications, or review by a qualified
chemist. Always verify the sequence, scale, resin loading, equivalents,
concentrations, solvent volumes, and cleavage conditions before laboratory use.

## 2. What SPPS Planner does

The program connects the following work into one workflow:

1. Enter a peptide sequence and project information.
2. Select resin, scale, loading, and synthesis chemistry.
3. Generate an editable synthesis Plan.
4. Review or directly edit individual Plan rows.
5. Apply the edited Plan to recalculate connected results.
6. Review Materials, Checklist, Total, Cleavage, and Project Summary.
7. Combine multiple peptides in Batch Manager.
8. Save or export records for later use.

The central idea is simple:

```text
Input conditions → Generate → Edit Plan → Apply Change → Review → Export
```

## 3. Important terms

### Project

A Project is the complete working session. It may contain one or more peptide
items.

### Peptide item

Each item in Project Manager has its own sequence, synthesis settings, Plan,
and calculated results. Switching items should restore that item's data.

### Generate

`Generate` creates or recreates the Plan from the current sequence and setup.
Use it when the sequence or basic synthesis conditions have changed.

Generating again may replace manual edits in the current Plan. If you only
changed a Plan row, use `Apply Change` instead.

### Apply Change

`Apply Change` uses the currently visible, edited Plan as the calculation
source. It updates Materials, Checklist, Total, Batch, and related outputs
without rebuilding the Plan from the original sequence.

### Autosave and Save Project

Autosave preserves the current session on the local computer. `Save Project`
creates an intentional project record or export. Autosave is useful for
recovery, but it should not be treated as the only project backup.

## 4. Installation and first launch

### Installed Windows version

1. Download `SPPS_Planner_Setup_V2.0.0.exe` from the GitHub Release.
2. Run the installer.
3. Follow the installation prompts.
4. Start SPPS Planner from the installed shortcut.

If Windows SmartScreen appears, verify that the file came from the official
project Release before continuing.

### Running from source

Requirements:

- Windows 10 or Windows 11
- 64-bit Python 3.11 or 3.12

Open Command Prompt in the project directory and run:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main_launcher.py
```

### First-launch check

After the main window opens, confirm that:

- Project Manager is visible.
- The sequence input area is empty or contains only restored work.
- Resin, scale, loading, and chemistry controls are available.
- Plan and result tabs can be opened.

If old work appears, the autosaved session was restored. See section 18 to
reset the session.

## 5. Recommended operating order

For reliable results, use this order:

1. Create or select a peptide item.
2. Enter Project, Peptide, and LOT information.
3. Enter and verify the sequence.
4. Select resin and enter loading.
5. Enter synthesis scale.
6. Select chemistry and detailed setup.
7. Configure doubling, special residues, and cleavage conditions.
8. Click `Generate`.
9. Review every Plan row.
10. Edit rows if required.
11. Click `Apply Change`.
12. Review every result tab.
13. Save or export the record.

## 6. Project Manager

Project Manager is used to manage multiple peptide items in one session.

### Add an item

1. Open Project Manager.
2. Choose the add/new-item function.
3. Enter a clear peptide name.
4. Select the new item before entering its sequence.

Use unique names when possible. Names such as `Peptide-01`, `Peptide-02`, or a
project code are easier to track than repeated generic names.

### Duplicate an item

Duplicate is useful when two peptides use similar conditions.

1. Select the original item.
2. Choose Duplicate.
3. Rename the duplicated item.
4. Change the sequence or conditions.
5. Click `Generate` after changing the inputs.

Always confirm that the duplicate does not retain an incorrect LOT number,
sequence, scale, or manually edited Plan.

### Delete an item

1. Select the intended item.
2. Confirm its name and sequence.
3. Choose Delete.
4. Confirm the deletion if prompted.

Deletion may remove the item's unsaved information. Save or export important
work first.

### Reorder items

Use the move-up or move-down controls to change the project order. This is
useful when the Batch or exported record should follow a synthesis order.

### Switching items

Before switching:

1. Finish the current field edit.
2. Apply changes if the Plan was edited.
3. Save if the work is important.

After switching, verify the item name and sequence before continuing.

## 7. Project and peptide information

Enter identifiers consistently because they may appear in saved and exported
records.

- **Project:** Overall experiment, client, or study name.
- **Peptide name:** Unique name for the current peptide.
- **LOT:** Material or production lot identifier.
- **Notes:** Optional information that helps another operator understand the
  plan.

Avoid placing confidential or regulated information in filenames unless your
organization's policy permits it.

## 8. Sequence entry

### Before entering a sequence

Decide whether terminal modifications and special components will be expressed
in the sequence or configured through the available setup controls. Use one
consistent method and review the generated Plan.

### Entry procedure

1. Select the correct peptide item.
2. Click the sequence field.
3. Enter or paste the sequence.
4. Check spelling, separators, brackets, and residue notation.
5. Confirm N-terminus and C-terminus settings.
6. Confirm D-amino acids, non-natural residues, chemicals, modifiers, tags,
   labels, and linkers.
7. Continue only after the sequence is correct.

An unrecognized name may cause an error or an incomplete Plan. If a required
material is missing, add it through Custom DB and generate again.

### Empty sequence behavior

An empty sequence is kept empty. The program does not intentionally insert a
fake example peptide or placeholder Plan.

## 9. Resin, scale, and loading

### Resin selection

Select the resin that matches the intended C-terminal chemistry and actual
laboratory material. Available profiles may include Rink Amide families,
2-CTC, preloaded `CTC(합성기)`, Wang, HMPB, Sieber Amide, PAL, Tentagel, and
Manual profiles.

Do not select resin only by a similar name. Check:

- Functional group and intended C-terminus
- Actual supplier specification
- Resin loading
- Preloaded or unloaded state
- Swelling and cleavage requirements

### Loading

Enter the resin loading using the unit displayed by the program. Copy the
value from the actual resin certificate or approved internal record.

A loading-entry error directly affects resin amount and connected reagent
calculations.

### Scale

Enter the intended synthesis scale in the unit shown by the UI. Confirm that
the value is the synthesis target, not the desired isolated product mass.

### 2-CTC warning

Direct loading on `2-CTC` uses loading-specific chemistry. Review loading amino
acid and DIEA conditions carefully. Applying changes should not convert these
rows into ordinary DIC/HOBt coupling rows.

The legacy saved value `CTC(합성용)` is migrated to `CTC(합성기)`.

## 10. Chemistry and detailed setup

Open:

```text
Project Manager → Show setup
```

The exact controls depend on the selected workflow. Review all visible values,
including:

- Coupling reagent
- Catalyst or additive
- Base
- Solvent
- Amino-acid equivalents
- Coupling-reagent equivalents
- Repeat count
- Deprotection conditions
- Wash conditions
- Doubling positions
- Cleavage cocktail

Preset buttons change chemistry conditions. They do not necessarily generate
the Plan. After selecting a preset, review the values and then click
`Generate` when a new Plan is required.

## 11. Doubling and repeat reactions

Use position-based doubling when selected residues require repeated coupling.

1. Open the doubling controls.
2. Select or enter the intended residue positions.
3. Confirm whether positions are counted from the displayed sequence direction.
4. Generate the Plan.
5. Confirm that the intended coupling rows show the correct repeat value.
6. Check Materials and Checklist after applying changes.

A repeat value is not limited to exactly two. If a row uses a value greater
than 2, verify that the Plan, material totals, and Checklist all reflect it.

## 12. Generating the synthesis Plan

Before clicking `Generate`, verify:

- Correct peptide item
- Correct sequence
- Correct termini and modifications
- Correct resin
- Correct loading
- Correct scale
- Correct chemistry
- Correct doubling positions
- Correct cleavage setup

Then:

1. Click `Generate`.
2. Wait for the Plan to appear.
3. Read from the first row to the last row.
4. Confirm loading, coupling, deprotection, wash, terminal modification, and
   final operations.
5. Do not proceed only because the program completed without an error.

## 13. Reading and editing the Plan

The Plan is an editable process table. Depending on the row type, columns may
include operation, material, unit, molecular weight, density, equivalents,
reagent, solvent, and repeat.

### Editing a row

1. Select the exact cell.
2. Enter the corrected value.
3. Confirm the unit.
4. Confirm MW and density where relevant.
5. Confirm equivalents and repeat count.
6. Check the associated reagent and solvent.
7. Finish the cell edit.
8. Click `Apply Change`.

### Replacing a material

When replacing a material, review every connected property. Changing only the
displayed name may be insufficient if MW, density, unit, or equivalents should
also change.

For example, replacing an `Ac2O` row with an `Ac-Glu(OtBu)-OH` row changes the
chemical meaning. After replacement, verify that the material calculation,
Checklist, Total, Batch, and Export results all match the new row.

### Deleting a row

1. Select the intended row.
2. Choose `Delete selected row`.
3. Confirm that only the intended row was removed.
4. Click `Apply Change`.
5. Review all connected results.

### Generate versus Apply Change

Use this rule:

| Situation | Button |
| --- | --- |
| Sequence changed | `Generate` |
| Resin, scale, or base chemistry changed | `Generate` |
| Plan cell was manually edited | `Apply Change` |
| A Plan row was replaced or deleted | `Apply Change` |
| You want to discard edits and rebuild from inputs | `Generate` |

## 14. Result tabs

### Materials

Materials shows calculated requirements for the selected peptide. Check:

- Resin
- Amino acids and modifications
- Coupling reagents
- Catalyst/additive
- Base
- Solvents
- Cleavage components
- Unit and quantity

### Selected Total Materials

This view summarizes selected calculated materials. Confirm that item selection
and quantities match the intended scope.

### Checklist

Checklist converts the Plan into an operator-oriented sequence. Compare it
against the Plan, especially after manual edits, deletions, or repeat changes.

### Cleavage Cocktail

Review the selected preset or custom cocktail, total amount, component ratios,
and mass/volume display. Independently confirm chemical compatibility and
laboratory safety.

### Project Summary

Use Project Summary as a final overview. It should agree with the selected
peptide, scale, resin, Plan, and material results.

## 15. Batch Manager

Batch Manager combines multiple peptide items.

1. Finish and apply changes for every peptide.
2. Open Batch Manager.
3. Select the intended peptide items.
4. Confirm each item name, scale, and status.
5. Recalculate the batch.
6. Review peptide-level results.
7. Review batch-level totals.
8. Export only after checking for duplicates or missing items.

If a peptide Plan changes later, return to Batch Manager and recalculate.

## 16. Custom DB

Open:

```text
Project Manager → Show setup → Custom DB
```

Supported categories may include:

- AA/Chemical
- Coupling reagent
- Catalyst/additive
- Base
- Solvent
- Cleavage cocktail component
- Resin
- Other material

### Adding a material

1. Select the correct category.
2. Enter a unique, consistent name.
3. Enter MW.
4. Enter density when volume calculation requires it.
5. Add useful notes.
6. Save the record.
7. Confirm it appears in the expected selection control.

### Updating or deleting a material

Before updating, check whether existing projects depend on the record. Before
deleting, save important project data. A changed database value may change
future calculations.

## 17. Saving and exporting

### Save Project

Use `Save Project` at meaningful checkpoints:

- After initial setup
- After generating and reviewing the Plan
- After manual Plan changes
- Before batch calculation
- Before closing the program

### Export

Available output can include CSV, XLSX, or JSON depending on the workflow.

Before export:

1. Apply all Plan changes.
2. Confirm the selected peptide or batch.
3. Check Project, Peptide, and LOT fields.
4. Review totals and units.
5. Choose a clear filename and location.
6. Open the exported file and spot-check its contents.

## 18. Autosave and session reset

The normal Windows autosave location is:

```text
%LOCALAPPDATA%\SPPS Planner\spps_planner_session_v1.json
```

To reset the restored session:

1. Save or export anything important.
2. Close SPPS Planner.
3. Open the path above in File Explorer.
4. Back up the file if recovery may be needed.
5. Remove the session file.
6. Restart SPPS Planner.

Do not edit the autosave JSON manually unless you understand its structure and
have a backup.

## 19. Final pre-run checklist

Before using a plan in the laboratory, verify:

- [ ] Correct project and peptide item
- [ ] Correct sequence and residue order
- [ ] Correct N- and C-terminal configuration
- [ ] Correct D/non-natural residues, tags, labels, and linkers
- [ ] Correct resin and preloaded/unloaded state
- [ ] Correct resin loading and synthesis scale
- [ ] Correct coupling chemistry and equivalents
- [ ] Correct deprotection and wash conditions
- [ ] Correct doubling positions and repeat values
- [ ] Correct terminal modification
- [ ] Correct cleavage cocktail
- [ ] Plan reviewed row by row
- [ ] Manual changes applied with `Apply Change`
- [ ] Materials and Checklist agree with the Plan
- [ ] Total and Batch scope are correct
- [ ] Export opened and checked
- [ ] Final review completed under the applicable laboratory SOP

## 20. Troubleshooting

### The Plan does not change

- Confirm that the intended peptide item is selected.
- If an input condition changed, click `Generate`.
- If a Plan cell changed, finish editing the cell and click `Apply Change`.

### Manual edits disappeared

`Generate` rebuilds the Plan from the input settings. Re-enter the edits if
needed, then use `Apply Change`.

### A material is missing

Check spelling and notation. Add a valid record through Custom DB, then generate
again.

### Totals look outdated

Finish the active cell edit, click `Apply Change`, and recalculate Batch Manager
if it is open.

### An old project opens automatically

The autosaved session was restored. Follow section 18.

### The application does not start

For source execution, verify Python version, virtual-environment activation,
dependency installation, and that `main_launcher.py` is being run from the
project directory.

## 21. Data and safety limitations

- Calculation output depends on the entered data.
- Custom DB values are the user's responsibility.
- Supplier loading values and densities can vary.
- Special residues may require process-specific validation.
- Cleavage and synthesis conditions must be reviewed against laboratory SOPs.
- Keep independent backups of critical project and export files.

## 22. Quick reference

```text
New sequence or setup       → Generate
Manual Plan edit            → Apply Change
Multiple peptides           → Project Manager / Batch Manager
Missing custom material     → Show setup / Custom DB
Old session keeps opening   → Reset autosave file
Before laboratory use       → Review Plan, Materials, Checklist, Total, Export
```

