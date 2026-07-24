# SPPS Planner V2.0.0

Fixed SPPS Planner V2.0.0 application source and required data.

## Key behavior

- Shows one blank peptide item at startup when no saved items exist.
- `CTC(합성기)` uses every residue written in Sequence as a coupling target, without loading AA/DIEA rows. The removed `CTC(합성용)` label is migrated only when opening older saved data.
- Cleavage preset names show the actual components, for example `TFA=95; TIS=2.5; Water=2.5`.
- User-facing version, VERSION files, EXE and Installer output names are unified as V2.0.0.
- Windows EXE/Installer build paths and output-name mismatches were corrected.

## Run from source

```bat
python main_launcher.py
```

## Build Windows EXE

```bat
BUILD_EXE_ONLY.bat
```

## Build Windows Installer

Install Python 3.11/3.12 and Inno Setup 6/7, then run:

```bat
BUILD_INSTALLER.bat
```

Expected installer:

```text
installer\output\SPPS_Planner_Setup_V2.0.0.exe
```
