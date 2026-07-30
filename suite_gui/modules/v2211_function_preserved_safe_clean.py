"""V2.2.11 function-preserved safe cleanup.

This module intentionally does NOT delete operator-facing legacy functions.
It only restores user-visible controls/options that were lost by the aggressive
V2.2.10 cleanup and makes the active V2.2.9 controller expose them clearly.
"""
from __future__ import annotations
import re
from typing import Any
import tkinter as tk
from tkinter import ttk

APP_VERSION = "V2.2.11"
VERSION_LABEL = "SPPS Planner GitHub V2.2.11 - Function Preserved Safe Clean"

AC_AA_OPTIONS = [
    "Ac-Ala-OH", "Ac-Arg(Pbf)-OH", "Ac-Asn(Trt)-OH", "Ac-Asp(OtBu)-OH", "Ac-Cys(Trt)-OH",
    "Ac-Gln(Trt)-OH", "Ac-Glu(OtBu)-OH", "Ac-Gly-OH", "Ac-His(Trt)-OH", "Ac-Ile-OH",
    "Ac-Leu-OH", "Ac-Lys(Boc)-OH", "Ac-Met-OH", "Ac-Phe-OH", "Ac-Pro-OH", "Ac-Ser(tBu)-OH",
    "Ac-Thr(tBu)-OH", "Ac-Trp(Boc)-OH", "Ac-Tyr(tBu)-OH", "Ac-Val-OH",
]
EXTRA_CHEMICAL_OPTIONS = [
    "Acetic anhydride (Ac2O)", "Palmitic acid", "Myristic acid", "Gallic acid", "Nicotinic acid", "Caffeic acid",
    "FITC", "Biotin", "Biotin-NHS", "FAM", "TAMRA", "ROX", "CY3", "CY5", "CY5.5", "CY7",
    "Ahx", "PEG4", "PEG8", "bAla", "gAla", "His6", "FLAG", "HA",
]


def _walk(widget):
    try:
        children = widget.winfo_children()
    except Exception:
        return
    for child in children:
        yield child
        yield from _walk(child)


def _norm(x: Any) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", str(x or "").lower())


def _dedupe(seq):
    out, seen = [], set()
    for item in seq:
        text = str(item or "").strip()
        if not text:
            continue
        key = _norm(text)
        if key not in seen:
            out.append(text)
            seen.add(key)
    return out


def _all_unit_options(gui, ns: dict[str, Any], column: str) -> list[str]:
    base = []
    for name in ("_v251_options_for_col", "_v250_options_for_col", "_v249_options_for_col"):
        fn = ns.get(name)
        if callable(fn):
            try:
                base += list(fn(gui, column))
            except Exception:
                pass
    try:
        base += list(getattr(gui, "UNIT_VALUES", []) or [])
    except Exception:
        pass
    if column == "Unit name":
        base += AC_AA_OPTIONS + EXTRA_CHEMICAL_OPTIONS
    return _dedupe(base)


def _patch_v229_unit_options(ns: dict[str, Any]):
    mod = ns.get("_install_v229_exact_sync")
    # The imported install function itself is not enough; patch the loaded module if available.
    try:
        import suite_gui.modules.v229_empty_start_exact_apply_sync as v229
    except Exception:
        return

    old_unit_options = getattr(v229, "_unit_options", None)

    def unit_options(gui, inner_ns: dict[str, Any], column: str) -> list[str]:
        values = []
        if callable(old_unit_options):
            try:
                values += list(old_unit_options(gui, inner_ns, column))
            except Exception:
                pass
        values += _all_unit_options(gui, ns, column)
        values += _all_unit_options(gui, inner_ns, column)
        return _dedupe(values)

    v229._unit_options = unit_options

    # Canonicalize Ac-AA names without losing exact protection spelling.
    old_canonical = getattr(v229, "_canonical", None)

    def canonical(inner_ns: dict[str, Any], value: str) -> str:
        raw = str(value or "").strip()
        key = _norm(raw)
        for opt in AC_AA_OPTIONS:
            if key == _norm(opt):
                return opt
        for opt in EXTRA_CHEMICAL_OPTIONS:
            if key == _norm(opt):
                return opt
        if callable(old_canonical):
            try:
                return old_canonical(inner_ns, value)
            except Exception:
                pass
        return raw

    v229._canonical = canonical


def _rename_setup_tabs(gui):
    for nb in [w for w in _walk(gui) if isinstance(w, ttk.Notebook)]:
        for tab in nb.tabs():
            try:
                text = str(nb.tab(tab, "text"))
                if text in {"Direct loading", "Loading rate"}:
                    nb.tab(tab, text="Loading")
            except Exception:
                pass


