"""SPPS Planner V2.0.0 final release adjustments.

This final layer is deliberately narrow: it preserves the accepted V2.2.15
workflow and only normalizes startup, cleavage preset display names, and release
version labeling.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

APP_VERSION = "V2.0.0"
VERSION_LABEL = "SPPS Planner V2.0.0"


ACTIVE_RESINS = [
    "Rink Amide AM", "Rink Amide MBHA", "Rink Amide ChemMatrix",
    "Rink Amide Tentagel", "2-CTC", "CTC(합성기)", "Wang", "HMPB",
    "Sieber Amide", "PAL resin", "Tentagel", "Manual",
]
_REMOVED_CTC_ALIASES = {"CTC(합성용)", "CTC 합성용", "CTC-synthesis", "CTC synthesis"}


def _normalize_resin(value):
    text = str(value or "").strip()
    if text in _REMOVED_CTC_ALIASES:
        return "CTC(합성기)"
    return text


def _enforce_resin_choices(gui):
    """Remove the deleted CTC(합성용) UI item without changing other behavior."""
    try:
        gui.RESIN_VALUES = list(ACTIVE_RESINS)
        type(gui).RESIN_VALUES = list(ACTIVE_RESINS)
    except Exception:
        pass

    try:
        for item in list(getattr(gui, "pm_items", []) or []):
            if isinstance(item, dict):
                item["resin"] = _normalize_resin(item.get("resin", ""))
    except Exception:
        pass

    try:
        current = _normalize_resin(gui.pm_resin.get())
        if current != str(gui.pm_resin.get() or "").strip():
            gui.pm_resin.set(current)
    except Exception:
        pass

    pm_resin_var = str(getattr(gui, "pm_resin", ""))
    for widget in _walk(gui):
        if not isinstance(widget, ttk.Combobox):
            continue
        try:
            values = [str(v) for v in widget.cget("values")]
            is_resin_widget = (
                str(widget.cget("textvariable")) == pm_resin_var
                or any("CTC" in v or "Rink Amide" in v for v in values)
            )
            if not is_resin_widget:
                continue
            current = _normalize_resin(widget.get())
            widget.configure(values=list(ACTIVE_RESINS))
            if current in ACTIVE_RESINS:
                widget.set(current)
            elif current in {"", "Amide"}:
                # Preserve the accepted blank/default startup state.
                widget.set(current)
        except Exception:
            pass

    try:
        if not getattr(gui, "_v200_resin_alias_trace", False):
            def _migrate_removed_alias(*_args):
                try:
                    value = str(gui.pm_resin.get() or "").strip()
                    normalized = _normalize_resin(value)
                    if normalized != value:
                        gui.pm_resin.set(normalized)
                    for item in list(getattr(gui, "pm_items", []) or []):
                        if isinstance(item, dict) and item.get("resin") in _REMOVED_CTC_ALIASES:
                            item["resin"] = "CTC(합성기)"
                except Exception:
                    pass
            gui.pm_resin.trace_add("write", _migrate_removed_alias)
            gui._v200_resin_alias_trace = True
    except Exception:
        pass


def _walk(widget):
    try:
        children = widget.winfo_children()
    except Exception:
        return
    for child in children:
        yield child
        yield from _walk(child)


def _blank_item():
    return {
        "project": "Project-001",
        "peptide": "Peptide-001",
        "sequence": "",
        "copies": "1",
        "scale": "0.2",
        "resin": "Rink Amide AM",
        "loading": "0.8",
        "lot": "",
        "chemistry": "DIC/HOBt",
        "status": "Ready",
        "cleavage_preset": "AUTO",
        "cleavage_components_text": "",
    }


def _ensure_one_start_item(gui):
    """Guarantee one blank slot only when the loaded session contains no items."""
    try:
        items = list(getattr(gui, "pm_items", []) or [])
        if items:
            return
        item = _blank_item()
        gui.pm_items = [item]
        gui.pm_list.delete(0, "end")
        try:
            label = gui.pm_display_name(item)
        except Exception:
            label = "Project-001 | Peptide-001"
        gui.pm_list.insert("end", label)
        # Keep the editor/results empty at startup; the item is loaded only when
        # the operator clicks or double-clicks it.
        gui._v229_active_index = None
    except Exception:
        pass


def _cleavage_display_values():
    try:
        from spps_planner.engine import cleavage_cocktail_presets
        frame = cleavage_cocktail_presets()
        values = ["AUTO"]
        mapping = {}
        for _, row in frame.iterrows():
            code = str(row.get("preset", "") or "").strip()
            components = str(row.get("components", "") or "").strip()
            if not code or code.upper() == "AUTO" or not components or components.startswith("<"):
                continue
            display = "; ".join(part.strip() for part in components.split(";") if part.strip())
            mapping[code] = display
            if display not in values:
                values.append(display)
        return values, mapping
    except Exception:
        return ["AUTO"], {}


def _configure_cleavage_preset(gui):
    values, mapping = _cleavage_display_values()
    try:
        current = str(gui.cleavage_preset.get() or "AUTO").strip()
        if current in mapping:
            gui.cleavage_preset.set(mapping[current])
    except Exception:
        pass
    target_var = str(getattr(gui, "cleavage_preset", ""))
    for widget in _walk(gui):
        if not isinstance(widget, ttk.Combobox):
            continue
        try:
            if str(widget.cget("textvariable")) == target_var:
                widget.configure(values=values, state="normal", width=38)
        except Exception:
            pass


def _apply_title(gui):
    try:
        gui.title(VERSION_LABEL)
    except Exception:
        pass
    for widget in _walk(gui):
        try:
            if isinstance(widget, ttk.Label) and str(widget.cget("text")).startswith("SPPS Planner"):
                widget.configure(text=VERSION_LABEL)
        except Exception:
            pass


def install(gui_cls, ns, *_args, **_kwargs):
    # Update the active controller constants used by session/export metadata.
    try:
        import suite_gui.modules.v229_empty_start_exact_apply_sync as v229
        v229.VERSION = APP_VERSION
        v229.TITLE = VERSION_LABEL
    except Exception:
        pass

    old_build = gui_cls._build
    old_destroy = gui_cls.destroy

    def build(self):
        old_build(self)
        _ensure_one_start_item(self)
        _enforce_resin_choices(self)
        _configure_cleavage_preset(self)
        _apply_title(self)
        # Reassert after legacy idle callbacks that may repopulate combobox values.
        try:
            self.after_idle(lambda _self=self: _enforce_resin_choices(_self))
            for delay in (100, 400, 1000):
                self.after(delay, lambda _self=self: _enforce_resin_choices(_self))
        except Exception:
            pass

    def destroy(self):
        try:
            return old_destroy(self)
        except tk.TclError:
            # Some legacy panes register the same Tcl cleanup command twice.
            # The root window is already closing at this point; suppress only
            # that harmless duplicate-cleanup error.
            return None

    gui_cls._build = build
    gui_cls.destroy = destroy
    gui_cls.TITLE = VERSION_LABEL
    return gui_cls
