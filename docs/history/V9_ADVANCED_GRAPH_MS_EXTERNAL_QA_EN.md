# SPPS Planner V9.0.0 — Advanced graph, theoretical MS ions and external ML holdout

**Implementation scope is not experimental validation.** App version remains V9.0.0; the legacy SPPS chemistry engine is unchanged.

- **Backbone-aware head-to-tail:** identifies the primary/secondary free backbone N-terminal alpha amine and C-terminal free carboxyl OH, not Lys NZ; validated cases include `SKS`, `PSP` and protected `S(tBu)KS(tBu)`.
- **One Lys branch + main-chain head-to-tail:** new *review-only* `lysine_branch_head_to_tail` graph mode for an explicit single Lys epsilon-amide L-residue branch, e.g. `AK(GGEP)S`, `AK(Dde)(GGEP)S` (the Dde group is assumed removed before branch coupling). No synthesis chemistry is inferred and no multi-branch/multi-ring support is implied.
- **Exact-mass ion candidates:** verified RDKit molecules yield formula, average neutral mass, exact neutral monoisotopic mass and candidate [M+H]+, [M+2H]2+, [M+3H]3+, [M+Na]+, [M+K]+ and [M−H]− m/z. These are **not measured peaks**, isotope distributions, or predictions of ion intensity. Checklist annotates [M+H]+ only when stored structure is independently revalidated.
- **Independent ML validation:** blocks sequence and run-ID leakage, evaluates the number of unique *successfully predicted* sequence groups, uses the correct sample median and reports sequence-balanced MAE plus empirical interval coverage when available. Results do not certify predictive accuracy.
- **CI and deterministic chemistry contract:** `python tools/validate_v9_chemistry_matrix.py [--out results.json]`. The Windows workflow now includes a native PyInstaller build plus packaged executable self-test **as CI steps to be run**, not a claim of a completed Windows build.

**Still unsupported/unverified:** arbitrary noncanonical residues and protecting groups, multiple branches or rings, branch-arm cyclization, graph-defined chemistry for CuAAC/SPAAC/RCM, independent measured yield validation, full-text generative literature AI, and real Windows installer installation/upgrade/uninstall acceptance. Unknown topologies must remain withheld rather than guessed.
