> **Later development update:** total-product MW is now supported for a single plain Lys ε-amide arm (`K(GGEP)`), but per-operation branch MW and non-head-to-tail mechanisms remain unsupported. See the [current reaction/branch guide](V9_REACTION_AND_BRANCH_EN.md).

# SPPS Planner V9.0.0 — Protected-form mass and yield scenario (development)

This development build adds catalog-supported Nα-Fmoc-free side-chain protected amino acids such as `H-Ser(tBu)-OH`, `H-Arg(Pbf)-OH`, `H-Glu(OtBu)-OH`, and `H-Lys(Boc)-OH`. Use `[H-Ser(tBu)-OH]-G` to place an exact building block inside a peptide sequence. `K(Dde)` and `K(ivDde)` are distinct.

## How to use

From Project Manager, open **Auto Plan (Optional)**. Select one Final Product pathway: linear deprotected, linear side-chain-protected, head-to-tail cyclic protected, or head-to-tail cyclic deprotected. Select the side-chain protection policy: catalog precursor assumptions, explicit annotations only, or none.

**Generate Full Plan** retains the established SPPS planning engine. The Selected Checklist now includes `peptide_mw` and `mw_form` for each operation. These numbers describe the theoretical *free peptide equivalent* rather than the MW of a resin-bound species. When a protected or cyclic product pathway is selected, selective cleavage, cyclization and/or final global deprotection appear as review-only rows (not as confirmed reactions or safe executable protocols).

## Mass states

- Linear protected (selective cleavage): side-chain protecting groups are assumed retained; verify this against the chemistry, especially acid-labile Trt.
- Head-to-tail protected: `linear protected neutral average MW - 18.01528` only when the N terminus is free and the C terminus is a free COOH.
- Head-to-tail deprotected: all modeled side-chain groups removed from the cyclic mass.
- Amide C terminus, capped N terminus, a single amino acid, unsupported branch chemistry or unknown modifications cause explicit warnings or disabled cyclic output.
- Mass values are **average neutral molecular weights**, not monoisotopic MS ions, masses of resin-attached intermediates, or evidence of synthesis success.

**Example:** `dS-dV-dS`, 2-CTC, catalog side-chain protection (tBu on both dSer): linear deprotected 291.305; linear protected 403.525; cyclic protected 385.510; cyclic deprotected 273.290 g/mol. These are theoretical masses assuming group retention and complete transformations.

## Optional yield scenario (not a prediction)

The theoretical upper-bound mass is `MW (g/mol) * scale (mmol) * copies / 1000`. The program does not output a realistic estimated recovery until the operator enters per-step coupling conversion (%) and isolation recovery (%), plus cyclization recovery (%) for cyclic products. It then calculates a simple, explicitly *operator-defined* scenario using `per_step_fraction ^ (residue_count - 1)` and the selected recovery factors. Loading, extra operations and purification variability must be reviewed separately. No empirical yield is inferred from sequence alone.

Native Windows execution, installer tests, automated reaction optimization, and laboratory validation have **not** been completed. See the Korean documentation for the full safety/accuracy limitations and literature links.
