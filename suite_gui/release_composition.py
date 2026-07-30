"""Ordered composition of the accepted SPPS Planner desktop release.

The legacy controller is intentionally treated as a behaviour baseline while
it is being decomposed.  All late release layers are registered here so their
order, displayed version, and installer signature are explicit and testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from suite_gui.modules.final_release_workflow import (
    install as install_final_release_workflow,
)
from suite_gui.modules.planner_workflow import install as install_planner_workflow
from suite_gui.modules.classic_workflow import install as install_classic_workflow
from suite_gui.modules.workbench_workflow import (
    install as install_fast_legacy_workflow,
)


Installer = Callable[..., Any]


@dataclass(frozen=True)
class ReleaseLayer:
    """One ordered compatibility layer in the accepted desktop release."""

    name: str
    internal_version: str
    title: str
    installer: Installer
    needs_original_build: bool = True


RELEASE_LAYERS = (
    ReleaseLayer(
        "classic_workflow_restore",
        "V2.2.7",
        "SPPS Planner GitHub V2.2.7",
        install_classic_workflow,
        needs_original_build=False,
    ),
    ReleaseLayer(
        "fast_legacy_exact_workflow",
        "V2.2.8",
        "SPPS Planner GitHub V2.2.8 - Fast Legacy UI + Exact Workflow",
        install_fast_legacy_workflow,
    ),
    ReleaseLayer(
        "planner_workflow",
        "V2.2.15",
        "SPPS Planner GitHub V2.2.15",
        install_planner_workflow,
    ),
    ReleaseLayer(
        "final_release_workflow",
        "V2.0.0",
        "SPPS Planner V2.0.0",
        install_final_release_workflow,
        needs_original_build=False,
    ),
)


def compose_release(gui_cls, namespace: dict[str, Any], original_build) -> None:
    """Apply every accepted layer in its historical order."""

    for layer in RELEASE_LAYERS:
        namespace["APP_VERSION"] = layer.internal_version
        namespace["VERSION_LABEL"] = layer.title
        gui_cls.TITLE = layer.title
        if layer.needs_original_build:
            layer.installer(gui_cls, namespace, original_build)
        else:
            layer.installer(gui_cls, namespace)


__all__ = ["RELEASE_LAYERS", "ReleaseLayer", "compose_release"]