def _ensure_loading_tab(gui):
    # Preserve the existing Loading tab; do not add a second resin-loading field.
    for nb in [w for w in _walk(gui) if isinstance(w, ttk.Notebook)]:
        texts = []
        for tab in nb.tabs():
            try:
                texts.append(str(nb.tab(tab, "text")))
            except Exception:
                pass
        if "Unit defaults" in texts and "Loading" in texts:
            return
    # Fallback only if legacy tab is truly missing.
    target = None
    for nb in [w for w in _walk(gui) if isinstance(w, ttk.Notebook)]:
        texts = [str(nb.tab(t, "text")) for t in nb.tabs()]
        if "Unit defaults" in texts or "Reagents" in texts:
            target = nb
            break
    if target is None:
        return
    frame = ttk.Frame(target, padding=6)
    target.insert(0, frame, text="Loading")
    if not hasattr(gui, "apply_loading_calc"):
        gui.apply_loading_calc = tk.BooleanVar(value=False)
    if not hasattr(gui, "loading_aa_eq"):
        gui.loading_aa_eq = tk.StringVar(value="2")
    if not hasattr(gui, "loading_diea_eq"):
        gui.loading_diea_eq = tk.StringVar(value="4")
    ttk.Checkbutton(frame, text="Use direct resin loading calculation", variable=gui.apply_loading_calc).grid(row=0, column=0, columnspan=3, sticky="w")
    ttk.Label(frame, text="Loading amino acid eq").grid(row=1, column=0, sticky="w", pady=3)
    ttk.Entry(frame, textvariable=gui.loading_aa_eq, width=12).grid(row=1, column=1, sticky="w", pady=3)
    ttk.Label(frame, text="Loading DIEA eq").grid(row=2, column=0, sticky="w", pady=3)
    ttk.Entry(frame, textvariable=gui.loading_diea_eq, width=12).grid(row=2, column=1, sticky="w", pady=3)
    ttk.Label(frame, text="Resin loading mmol/g is edited only in Selected peptide editor.").grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))


def _ensure_unit_defaults_alias(gui):
    # Keep original Default AA eq/repeat controls, and add clear labels only if the words are absent.
    found_doubling = False
    found_default_eq = False
    for w in _walk(gui):
        if isinstance(w, ttk.Label):
            try:
                txt = str(w.cget("text"))
            except Exception:
                continue
            if "Default AA eq" in txt or "Amino acid eq" in txt:
                found_default_eq = True
            if "Doubling" in txt or "Default AA repeat" in txt:
                found_doubling = True
    if found_default_eq and found_doubling:
        return
    for nb in [w for w in _walk(gui) if isinstance(w, ttk.Notebook)]:
        for tab in nb.tabs():
            try:
                if str(nb.tab(tab, "text")) != "Unit defaults":
                    continue
                frame = nb.nametowidget(tab)
                row = 8
                if not found_default_eq and hasattr(gui, "coupling_eq"):
                    ttk.Label(frame, text="Amino acid eq").grid(row=row, column=0, sticky="w", pady=(8, 2))
                    ttk.Entry(frame, textvariable=gui.coupling_eq, width=18).grid(row=row, column=1, sticky="w", pady=(8, 2))
                    row += 1
                if not found_doubling and hasattr(gui, "coupling_repeats"):
                    ttk.Label(frame, text="Doubling / AA repeat").grid(row=row, column=0, sticky="w", pady=2)
                    ttk.Spinbox(frame, from_=1, to=30, textvariable=gui.coupling_repeats, width=18).grid(row=row, column=1, sticky="w", pady=2)
                return
            except Exception:
                pass


def _extend_class_unit_values(gui_cls):
    try:
        vals = list(getattr(gui_cls, "UNIT_VALUES", []) or [])
        gui_cls.UNIT_VALUES = _dedupe(vals + AC_AA_OPTIONS + EXTRA_CHEMICAL_OPTIONS)
    except Exception:
        pass


def apply_post_build(gui):
    _extend_class_unit_values(type(gui))
    try:
        gui.title(VERSION_LABEL)
    except Exception:
        pass
    for widget in _walk(gui):
        try:
            if (
                isinstance(widget, ttk.Label)
                and str(widget.cget("text")).startswith("SPPS Planner GitHub")
            ):
                widget.configure(text=VERSION_LABEL)
        except Exception:
            pass
    _rename_setup_tabs(gui)
    _ensure_loading_tab(gui)
    _ensure_unit_defaults_alias(gui)
    try:
        gui.UNIT_VALUES = _dedupe(
            list(getattr(gui, "UNIT_VALUES", []) or [])
            + AC_AA_OPTIONS
            + EXTRA_CHEMICAL_OPTIONS
        )
    except Exception:
        pass


def install(gui_cls, ns: dict[str, Any], *_args, **_kwargs):
    _patch_v229_unit_options(ns)
    _extend_class_unit_values(gui_cls)
    try:
        gui_cls.TITLE = VERSION_LABEL
    except Exception:
        pass
    old_build = gui_cls._build

    def build(self):
        old_build(self)
        apply_post_build(self)

    gui_cls._build = build
    return gui_cls
