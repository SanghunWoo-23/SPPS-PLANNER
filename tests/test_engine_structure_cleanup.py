from __future__ import annotations

import ast
from pathlib import Path


def test_embedded_engine_uses_single_canonical_material_pipeline():
    root = Path(__file__).resolve().parents[1]
    engine_path = root / "apps" / "spps_planner_app" / "spps_planner" / "engine.py"
    source = engine_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(engine_path))

    forbidden_fragments = (
        "_v219", "_v221", "_v222",
        "_V219", "_V221", "_V222",
        "ORIG_GENERATE_STEP_MATERIALS", "ORIG_GENERATE_MATERIALS",
        "patch-stack",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "generate_step_materials" in functions
    assert "generate_materials" in functions

    # The public material APIs must be defined only once and must not be rebound
    # later through compatibility aliases or version-specific wrappers.
    assert sum(1 for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "generate_step_materials") == 1
    assert sum(1 for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "generate_materials") == 1

    rebound = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in {"generate_step_materials", "generate_materials"}:
                rebound.append(target.id)
    assert rebound == []
