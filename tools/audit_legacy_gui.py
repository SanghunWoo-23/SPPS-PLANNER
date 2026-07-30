"""Report definition and SPPSGui-rebinding hotspots in the legacy controller."""
from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path


def audit(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    definitions: dict[str, list[int]] = defaultdict(list)
    class_bindings: dict[str, list[dict[str, object]]] = defaultdict(list)
    preserved_aliases: list[dict[str, object]] = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions[node.name].append(node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("_V"):
                    if isinstance(node.value, ast.Attribute):
                        preserved_aliases.append(
                            {
                                "alias": target.id,
                                "source": ast.unparse(node.value),
                                "line": node.lineno,
                            }
                        )
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "SPPSGui"
                ):
                    class_bindings[target.attr].append(
                        {
                            "line": node.lineno,
                            "value": ast.unparse(node.value),
                        }
                    )

    repeated_definitions = {
        name: lines
        for name, lines in sorted(definitions.items())
        if len(lines) > 1
    }
    repeated_bindings = {
        name: bindings
        for name, bindings in sorted(class_bindings.items())
        if len(bindings) > 1
    }
    return {
        "path": str(path),
        "line_count": len(source.splitlines()),
        "top_level_definition_count": sum(len(lines) for lines in definitions.values()),
        "repeated_definition_names": repeated_definitions,
        "spps_gui_binding_count": sum(len(items) for items in class_bindings.values()),
        "repeated_spps_gui_bindings": repeated_bindings,
        "preserved_aliases": preserved_aliases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("suite_gui/legacy_controller.py"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit(args.path)

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    print(f"File: {report['path']}")
    print(f"Lines: {report['line_count']}")
    print(f"Top-level definitions: {report['top_level_definition_count']}")
    print(f"Repeated definition names: {len(report['repeated_definition_names'])}")
    print(f"SPPSGui bindings: {report['spps_gui_binding_count']}")
    print(f"Repeated SPPSGui binding names: {len(report['repeated_spps_gui_bindings'])}")
    print(f"Preserved previous-function aliases: {len(report['preserved_aliases'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
