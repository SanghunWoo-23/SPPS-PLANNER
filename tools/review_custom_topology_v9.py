"""Review mapped peptide topology from local files without starting Tkinter.

Example:
  python tools/validate_atomic_topology_v9.py topology.json --catalog monomers.xlsx

A successful result is only a theoretical structure/mass review. It does not
approve a reaction, vendor identity, protecting-group stability or a wet-lab SOP.
No network access, executable deserialization, or dynamic plugins are used.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'apps'/'spps_planner_app'
if str(APP) not in sys.path:
    sys.path.insert(0,str(APP))

from spps_planner.atomic_topology_v9 import calculate_atomic_topology, load_atomic_topology_json
from spps_planner.monomer_catalog_v9 import import_monomer_catalog, resolve_catalog_tokens


def validate_files(topology: str|Path, catalog: str|Path|None = None) -> dict:
    """Return a data-only, explicit PASS / WITHHELD result; never repair input."""
    try:
        document=load_atomic_topology_json(topology)
        catalog_details=None
        if catalog is not None:
            catalog_details=import_monomer_catalog(catalog)
            if catalog_details['rejected_count'] or not catalog_details['accepted_count']:
                return {'status':'WITHHELD_CATALOG_REVIEW_REQUIRED',
                        'accepted_count':catalog_details['accepted_count'],
                        'rejected_count':catalog_details['rejected_count'],
                        'rejected':catalog_details['rejected'],
                        'note':'Resolve all rejected definitions before calculating a product.'}
            definitions={entry['token']:entry for entry in catalog_details['accepted']}
            document=resolve_catalog_tokens(document,definitions)
        result=calculate_atomic_topology(document)
        if catalog_details is not None:
            result['catalog_sha256']=catalog_details['file_sha256']
        result['review_scope']='THEORETICAL_STRUCTURE_ONLY_NOT_AN_APPROVED_SYNTHESIS'
        return result
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as exc:
        return {'status':'WITHHELD_INVALID_INPUT','reason':str(exc)[:500],
                'review_scope':'NO_PRODUCT_MASS_ACCEPTED'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('topology',help='Local atom-mapped peptide topology JSON')
    parser.add_argument('--catalog',help='Optional approved-to-review monomer JSON/CSV/TSV/XLSX file')
    args=parser.parse_args(argv)
    review=validate_files(args.topology,args.catalog)
    print(json.dumps(review,indent=2,ensure_ascii=False,allow_nan=False))
    return 0 if review.get('status')=='ATOM_MAPPED_GRAPH_PASS' else 2


if __name__=='__main__':
    raise SystemExit(main())
