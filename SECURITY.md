# Security policy — SPPS Planner V9.0.0

SPPS Planner handles experimental metadata and may ingest spreadsheets, molecular
structures and local PDFs. **Do not open untrusted serialized ML artifacts**;
only the Excel AI JSON prediction format uses validated non-executable inference.
Other legacy ML modules may still load `joblib`; use local, trusted sources only.

Report suspected security issues privately to the repository maintainer via
GitHub's private vulnerability reporting (if enabled), rather than posting
secrets, patient data, proprietary sequences or unreleased experimental data in
public issues.

The project has **no promise of a fixed security maintenance period**.
V9.0.0 remains a development-source candidate; third-party binary artifacts
require separate security and license review before distribution.
