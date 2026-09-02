# SPPS Planner Public / GitHub Data Policy

SPPS Planner V5.0.0 is distributed as a **sanitized public build**.

The public repository is intended to provide the complete public planner, recording, recommendation, model-management, and release code without publishing internal/private experimental history.

## What the public distribution includes

The Public/GitHub package keeps the functional source required for:

- core SPPS planning and calculation;
- sequence parsing and reagent/catalog handling;
- Project / Work Item / Run workflows;
- Materials, Checklist, Batch, Cleavage, and Export;
- Experimental Data schema and local SQLite storage;
- Add Result / Add Issue workflows;
- CSV/XLSX/ZIP import paths supported by the application;
- sequence/history lookup and evidence review;
- Loading and Cleavage advisors;
- bounded interpolation and public-safe empirical fallback logic;
- explicit Loading model rebuild, validation, model registry, promotion, and rollback;
- Risk & Evidence / Data Health review;
- public-safe empty experimental seed instructions.

## What is intentionally excluded

The public repository must not intentionally bundle:

- user/company/internal measured loading history;
- user/company/internal cleavage-report history;
- confidential product-to-sequence mappings;
- private exact-sequence cleavage anchor files;
- internal operator notes that disclose confidential experimental conditions;
- private/local model files trained on non-public laboratory history;
- exported experimental workbooks/databases that were not explicitly reviewed for publication.

## Public experimental seed directory

`apps/spps_planner_app/data/experimental_seed/` is expected to remain public-safe.

In the public release it should contain only documentation/templates that do not disclose internal experimental history. Users populate their own local knowledge base through the application's recording/import workflow.

## Runtime data

User-generated runtime data is stored outside the repository under the public-build user-data location. On Windows the core public build directory is based on:

```text
%LOCALAPPDATA%\SPPS_Planner_PUBLIC\
```

Runtime data can include:

- project/session state;
- experimental SQLite databases;
- imported lab files and provenance records;
- model registry/model files;
- logs;
- exports and generated output;
- HPLC/data-file link metadata.

These files must not be assumed to be publication-safe merely because the application created them.

## Publication and contribution rule

Before committing, publishing, attaching, or redistributing any experimental database, imported workbook, export, model, log, or generated report:

1. confirm that the data is authorized for publication;
2. inspect sequences, product names, lot/sample identifiers, notes, paths, and metadata;
3. remove confidential/private content where required;
4. verify that no public/private seed or local runtime directory was accidentally copied into the repository.

## Public / private source relationship

Shared functional source should remain common wherever possible. Build flavor and bundled data/policy content may differ, but the public repository must not become a reduced or fake implementation merely because it starts without internal experimental history.

A public installation with an empty experimental database should remain useful through the core planner, user-entered data, and public-safe fallback logic.
