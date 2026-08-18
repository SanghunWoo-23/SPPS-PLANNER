# Public / GitHub data policy

This distribution intentionally contains no bundled private experimental history.

The public build keeps the experimental-data schema, Record Lab Data UI,
CSV/XLSX import, consensus recommendation, similarity search, and ML/advisor
logic. Users populate the knowledge base with their own authorized data.

Removed from the public distribution:
- user/company loading-history seed observations;
- user/company cleavage-report seed observations;
- private product-to-sequence mappings;
- exact sequence-specific cleavage rules derived from private experiment history;
- validation notes that disclose those private experimental conditions.

Runtime experimental data is stored outside the source tree and should not be
committed to Git. Review all imported/exported data before publication.
