"""Runtime contract for the fully composed desktop release."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RouteContract:
    name: str
    allowed_modules: tuple[str, ...]


ROUTES = (
    RouteContract("_build", ("suite_gui.modules.final_release_workflow",)),
    RouteContract(
        "generate_update_plan",
        ("suite_gui.modules.project_manager_workflow",),
    ),
    RouteContract("apply_change", ("suite_gui.modules.project_manager_workflow",)),
    RouteContract("export_outputs", ("suite_gui.modules.project_manager_workflow",)),
    RouteContract("pm_on_select", ("suite_gui.modules.project_manager_workflow",)),
    RouteContract("pm_add_peptide", ("suite_gui.modules.plan_workflow",)),
    RouteContract(
        "pm_delete_peptide",
        ("suite_gui.modules.project_manager_workflow",),
    ),
    RouteContract(
        "save_autosave_state",
        ("suite_gui.modules.v200_custom_db_tab_restore",),
    ),
    RouteContract(
        "schedule_autosave",
        ("suite_gui.modules.v200_custom_db_tab_restore",),
    ),
    RouteContract(
        "save_project",
        ("suite_gui.modules.v228_fast_legacy_exact_workflow",),
    ),
)


def active_route_report(gui_cls: type[Any]) -> dict[str, dict[str, Any]]:
    """Describe the final callable bound to every user-facing controller route."""
    report = {}
    for contract in ROUTES:
        function = getattr(gui_cls, contract.name, None)
        report[contract.name] = {
            "callable": callable(function),
            "module": getattr(function, "__module__", ""),
            "name": getattr(function, "__name__", ""),
            "allowed_modules": contract.allowed_modules,
        }
    return report


def validate_release_controller(gui_cls: type[Any]) -> None:
    """Fail fast if a historical late patch becomes an active release route."""
    failures = []
    for route, details in active_route_report(gui_cls).items():
        if not details["callable"]:
            failures.append(f"{route}: missing callable")
        elif details["module"] not in details["allowed_modules"]:
            failures.append(f"{route}: unexpected source {details['module']}")
    if failures:
        raise RuntimeError("Invalid SPPS Planner release composition: " + "; ".join(failures))


__all__ = [
    "ROUTES",
    "RouteContract",
    "active_route_report",
    "validate_release_controller",
]
