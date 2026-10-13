<div align="center">

<img src="assets/SPPS_Planner_Icon.png" alt="SPPS Planner" width="150">

# SPPS Planner v7.0.0

**Windows-first desktop software for solid-phase peptide synthesis planning, calculation, and experiment-aware workflow support**

[![Release](https://img.shields.io/badge/release-v7.0.0-2563EB?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](requirements.txt)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D4?style=for-the-badge&logo=windows&logoColor=white)](#quick-start)

[한국어](README_KO.md) · [User Manual](docs/USER_MANUAL_EN.md) · [Architecture](docs/ARCHITECTURE.md) · [Public Data Policy](PUBLIC_DATA_POLICY.md)

</div>

## Overview

SPPS Planner connects peptide setup, synthesis planning, materials, checklists, batch calculations, cleavage settings, and experiment-aware records in one desktop workflow.

```text
Project Manager
  → Add / Edit peptide
  → Sequence / Scale / Resin / Loading / exact bottle setup
  → Generate
  → Review Plan / Materials / Checklist / Cleavage
  → Batch Manager / Export
```

## V7 highlights

- Project Manager-centered Add/Edit workflow
- Sequence, scale, copies, resin, loading, and LOT setup in one dialog
- Exact bottle identity for coupling reagent / additive / base / solvent
- **My recipes**: save, load, rename, delete, favorite, backup, and import
- Recent recipe and bottle shortcuts
- STEP 3 review before save and edit-change summary
- Targeted stale-result invalidation after synthesis-defining edits
- Ready / Calculated / Error status visibility in Project Manager
- Peptide-specific recipes kept separate from Batch Manager solution-prep defaults
- Loading / Cleavage recommendation and experimental-record support
- Public build excludes private laboratory history, local company databases, and original experimental images

## Quick start

### Requirements

- Windows 10 / 11
- 64-bit Python 3.11 or 3.12

### Run from source

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main_launcher.py
```

### Development / verification

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py
```

See [docs/WINDOWS_BUILD_KO.md](docs/WINDOWS_BUILD_KO.md) for Windows packaging.

## Basic workflow

1. Open **Project Manager → Add**.
2. Enter the peptide sequence and synthesis setup.
3. Select reagent / additive / base / solvent identities.
4. Review STEP 3 and save.
5. Select **Generate** to create the synthesis Plan.
6. Edit the Plan when needed and use **Apply Change** to refresh connected calculations.
7. Review Materials, Checklist, Cleavage, and Batch outputs.

For details, see the [User Manual](docs/USER_MANUAL_EN.md).

## Chemistry identity examples

- `NMM` = N-Methylmorpholine, **Base**
- `NMP` = N-methyl-2-pyrrolidone, **Solvent**
- `HOBt (anhydrous)` and `HOBt hydrate / monohydrate` remain separate bottle identities

## Public data policy

The public repository does not include private experimental history/seeds, source laboratory photographs, company-local SQLite databases, or confidential sample information.

See [PUBLIC_DATA_POLICY.md](PUBLIC_DATA_POLICY.md).

## Documentation

| Document | Purpose |
| --- | --- |
| [User Manual](docs/USER_MANUAL_EN.md) | Detailed usage |
| [한국어 사용자 매뉴얼](docs/USER_MANUAL_KO.md) | Korean manual |
| [Architecture](docs/ARCHITECTURE.md) | Source architecture |
| [Reagent DB Schema](docs/SPPS_REAGENT_DATABASE_SCHEMA.md) | Reagent database schema |
| [Parser Contract](docs/SPPS_PARSER_CONTRACT.md) | Sequence parser contract |
| [Windows Build](docs/WINDOWS_BUILD_KO.md) | EXE / installer build |
| [Release Notes](RELEASE_NOTES_V7.0.0_FINAL.md) | v7.0.0 release summary |

## Development principles

- Keep Public and Private ancestry separate.
- No runtime monkey-patch stack or placeholder/dummy production implementation.
- Keep recommendation provenance explicit where possible.
- Do not change validated chemistry behavior incidentally during UI refactoring.

## License

See [LICENSE](LICENSE).
