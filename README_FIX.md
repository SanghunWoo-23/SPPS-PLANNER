# SPPS Planner V6.0.0 — Windows CI SQLite handle fix

Replace the matching repository files with the files in this patch.

Changed files:
- `.github/workflows/ci.yml`
- `suite_gui/experimental_data.py`
- `tests/test_v4_canonical_data_audit.py`

Fixes:
- installs `requirements-dev.txt` in GitHub Actions before running pytest;
- keeps Windows 3.11 and 3.12 jobs independent with `fail-fast: false`;
- closes experimental SQLite connections on context-manager exit;
- prevents Windows `WinError 32` when `preview.sqlite` is removed;
- adds a regression test that verifies the SQLite handle is actually released.
