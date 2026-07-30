from __future__ import annotations

import hashlib
import json
import math

import pandas as pd

from spps_planner.engine import (
    PlanInput,
    generate_cleavage_cocktail,
    generate_detailed_operations,
    generate_materials,
    generate_step_materials,
    generate_step_matrix,
    generate_step_reagent_plan,
    plan_summary,
    validate_plan,
)


def _normal(value):
    if value is None or isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, float):
        return round(value, 9)
    return value


def _digest(value) -> str:
    if isinstance(value, pd.DataFrame):
        value = [
            [str(column) for column in value.columns],
            [[_normal(cell) for cell in row] for row in value.itertuples(index=False, name=None)],
        ]
    elif isinstance(value, dict):
        value = {str(key): _normal(item) for key, item in sorted(value.items())}
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


SCENARIOS = {
    "amide": PlanInput(
        sequence="Ac-EEMQRR-NH2",
        scale_mmol=0.4,
        resin="Rink Amide AM",
        resin_loading_mmol_g=0.8,
    ),
    "ctc": PlanInput(
        sequence="AEKIRKELEKQ",
        scale_mmol=0.2,
        resin="CTC(합성기)",
        resin_loading_mmol_g=1.39,
        apply_resin_loading=False,
        default_coupling_reagent="HBTU",
        default_reagent_eq=10,
        default_catalyst="",
        default_catalyst_eq=0,
        default_base="DIEA",
        default_base_eq=5,
        default_reaction_solvent="NMP",
    ),
    "branch": PlanInput(
        sequence="Ac-G-H-K-K-K(GGEP)-NH2",
        scale_mmol=0.4,
        resin="Rink Amide AM",
    ),
}

GENERATORS = {
    "step_matrix": generate_step_matrix,
    "operations": generate_detailed_operations,
    "reagent_plan": generate_step_reagent_plan,
    "step_materials": generate_step_materials,
    "materials": generate_materials,
    "cleavage": generate_cleavage_cocktail,
    "validation": validate_plan,
    "summary": plan_summary,
}

EXPECTED = {
    "amide": {
        "step_matrix": "fa666e80f8d47a2c368cf0ea38edf7deaec6317e01d8d4592fbcb66b344bc7f9",
        "operations": "43c82c7d77b37fb5ef04c7767ebca609e494b627d80856bfb951f92926c248e6",
        "reagent_plan": "d0bbedbd9dd8555a41577ed980c9ee0e66ee7faa67d28fcc13d60d47b208928b",
        "step_materials": "9d8d62b7e020bbee64022a99d27531115bc9ab2c8488d9791e1839c582171e69",
        "materials": "66f9c1940ca40715e8e64139b8ccfe4a2cc7ade05d06285f19f564e1b2046eac",
        "cleavage": "e07cf094a1a7a1ff2c172ed9a42e993eef1d9b7187d222c78d5c34e62fd6bff2",
        "validation": "749bd99884f2501b3c135e277a6042039fafd80a041e9377679092546df4482e",
        "summary": "35b18af3660f3f6bf088b98e087c71e51c7631681fcd447584b7116a4ec8c917",
    },
    "ctc": {
        "step_matrix": "59bedf9c7a269812bf70d00816680bf550d21af821a3d97ffe5c765d33556abb",
        "operations": "7e3f7957abceeca0d62f4e9231cecd9ddd75c187a1fb0e383fba6f9e253bed45",
        "reagent_plan": "83c1764d7f4cc24b348af81bdd3494049788cce07bba4b94ed64d0ab5c0c88eb",
        "step_materials": "5f27e98e21826db33c41ccd624d69aacd70e94a9b9f48ed071f360db116d66c6",
        "materials": "54c322a6edf99e4f760ed07ca1fe46902d8d645d80ddfc71e66fb30989203799",
        "cleavage": "f37945d8e59824d12c71a908ac7f9c7c2e9785121224283007c2e1a6bce68504",
        "validation": "89b0e3b1b718221d63c7f8021f41bd006401f4288e90da67fafcd964fb83911b",
        "summary": "81f864417c2c529323e6c1128f8d9f9042d7b990dd7a10b3c19932c419d5a081",
    },
    "branch": {
        "step_matrix": "6dca1a5595a6947bcbdbc6acb67cff8e0ef769e8b0d6a5a31bb524fdad890065",
        "operations": "bc93696bbbcab972690c40ea9ad40874dd5cb62d82de9d0d3fae7b104dc94799",
        "reagent_plan": "6b5503a8b4c16b17a501e2b16afd2960c1cbac754f700bb5a1fb4224212c8043",
        "step_materials": "5863f4322d2ca5d09051aeec449ab9898946ce6850a3835f5b1a21a115741297",
        "materials": "84eb3b4ac09171c6622625ddd1674e23dca182fa50a76c9b8a595cdf6e77b017",
        "cleavage": "1e8e15e8bf6aba576764f0c423d86f252a771a923665861390266db087c9b8bb",
        "validation": "fc7afc76fc6eec71461e9c1b19ecea65fe762806895e9e61e84c8d1b077497c8",
        "summary": "cd18e57f87ffe9e5eb9833f5cf088d11851dc9b94db2ed98d74015427f5ca1b1",
    },
}


def test_accepted_engine_outputs_remain_byte_equivalent_after_normalization():
    actual = {
        scenario: {
            output: _digest(generator(plan))
            for output, generator in GENERATORS.items()
        }
        for scenario, plan in SCENARIOS.items()
    }
    assert actual == EXPECTED
