# SPPS Planner V9.0.0 — Strict Chemistry and Evidence Input Contracts (2026-11-11)

## Changes

- Operator-defined monomer `token` and inline `smiles` must resolve to the same canonical mapped, stereochemical structure. A mismatched protecting group, identity or atom-map is rejected; no automatic substitution is allowed.
- Optional `reported_mw` or `mw` validates the **average neutral monomer molecular weight (g/mol)** against the atom-mapped RDKit structure within 0.25 g/mol. Counterions, salts and solvates require separate composition review.
- Duplicate JSON keys, NaN/Infinity, malformed headers, duplicate `token`/`smiles` fields, and oversized topology input are rejected before a result can be attached to Auto Plan.
- Assembly-stage intermediate products now carry a neutral average MW, exact mass, molecular formula, and number of connected components. These are theoretical molecular equivalents, not resin measurements or verified conversions.
- Opt-in AI evidence review rejects duplicate excerpt IDs and empty, unanchored findings. Exact-quote matching is not proof of scientific interpretation.
- `python tools/review_custom_topology_v9.py topology.json --catalog monomers.xlsx` is the reproducible, non-GUI chemistry review CLI. Exit code 0 means a theoretical graph passed; 2 means WITHHELD.

## Scope and restrictions

Existing SPPS equivalents and base chemistry engine were not modified. Physical chemical identity, reaction selectivity, wet-lab yield/purity, external model prediction accuracy, and native Windows installation require independent evidence. CI definitions and Linux/Xvfb checks do not replace those validations. Do not publish the Private package or its seed data.
