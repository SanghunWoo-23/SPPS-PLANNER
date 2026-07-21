"""V2.0.99 modular router.

Installs extracted modules after all legacy patches.  This is the active GUI
route for Peptide Items, Generate/Update, Export, and Cleavage controls.
"""
from __future__ import annotations

try:
    from spps_planner.version import VERSION_NAME
except Exception:
    VERSION_NAME = "SPPS Planner GitHub V2.1.9 - UI Rollback to V2.0.94 Layout"

from suite_gui.modules import gui_common as state
from suite_gui.modules.peptide_items import bind_peptide_items, duplicate_selected, delete_selected
from suite_gui.modules.cleavage_panel import ensure_cleavage_panel, refresh_cleavage_panel
from suite_gui.modules.export_panel import export_outputs, generate_update

VERSION_LABEL = VERSION_NAME


def normalize_gui(gui, ns: dict | None = None) -> None:
    try: gui.title(VERSION_LABEL)
    except Exception: pass
    try:
        if hasattr(gui, "title_label"):
            gui.title_label.configure(text=VERSION_LABEL)
    except Exception:
        pass
    try: bind_peptide_items(gui)
    except Exception: pass
    try: ensure_cleavage_panel(gui)
    except Exception: pass
    try:
        for w in state.walk_widgets(gui):
            try:
                if w.winfo_class() not in ("TButton", "Button"):
                    continue
                text = str(w.cget("text")).strip()
                if text == "Duplicate":
                    w.configure(command=lambda _gui=gui: duplicate_selected(_gui))
                elif text == "Delete":
                    w.configure(command=lambda _gui=gui: delete_selected(_gui))
                elif text in {"Export", "Save"}:
                    w.configure(command=lambda _gui=gui: export_outputs(_gui))
                elif text.startswith("Generate / Update") or text == "Apply cleavage":
                    w.configure(command=lambda _gui=gui: generate_update(_gui))
            except Exception:
                pass
    except Exception:
        pass
    try: refresh_cleavage_panel(gui)
    except Exception: pass


def install_v2097_router(SPPSGui, ns: dict | None = None) -> None:
    old_build = getattr(SPPSGui, "_build", None)
    def wrapped_build(self):
        if old_build is not None:
            old_build(self)
        normalize_gui(self, ns)
        for delay in (25, 100, 300, 800, 1800, 4000, 8000, 12000):
            try: self.after(delay, lambda _self=self: normalize_gui(_self, ns))
            except Exception: pass
    if old_build is not None:
        SPPSGui._build = wrapped_build
    SPPSGui.pm_duplicate_peptide = lambda self: duplicate_selected(self)
    SPPSGui.pm_delete_peptide = lambda self: delete_selected(self)
    SPPSGui.generate_update_plan = lambda self, *a, **k: generate_update(self)
    SPPSGui.pm_generate_selected = lambda self, *a, **k: generate_update(self)
    SPPSGui.pm_calculate_all = lambda self, *a, **k: generate_update(self)
    SPPSGui.apply_change = lambda self, *a, **k: generate_update(self)
    SPPSGui.pm_apply_change = lambda self, *a, **k: generate_update(self)
    SPPSGui.export_outputs = lambda self, *a, **k: export_outputs(self)
    SPPSGui._v2097_normalize_gui = lambda self: normalize_gui(self, ns)
