# SPPS Planner V9.0.0 — Strict Chemistry & Evidence-Aware AI (development)

The new V9.0.0 revision rejects misspelled topology fields instead of silently calculating a different molecule, checks per-reaction exact mass balance, records a structural-review SHA-256, and blocks attaching failed structural reviews to Auto Plan. The original SPPS reagent-calculation engine is unchanged.

An **opt-in** literature AI helper sends *only operator-previewed excerpts* to the OpenAI Responses API, with `store=false`, and validates returned exact quotations against the excerpts before showing an unapproved research draft. Configure `OPENAI_API_KEY` and `SPPS_LITERATURE_AI_MODEL`; no API request occurs without a separate user action. API use may incur charges. This is **not** a validated chemistry SOP.

Windows CI now includes packaged EXE `--gui-smoke` lifecycle checks, silent installer deployment/uninstall, preservation of test user files, and a downloadable JSON acceptance report. No native Windows success is claimed until those checks actually run.

Full source and evidence limitations: [Detailed Korean QA / handover](V9_STRICT_ATOMIC_EVIDENCE_AI_WINDOWS_KO.md).
