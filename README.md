# SPPS Planner V2.0.0

SPPS Planner V2.0.0 is a desktop planning tool for solid-phase peptide synthesis workflows. This repository contains the fixed V2.0.0 source, build scripts, required data, and regression tests. The application version is **V2.0.0**.

## Highlights

- Project and batch planning for SPPS workflows
- Editable Plan with Apply Change synchronization
- Recalculation of Materials, Checklist, Total, Batch, and Export after replacing an `Ac2O` Plan row with `Ac-Glu(OtBu)-OH`
- Amino-acid eq and position-based doubling controls
- Resin, solvent, base, catalyst, amino-acid/chemical, and cleavage-material calculations
- Chemical/modifier parsing in peptide sequences
- CSV/XLSX export and LOT information support
- `CTC(합성기)` full-sequence coupling behavior without loading AA/DIEA rows
- Legacy `CTC(합성용)` saved values migrate to `CTC(합성기)` and are not shown as a selectable resin
- Custom DB add/update/delete support for AA/chemical, coupling reagent, catalyst/additive, base, solvent, cleavage cocktail, resin, and other materials
- `Use DIC/HOBt` and `Use HBTU/NMP 10eq` switch chemistry/default conditions without auto-generating Plan preset rows

## Run from source

Requirements: Python 3.11 or 3.12 on Windows.

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python main_launcher.py
```

## Build Windows EXE

```bat
BUILD_EXE_ONLY.bat
```

Expected output:

```text
dist\SPPS_Planner\SPPS_Planner.exe
```

## Build Windows Installer

Install Inno Setup 6 or 7, then run:

```bat
BUILD_INSTALLER.bat
```

Expected output:

```text
installer\output\SPPS_Planner_Setup_V2.0.0.exe
```

## Autosaved session

The application can restore peptide items from the Windows autosave file:

```text
%LOCALAPPDATA%\SPPS Planner\spps_planner_session_v1.json
```

Close the application and remove that file to reset the autosaved session. Runtime session data is excluded by `.gitignore`.

## Custom DB

Open `Project Manager`, choose **Show setup**, and select the `Custom DB` tab. Enter a material name, class, MW, density, and note, then use `Add / Update material`. Custom entries are immediately available in the existing Plan dropdowns and MW/density calculation lookup. Selected rows can be removed with `Delete selected material`.

Supported classes include AA/Chemical, coupling reagent, catalyst/additive, base, solvent, cleavage cocktail, resin, and other materials. Entries are stored in the normal autosave session file:

```text
%USERPROFILE%\.spps_planner\spps_planner_session_v1.json
```

## Repository layout

- `main_launcher.py` — application entry point
- `suite_gui/` — classic desktop UI and workflow controllers
- `apps/spps_planner_app/spps_planner/` — parser, calculation engine, database, and export modules
- `apps/spps_planner_app/data/` — bundled reagent and process data
- `tests/` — regression tests
- `installer/` — Inno Setup configuration
- `docs/` — parser contract and reagent database schema documentation
- `docs/ARCHITECTURE.md` — release composition, extracted responsibilities, and verification

## Tests

```bat
python -m pip install -r requirements.txt -r requirements-dev.txt
python tools\verify_release.py --passes 5
```

## License

See [`LICENSE`](LICENSE). This repository uses a custom public academic citation license and is not presented as an OSI-approved open-source license.
