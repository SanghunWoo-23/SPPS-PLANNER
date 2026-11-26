# SPPS Planner V9.0.0 — Sharp Atomic & Evidence Extension

**Development source / operator review only.** Existing SPPS quantity calculations and Tkinter workflow are preserved.

New optional RDKit atom-mapped monomer and product graph module accepts explicit free-amine/carboxyl residue SMILES, multiple independently declared chains, operator-selected atom sites, and narrowly validated transformations: amide, disulfide, alkyl-halide thioether, carbonyl-conjugated thiol–Michael, explicit 1,4-CuAAC, and terminal-alkene RCM. The graph computes neutral average/monoisotopic mass, formula, product SMILES, and theoretical ions, **not reaction success, catalyst choice, chemical conversion, structural identity or yield**. It fails closed on missing atom maps or unsupported chemistry.

For noncanonical or protected residues, **complete user-reviewed SMILES** are required. Names such as `L-Nle`, `Aib`, `H-Ser(tBu)-OH`, or `H-Lys(Boc)-OH` are demonstrated in `docs/examples`, not inferred from names. Unspecified stereocentres and invalid valence are rejected. Pbf/Dde and other groups can be represented as explicit mapped atoms if the user provides their verified structures; arbitrary named reaction templates, SPAAC and 1,5-CuAAC remain unsupported.

In Auto Plan, choose `Independent molecular graph / Cross-link...` then `Custom atom-mapped JSON...`. Load a local JSON topology or import an approved monomer catalog (`token`, `smiles`, `source`) from Excel/CSV/TSV/JSON. Operator confirmation is required before attaching review-only graph results. Checklist recomputes the molecular graph to detect stale/tampered results.

`Local PDF / Paper Evidence...` retrieves short page-cited excerpts from operator-supplied PDF/TXT/MD sources. There is no external transmission, OCR, LLM article interpretation or autonomous SOP extraction. Existing opt-in Crossref bibliography is separate.

The Windows CI now includes Installer build, isolated silent install, installed EXE self-test, and silent uninstall. **Passing native Windows logs are not available from this Linux session.** Independent experimental yield/purity prediction performance remains unverified because no independent measured holdout dataset was provided.

Run focused tests with `python -m pytest -q tests/test_v9_atomic_topology_sharp.py tests/test_v9_custom_monomer_registry.py tests/test_v9_fulltext_evidence_sharp.py`; also run `python tools/validate_atomic_topology_v9.py` and `python main_launcher.py --self-test`.

References: [RDKit source and BSD-3 license](https://github.com/rdkit/rdkit), [RDKit reaction operations](https://www.rdkit.org/docs/RDKit_Book.html), [scikit-learn model persistence](https://scikit-learn.org/stable/model_persistence.html), [Crossref REST metadata](https://www.crossref.org/documentation/retrieve-metadata/rest-api).
