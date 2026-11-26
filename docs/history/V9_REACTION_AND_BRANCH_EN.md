# SPPS Planner V9.0.0 — Reaction Method & Limited Branch Mass Review

Development scope (not a validated laboratory SOP or empirical yield model).

## Head-to-tail review editor

Project Manager → Auto Plan (Optional) → select a head-to-tail protected/deprotected product → **Head-to-tail Method...**. The editor offers **DIC/HOBt, EDC·HCl/HOBt, HATU/DIEA, PyBOP/NMM, DIC/Oxyma**. Coupling agents, additives and bases are distinct roles, **not all catalysts**. Enter equivalents per bottle, solution concentration in mM, solvent, reaction time and optional temperature. No protocol settings are supplied automatically. Preview the **mmol** per reagent and the ideal solution volume using `mL per copy = 1000 × scale(mmol) / concentration(mM)`. Supplier-specific mass/volume amounts require exact bottle MW and density. Blank values are stored with `INCOMPLETE_REVIEW_ONLY` status.

`Use as unapproved draft` attaches the method to Auto Plan, the project `v9_mass_options.reaction_review`, and the Checklist **review-only** head-to-tail stage; it does not overwrite established Plan/Materials calculations. JSON export includes the draft and its provenance. Reload restores a method only if sequence, resin, scale, copies and protecting-group policy match.

Supported mass pathway: **solution-phase head-to-tail amide closure** after a verified selective cleavage, retaining side-chain protection on a conditional basis. Protected cyclic MW = protected linear MW − 18.01528 g/mol. On-resin head-to-tail, disulfide, side-chain lactam, click, RCM and modified bonding are not quantitatively implemented and must not receive fabricated conditions or masses.

## Limited lysine branch mass

`K(GGEP)` (or `K(Dde)(GGEP)` where the handle is removed) is treated as **one ordinary L-amino-acid branch arm attached through Lys ε-NH2 to the arm C-terminal COOH**. The attachment releases one H2O; the branch net mass increment equals the sum of its residue contributions. Catalog side-chain protecting-group retention is conditional. Multi-arm, D-amino-acid arms, nested protected arms, other attachment chemistries, and branch+cyclization require an atomic connection graph and fail closed.

Branch final-product theoretical MW is available in Auto Plan. **Per-operation branch Checklist MW remains blocked** because the currently displayed assembly order and protection state are not atom-verified. Existing operator-input yield arithmetic remains explicitly unvalidated.

## Checks & limitations

Review source tests, optional Xvfb GUI test and static Windows release verification before distributing. Native Windows GUI/EXE/Installer, real reaction conditions and yield are not verified by these source tests. Only the Public ZIP may be uploaded to GitHub.
