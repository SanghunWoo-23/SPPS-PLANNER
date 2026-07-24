"""V2.0.99 Project Manager modularization router.

This router is intentionally thin.  It installs the ProjectManagerController so
future GUI changes go into modules, not the legacy 43k-line patch stack.
"""
from __future__ import annotations

try:
    from spps_planner.version import VERSION_NAME
except Exception:  # pragma: no cover
    VERSION_NAME = "SPPS Planner GitHub V2.1.9 - UI Rollback to V2.0.94 Layout"

from suite_gui.modules.project_manager_panel import get_controller, normalize_project_manager

VERSION_LABEL = VERSION_NAME


def normalize_gui(gui, ns: dict | None = None) -> None:
    try:
        gui.title(VERSION_LABEL)
    except Exception:
        pass
    try:
        if hasattr(gui, "title_label"):
            gui.title_label.configure(text=VERSION_LABEL)
    except Exception:
        pass
    try:
        normalize_project_manager(gui)
    except Exception:
        pass


def install_v2098_router(SPPSGui, ns: dict | None = None) -> None:
    if getattr(SPPSGui, "_v2098_router_installed", False):
        return
    setattr(SPPSGui, "_v2098_router_installed", True)
    old_build = getattr(SPPSGui, "_build", None)

    def wrapped_build(self):
        if old_build is not None:
            old_build(self)
        normalize_gui(self, ns)
        # Late re-normalization protects against legacy deferred patches that
        # recreate widgets after initial build.
        for delay in (25, 100, 300, 800, 1800, 4000, 8000, 12000):
            try:
                self.after(delay, lambda _self=self: normalize_gui(_self, ns))
            except Exception:
                pass

    if old_build is not None:
        SPPSGui._build = wrapped_build

    def _controller_method(name):
        return lambda self, *a, **k: getattr(get_controller(self), name)(*a, **k)

    SPPSGui.pm_duplicate_peptide = _controller_method("duplicate_selected")
    SPPSGui.pm_delete_peptide = _controller_method("delete_selected")
    SPPSGui.generate_update_plan = _controller_method("generate_update")
    SPPSGui.pm_generate_selected = _controller_method("generate_update")
    SPPSGui.pm_calculate_all = _controller_method("generate_update")
    SPPSGui.apply_change = _controller_method("generate_update")
    SPPSGui.pm_apply_change = _controller_method("generate_update")
    SPPSGui.export_outputs = _controller_method("export_outputs")
    SPPSGui._v2098_normalize_gui = lambda self: normalize_gui(self, ns)
