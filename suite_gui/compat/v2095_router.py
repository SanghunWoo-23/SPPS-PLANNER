"""Final cleanup router for V2.0.99.

This module is the single last-mile binding point for the historical Tk GUI.
It does not remove existing UI widgets.  It only rebinds the Project Manager
buttons/listbox to stable modular handlers so older patch-stack functions cannot
silently override the active behavior.
"""
from __future__ import annotations

try:
    from spps_planner.version import VERSION_NAME
except Exception:  # Direct script launch before app path setup.
    VERSION_NAME = "SPPS Planner GitHub V2.1.9 - UI Rollback to V2.0.94 Layout"

from suite_gui.modules.peptide_items import bind_peptide_items, duplicate_selected, delete_selected
from suite_gui.modules.cleavage_panel import ensure_cleavage_panel, refresh_cleavage_panel
from suite_gui.modules.export_panel import export_outputs, generate_update

VERSION_LABEL = VERSION_NAME


def _walk_widgets(gui, ns: dict):
    walker = ns.get("_v2093_walk")
    if callable(walker):
        return walker(gui)
    out = []
    stack = list(getattr(gui, "winfo_children", lambda: [])())
    while stack:
        w = stack.pop(0)
        out.append(w)
        try:
            stack.extend(w.winfo_children())
        except Exception:
            pass
    return out


def normalize_gui(gui, ns: dict) -> None:
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
        bind_peptide_items(gui, ns)
    except Exception:
        pass
    try:
        ensure_cleavage_panel(gui, ns)
    except Exception:
        pass
    try:
        for w in _walk_widgets(gui, ns):
            try:
                if w.winfo_class() not in ("TButton", "Button"):
                    continue
                text = str(w.cget("text")).strip()
                if text == "Duplicate":
                    w.configure(command=lambda _gui=gui: duplicate_selected(_gui, ns))
                elif text == "Delete":
                    w.configure(command=lambda _gui=gui: delete_selected(_gui, ns))
                elif text in {"Export", "Save"}:
                    w.configure(command=lambda _gui=gui: export_outputs(_gui, ns))
                elif text.startswith("Generate / Update") or text == "Apply cleavage":
                    w.configure(command=lambda _gui=gui: generate_update(_gui, ns))
            except Exception:
                pass
    except Exception:
        pass
    try:
        refresh_cleavage_panel(gui, ns)
    except Exception:
        pass


def install_v2095_router(SPPSGui, ns: dict) -> None:
    old_build = getattr(SPPSGui, "_build", None)

    def wrapped_build(self):
        if old_build is not None:
            old_build(self)
        normalize_gui(self, ns)
        for delay in (50, 250, 750, 1500, 3500, 7000, 12000):
            try:
                self.after(delay, lambda _self=self: normalize_gui(_self, ns))
            except Exception:
                pass

    if old_build is not None:
        SPPSGui._build = wrapped_build
    SPPSGui.pm_duplicate_peptide = lambda self: duplicate_selected(self, ns)
    SPPSGui.pm_delete_peptide = lambda self: delete_selected(self, ns)
    SPPSGui.generate_update_plan = lambda self, *a, **k: generate_update(self, ns)
    SPPSGui.pm_generate_selected = lambda self, *a, **k: generate_update(self, ns)
    SPPSGui.pm_calculate_all = lambda self, *a, **k: generate_update(self, ns)
    SPPSGui.apply_change = lambda self, *a, **k: generate_update(self, ns)
    SPPSGui.pm_apply_change = lambda self, *a, **k: generate_update(self, ns)
    SPPSGui.export_outputs = lambda self, *a, **k: export_outputs(self, ns)
    SPPSGui._v2095_normalize_gui = lambda self: normalize_gui(self, ns)
