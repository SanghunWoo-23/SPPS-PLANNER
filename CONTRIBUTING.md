# Contributing

SPPS Planner V2.0.0 is a fixed release. Changes should preserve the existing operator workflow and calculation behavior.

## Development setup

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
python -m pip install -r requirements.txt -r requirements-dev.txt
python main_launcher.py
```

## Validation

```bat
python -m compileall -q main_launcher.py suite_gui peptiforg_core apps\spps_planner_app\spps_planner
set PYTHONPATH=%CD%\apps\spps_planner_app;%CD%
python -m pytest -q tests\test_v2215_ctc_synthesis_full_sequence.py tests\test_v200_final_release.py -k "not gui"
```

Do not commit generated EXE/Installer files, virtual environments, caches, runtime logs, exports, or user session files.
