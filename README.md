<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner icon" width="128">

# SPPS Planner V9.0.0

**Windows-first solid-phase peptide synthesis planning and evidence-aware research tooling**

[한국어 안내](README_KO.md) · [User Manual](docs/USER_MANUAL_EN.md) · [V9 development scope](README_V9_DEVELOPMENT.md)

</div>

> **Development source candidate — not a verified Windows binary release.**
> This archive contains Python source code and Windows build inputs, **not** an
> executable installer. SPPS calculation outputs and AI predictions require
> operator review and independent experimental validation.

**Documentation:** [Current guide and files](docs/INDEX.md).

## Features

- Project Manager, editable SPPS Plan, Materials, Checklist, Batch Manager,
  selective cleavage/workup drafts, and operator-reviewed Auto Plan.
- Sequence-aware reagent calculations and supported protected-peptide,
  Lys-branch and head-to-tail mass calculations.
- Optional RDKit molecular graph cross-checks for **explicitly mapped**
  standard/noncanonical monomers and bounded ring/branch topologies.
- Local CSV/Excel review (multiple files and sheets), dataset audits,
  exploratory yield/purity ML, and stage-wise model readiness reporting.
- Local evidence search across user-supplied PDF/text and optional
  explicitly consented, excerpt-only online literature assistance.
- Cancellation-aware background ML tasks and read-only independent
  external-data evaluation CLI.

**Limits:** Complex reactions are not automatically proven feasible; theoretical
MW does not establish reaction selectivity or isolated yield. ML performance
must be established on independent wet-lab data. No Windows-native acceptance
result is claimed for the source packages.

## Quick start (source checkout)

Python **3.11/3.12**, Tkinter and a supported OS are required. Windows is the
primary target; Linux with a desktop/Xvfb is useful for development/testing.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate   |   POSIX: source .venv/bin/activate
python -m pip install -r requirements.txt
python main_launcher.py --self-test
python main_launcher.py
```

RDKit is installed by the default `requirements.txt`. The historical
`requirements-rdkit-optional.txt` is retained for compatibility only;
**do not install it a second time**. If RDKit is unavailable, advanced
atom-mapped verification is withheld rather than guessed.

For Windows EXE + Installer builds, run **`INSTALL_BUILD_TOOLS_AND_BUILD.bat`**
on Windows only; its outcome still requires native validation. See
[full manuals](docs/USER_MANUAL_EN.md) and [development status](README_V9_DEVELOPMENT.md).

## Verify and build a GitHub-ready PUBLIC source package

```bash
python tools/github_release_preflight_v9.py --strict
python -m pytest -q tests/test_v9_github_public_preflight.py
python tools/build_github_source_release_v9.py --output ../SPPS_Planner_V9.0.0_PUBLIC_SOURCE.zip
```

The independent GitHub Actions preflight checks for private experiment seeds,
local databases and serialized models, verifies the version and source SHA-256
manifest, and produces a source ZIP as an **Actions artifact**. It does not
publish a Release or modify an existing branch. See
[GitHub publication guide (KO)](docs/GITHUB_PUBLICATION_V9_KO.md).

## Privacy, citations and licensing

**Only PUBLIC source may be published.** Never include Private lab records,
experimental seed files, company data, project sessions or learned models.
See [public data policy](PUBLIC_DATA_POLICY.md) and [security](SECURITY.md).

This repository is **source-available under a custom non-commercial academic
citation license**, **not an OSI-approved open-source license**. See [LICENSE](LICENSE)
and [CITATION.cff](CITATION.cff). Third-party licenses need to be reviewed
before redistributing binaries; see [dependency notices](docs/V9_DEPENDENCY_LICENSE_NOTICE.md).

**Repository:** https://github.com/SanghunWoo-23/SPPS-PLANNER
