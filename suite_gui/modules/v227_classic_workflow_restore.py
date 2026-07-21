"""V2.2.7 Classic Project Manager workflow restoration.

This module is the final controller layer for the Classic UI.  It deliberately
separates Generate (build a plan from editor/setup values) from Apply Change
(commit the currently visible/edited Selected Plan to linked tabs), restores
per-peptide autosave/restore, and keeps the cleavage cocktail preset explicit
instead of silently changing it from the resin profile.
"""
from __future__ import annotations

from typing import Any
import re

import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox


VERSION = "V2.2.7"
TITLE = "SPPS Planner GitHub V2.2.7"

PLAN_COLUMNS = [
    "No", "Unit name", "MW", "Density(g/mL)", "Unit mmol", "Unit amount",
    "Reagent 1", "R1 MW", "R1 Density", "R1 mmol", "R1 amount",
    "Reagent 2 / catalyst", "R2 MW", "R2 Density", "R2 mmol", "R2 amount",
    "Base", "Base MW", "Base Density", "Base mmol", "Base amount",
    "Coupling solvent", "Solvent mL", "Repeat", "Note",
]

PLAN_WIDTHS = {
    "No": 50, "Unit name": 280, "MW": 90, "Density(g/mL)": 120,
    "Unit mmol": 105, "Unit amount": 120, "Reagent 1": 125, "R1 MW": 85,
    "R1 Density": 105, "R1 mmol": 105, "R1 amount": 120,
    "Reagent 2 / catalyst": 175, "R2 MW": 85, "R2 Density": 105,
    "R2 mmol": 105, "R2 amount": 120, "Base": 115, "Base MW": 85,
    "Base Density": 105, "Base mmol": 105, "Base amount": 120,
    "Coupling solvent": 170, "Solvent mL": 105, "Repeat": 70, "Note": 360,
}

# Restore the original cleavage cocktail preset list. V2.2.6 accidentally
# replaced these values with the resin-name list.
CLEAVAGE_PRESETS = [
    "AUTO",
    "DEFAULT_TFA_WATER",
    "DEFAULT_TFA_TIS_WATER",
    "TFA_TIS_WATER_96_2_2",
    "TFA_MC_1_1",
    "ACOH_TFE_MC_1_1_8",
    "ACOH_TFE_MC_2_2_6",
    "REDUCING_TFA_TIS_WATER_EDT",
    "CYS_EDT",
    "REAGENT_B",
    "REAGENT_K",
    "REAGENT_L",
    "REAGENT_R",
    "REAGENT_H",
    "REAGENT_I",
    "TFA_WATER_TIS_EDT",
    "TFA_THIOANISOLE_EDT_ANISOLE",
    "TFA_TIS_P_CRESOL_WATER",
    "LOW_TFA_2CTC_TEST",
    "CUSTOM",
]

OUTPUT_TREE_SPECS = {
    "selected_plan_rows": ("pm_selected_plan_tree", PLAN_COLUMNS),
    "selected_material_rows": ("pm_selected_material_tree", None),
    "selected_total_rows": ("pm_selected_total_tree", None),
    "selected_checklist_rows": ("progress_tree", ["line", "done", "checked_at", "operation", "unit", "next_step", "note"]),
    "selected_cleavage_rows": ("pm_cleavage_tree", None),
}



def _get(ns: dict[str, Any], name: str, default: Any = None) -> Any:
    return ns.get(name, default)


def _walk(root):
    out = []
    stack = [root]
    while stack:
        w = stack.pop(0)
        out.append(w)
        try:
            stack.extend(w.winfo_children())
        except Exception:
            pass
    return out


def _num(value: Any, default: float = 0.0) -> float:
    try:
        s = str(value or "").replace(",", "").strip()
        return float(s) if s else float(default)
    except Exception:
        return float(default)


def _fmt(value: Any, digits: int = 4) -> str:
    try:
        f = float(value)
    except Exception:
        return "" if value is None else str(value)
    if abs(f) < 1e-12:
        return ""
    if abs(f - round(f)) < 1e-10:
        return str(int(round(f)))
    return f"{f:.{digits}f}".rstrip("0").rstrip(".")


def _tree_rows(tree) -> list[dict[str, str]]:
    if tree is None:
        return []
    cols = list(tree["columns"])
    rows: list[dict[str, str]] = []
    for iid in list(tree.get_children()):
        vals = list(tree.item(iid, "values"))
        vals += [""] * max(0, len(cols) - len(vals))
        rows.append({c: str(vals[i]) if i < len(vals) else "" for i, c in enumerate(cols)})
    return rows


def _write_dict_rows(tree, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    if tree is None:
        return
    if columns is None:
        columns = []
        for row in rows:
            for key in row.keys():
                key = str(key)
                if key not in columns:
                    columns.append(key)
        if not columns:
            columns = list(tree["columns"])
    tree.configure(columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        width = 130
        if col in {"note", "operation", "next_step", "solution_note"}:
            width = 320
        elif col in {"material", "protected_reagent", "Unit name", "unit"}:
            width = 210
        elif col in {"done", "line", "step", "No"}:
            width = 75
        tree.column(col, width=width, minwidth=45, anchor="w", stretch=False)
    kids = list(tree.get_children())
    if kids:
        tree.delete(*kids)
    for row in rows:
        tree.insert("", "end", values=[str(row.get(col, "") or "") for col in columns])


def _clear_tree(tree) -> None:
    if tree is None:
        return
    kids = list(tree.get_children())
    if kids:
        tree.delete(*kids)


def _save_visible_outputs_to_item(gui, index: int | None = None) -> None:
    if index is None:
        index = getattr(gui, "_v227_active_index", None)
    try:
        index = int(index)
        if not (0 <= index < len(gui.pm_items)):
            return
    except Exception:
        return
    item = gui.pm_items[index]
    # Commit any still-open in-place editor before taking the snapshot.
    try:
        editor = getattr(getattr(gui, "pm_selected_plan_tree", None), "_v254_editor", None)
        if editor is not None and editor.winfo_exists():
            editor.event_generate("<Return>")
            gui.update_idletasks()
    except Exception:
        pass
    for key, (attr, _columns) in OUTPUT_TREE_SPECS.items():
        tree = getattr(gui, attr, None)
        if tree is None and key == "selected_total_rows":
            tree = getattr(gui, "pm_total_tree", None)
        item[key] = _tree_rows(tree)


def _restore_visible_outputs_from_item(gui, item: dict[str, Any], ns: dict[str, Any]) -> bool:
    plan_rows = list(item.get("selected_plan_rows") or [])
    if not plan_rows:
        for key, (attr, _columns) in OUTPUT_TREE_SPECS.items():
            tree = getattr(gui, attr, None)
            if tree is None and key == "selected_total_rows":
                tree = getattr(gui, "pm_total_tree", None)
            _clear_tree(tree)
        return False

    _write_plan_tree(gui, plan_rows, ns)
    restored_linked = False
    for key, (attr, columns) in OUTPUT_TREE_SPECS.items():
        if key == "selected_plan_rows":
            continue
        rows = list(item.get(key) or [])
        tree = getattr(gui, attr, None)
        if tree is None and key == "selected_total_rows":
            tree = getattr(gui, "pm_total_tree", None)
        if rows:
            _write_dict_rows(tree, rows, list(columns) if columns else None)
            restored_linked = True
        else:
            _clear_tree(tree)
    try:
        gui._update_progress_widgets()
    except Exception:
        pass
    return restored_linked


def _write_plan_tree(gui, rows: list[dict[str, Any]], ns: dict[str, Any]) -> None:
    tree = getattr(gui, "pm_selected_plan_tree", None)
    if tree is None:
        return
    tree.configure(columns=PLAN_COLUMNS, show="headings")
    for col in PLAN_COLUMNS:
        tree.heading(col, text=col)
        tree.column(col, width=PLAN_WIDTHS.get(col, 130), minwidth=50, anchor="w", stretch=False)
    kids = list(tree.get_children())
    if kids:
        tree.delete(*kids)
    for row in rows:
        tree.insert("", "end", values=[str(row.get(col, "") or "") for col in PLAN_COLUMNS])
    bind_editor = _get(ns, "_v254_bind_selected_plan_editor")
    if callable(bind_editor):
        try:
            bind_editor(gui)
        except Exception:
            pass


def _lookup(gui, name: str, ns: dict[str, Any]) -> tuple[float, float]:
    if not str(name or "").strip():
        return 0.0, 0.0
    for fn_name in ("_v29_material_lookup", "_v251_lookup", "_v248_lookup"):
        fn = _get(ns, fn_name)
        if callable(fn):
            try:
                mw, density = fn(gui, name)
                return _num(mw), _num(density)
            except Exception:
                pass
    return 0.0, 0.0


def _is_liquid(gui, name: str, cls: str, density: float, ns: dict[str, Any]) -> bool:
    fn = _get(ns, "_v222_is_liquid_gui") or _get(ns, "_v221_is_liquid_gui")
    if callable(fn):
        try:
            return bool(fn(name, cls, "", ""))
        except Exception:
            pass
    key = re.sub(r"[^a-z0-9]+", "", str(name or "").lower())
    return key in {
        "dic", "diea", "dipea", "dmf", "dcm", "mcdcm", "nmp", "tfa", "tis",
        "edt", "water", "h2o", "piperidine", "ac2o", "aceticanhydride", "tea",
        "triethylamine", "pyridine", "thioanisole", "anisole", "dmso", "dms",
    } or (density > 0 and key in {"aceticacid", "tfe", "methanol", "meoh"})


def _amount(gui, name: str, cls: str, mmol: float, mw: float, density: float, ns: dict[str, Any]) -> str:
    if mmol <= 0 or mw <= 0:
        return ""
    grams = mmol * mw / 1000.0
    if _is_liquid(gui, name, cls, density, ns) and density > 0:
        return f"{_fmt(grams / density)} mL"
    return f"{_fmt(grams)} g"


def _stable_plan_rows(gui, inp, ns: dict[str, Any]) -> list[dict[str, Any]]:
    from spps_planner.engine import generate_step_reagent_plan, working_volume_mL

    plan = generate_step_reagent_plan(inp)
    rows: list[dict[str, Any]] = []
    working_ml = _num(working_volume_mL(inp), 0.0)
    for _, r in plan.iterrows():
        unit = str(r.get("protected_reagent", "") or r.get("unit", "") or "").strip()
        unit_cls = str(r.get("reagent_class", "") or "")
        unit_mw = _num(r.get("reagent_mw"), 0.0)
        _, unit_density = _lookup(gui, unit, ns)
        unit_mmol = _num(r.get("planned_reagent_mmol"), 0.0)

        repeat = max(0, int(round(_num(r.get("coupling_repeat"), 0.0))))
        scale = _num(getattr(inp, "scale_mmol", 0.0), 0.0)

        r1 = str(r.get("coupling_reagent", "") or "").strip()
        r1_eq = _num(r.get("coupling_reagent_eq"), 0.0)
        r1_count = max(0, int(round(_num(r.get("coupling_reagent_count"), 0.0))))
        r1_mmol = scale * r1_eq * r1_count * repeat if r1 else 0.0
        r1_mw, r1_den = _lookup(gui, r1, ns)

        r2 = str(r.get("catalyst", "") or r.get("additive", "") or "").strip()
        r2_eq = _num(r.get("catalyst_eq"), 0.0)
        r2_count = max(0, int(round(_num(r.get("catalyst_count"), 0.0))))
        r2_mmol = scale * r2_eq * r2_count * repeat if r2 else 0.0
        r2_mw, r2_den = _lookup(gui, r2, ns)

        base = str(r.get("base", "") or "").strip()
        base_eq = _num(r.get("base_eq"), 0.0)
        base_count = max(0, int(round(_num(r.get("base_count"), 0.0))))
        base_mmol = scale * base_eq * base_count * repeat if base else 0.0
        base_mw, base_den = _lookup(gui, base, ns)

        solvent = str(r.get("reaction_solvent", "") or "").strip()
        solvent_ml = working_ml * repeat if solvent and repeat > 0 else 0.0
        phase = str(r.get("phase", "") or "")
        note = str(r.get("note", "") or "")
        if phase and phase not in note:
            note = f"{phase}: {note}" if note else phase

        rows.append({
            "No": _fmt(r.get("step", "")),
            "Unit name": unit,
            "MW": _fmt(unit_mw),
            "Density(g/mL)": _fmt(unit_density),
            "Unit mmol": _fmt(unit_mmol),
            "Unit amount": _amount(gui, unit, unit_cls, unit_mmol, unit_mw, unit_density, ns),
            "Reagent 1": r1,
            "R1 MW": _fmt(r1_mw),
            "R1 Density": _fmt(r1_den),
            "R1 mmol": _fmt(r1_mmol),
            "R1 amount": _amount(gui, r1, "Coupling reagent", r1_mmol, r1_mw, r1_den, ns),
            "Reagent 2 / catalyst": r2,
            "R2 MW": _fmt(r2_mw),
            "R2 Density": _fmt(r2_den),
            "R2 mmol": _fmt(r2_mmol),
            "R2 amount": _amount(gui, r2, "Catalyst/additive", r2_mmol, r2_mw, r2_den, ns),
            "Base": base,
            "Base MW": _fmt(base_mw),
            "Base Density": _fmt(base_den),
            "Base mmol": _fmt(base_mmol),
            "Base amount": _amount(gui, base, "Base", base_mmol, base_mw, base_den, ns),
            "Coupling solvent": solvent,
            "Solvent mL": _fmt(solvent_ml),
            "Repeat": _fmt(repeat),
            "Note": note,
        })
    return rows


def _write_checklist_from_operations(gui, operations: pd.DataFrame) -> None:
    tree = getattr(gui, "progress_tree", None)
    if tree is None:
        return
    cols = ["line", "done", "checked_at", "operation", "unit", "next_step", "note"]
    tree.configure(columns=cols, show="headings")
    widths = {"line": 70, "done": 80, "checked_at": 145, "operation": 250, "unit": 160, "next_step": 230, "note": 520}
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=widths.get(c, 130), anchor="w", stretch=False)
    kids = list(tree.get_children())
    if kids:
        tree.delete(*kids)
    op_rows = list(operations.fillna("").to_dict("records")) if operations is not None else []
    for i, r in enumerate(op_rows):
        op = str(r.get("operation_group", "") or "")
        detail = str(r.get("operation_detail", "") or "")
        operation = f"{op}: {detail}" if detail else op
        next_step = ""
        if i + 1 < len(op_rows):
            nr = op_rows[i + 1]
            next_step = f"{nr.get('operation_group', '')}: {nr.get('operation_detail', '')}".strip(": ")
        notes = [str(r.get("solution_note", "") or ""), str(r.get("note", "") or "")]
        note = " | ".join(x for x in notes if x)
        tree.insert("", "end", values=[r.get("line", i + 1), "", "", operation, r.get("unit", ""), next_step, note])
    try:
        gui._update_progress_widgets()
    except Exception:
        pass
    txt = getattr(gui, "pm_selected_check_text", None)
    if txt is not None:
        try:
            txt.delete("1.0", "end")
            for r in op_rows:
                txt.insert("end", f"[{r.get('line','')}] Step {r.get('step','')} {r.get('unit','')} - {r.get('operation_group','')}: {r.get('operation_detail','')} | {r.get('solution_note','')}\n")
        except Exception:
            pass


def _save_plan_rows_to_item(gui, index: int | None = None) -> None:
    # Compatibility name retained for older callers; the restored workflow saves
    # every linked output so switching peptide items brings back the full state.
    _save_visible_outputs_to_item(gui, index)


def _save_editor_to_index(gui, index: int, ns: dict[str, Any]) -> None:
    try:
        if not (0 <= int(index) < len(getattr(gui, "pm_items", []))):
            return
    except Exception:
        return
    old_2093 = getattr(gui, "_v2093_active_index", None)
    old_276 = getattr(gui, "_v276_active_index", None)
    try:
        gui._v2093_active_index = int(index)
        gui._v276_active_index = int(index)
        saver = _get(ns, "_v226_save_active") or _get(ns, "_v2093_save_active")
        if callable(saver):
            saver(gui)
        _save_visible_outputs_to_item(gui, int(index))
        refresh_list = _get(ns, "_v2093_refresh_list")
        if callable(refresh_list):
            try:
                refresh_list(gui, [int(index)])
            except Exception:
                pass
    finally:
        # Keep the supplied index authoritative; selection may already point to the next item.
        gui._v2093_active_index = int(index)
        gui._v276_active_index = int(index)
        if old_2093 is None and old_276 is None:
            pass


def _restore_item(gui, index: int, ns: dict[str, Any]) -> None:
    try:
        if not (0 <= int(index) < len(getattr(gui, "pm_items", []))):
            return
    except Exception:
        return
    gui._v227_switching = True
    gui._v226_resin_syncing = True
    try:
        loader = _get(ns, "_v226_load_item_to_editor") or _get(ns, "_v2093_load_item_to_editor")
        if callable(loader):
            loader(gui, int(index))
        gui._v227_active_index = int(index)
        gui._v2093_active_index = int(index)
        gui._v276_active_index = int(index)
    finally:
        gui._v226_resin_syncing = False
        gui._v227_switching = False

    item = gui.pm_items[int(index)]
    restored_linked = _restore_visible_outputs_from_item(gui, item, ns)
    if item.get("selected_plan_rows") and not restored_linked:
        # Older saved sessions may contain only Selected Plan. Rebuild the adjacent
        # tabs once, then keep their per-peptide snapshots from this point forward.
        refresh_visible_links(gui, ns)
        _save_visible_outputs_to_item(gui, int(index))
    try:
        refresh_cleavage(gui, ns)
    except Exception:
        pass


def on_item_select(gui, ns: dict[str, Any], _event=None):
    if getattr(gui, "_v227_switching", False):
        return "break"
    try:
        selected = list(gui.pm_list.curselection())
        if not selected:
            return "break"
        new_index = int(selected[0])
    except Exception:
        return "break"
    old_index = getattr(gui, "_v227_active_index", getattr(gui, "_v2093_active_index", None))
    if old_index is not None and int(old_index) != new_index:
        _save_editor_to_index(gui, int(old_index), ns)
    _restore_item(gui, new_index, ns)
    try:
        gui.schedule_autosave()
    except Exception:
        pass
    return "break"


def _store_generated_rows(gui, rows: list[dict[str, Any]]) -> None:
    idx = getattr(gui, "_v227_active_index", getattr(gui, "_v2093_active_index", None))
    try:
        if idx is not None and 0 <= int(idx) < len(gui.pm_items):
            gui.pm_items[int(idx)]["selected_plan_rows"] = [{c: str(r.get(c, "") or "") for c in PLAN_COLUMNS} for r in rows]
            gui.pm_items[int(idx)]["status"] = "Calculated"
    except Exception:
        pass


def generate(gui, ns: dict[str, Any]):
    """Generate = build/rebuild Selected Plan from editor and setup values."""
    if getattr(gui, "_v227_generate_running", False):
        return None
    gui._v227_generate_running = True
    try:
        idx = getattr(gui, "_v227_active_index", getattr(gui, "_v2093_active_index", None))
        if idx is not None:
            _save_editor_to_index(gui, int(idx), ns)
        plan_input = _get(ns, "_v226_plan_input") or _get(ns, "_v222_plan_input")
        if not callable(plan_input):
            raise RuntimeError("Final PlanInput controller is unavailable.")
        inp = plan_input(gui)
        rows = _stable_plan_rows(gui, inp, ns)
        _write_plan_tree(gui, rows, ns)
        _store_generated_rows(gui, rows)

        # Core engine remains the authoritative source for protocol-order materials,
        # totals and operations; only the operator-facing Selected Plan shape changes.
        core_tables = _get(ns, "_v221_core_tables")
        tables = core_tables(gui)[2] if callable(core_tables) else {}
        writer = _get(ns, "_v2093_write_tree")
        if callable(writer):
            if getattr(gui, "pm_selected_material_tree", None) is not None:
                writer(gui, gui.pm_selected_material_tree, tables.get("selected_materials_core", pd.DataFrame()))
            total_tree = getattr(gui, "pm_selected_total_tree", None) or getattr(gui, "pm_total_tree", None)
            if total_tree is not None:
                writer(gui, total_tree, tables.get("selected_total_materials_visible", pd.DataFrame()))
        _write_checklist_from_operations(gui, tables.get("operations_core", pd.DataFrame()))
        cleavage_df = tables.get("cleavage_cocktail")
        refresh_fn = _get(ns, "_v2093_refresh_cleavage")
        if callable(refresh_fn):
            refresh_fn(gui, cleavage_df)
        if idx is not None:
            _save_visible_outputs_to_item(gui, int(idx))

        try:
            refresh_list = _get(ns, "_v2093_refresh_list")
            if callable(refresh_list) and idx is not None:
                refresh_list(gui, [int(idx)])
        except Exception:
            pass
        try:
            gui.schedule_autosave()
        except Exception:
            pass
        normalize_ui(gui, ns)
        return tables
    except Exception as exc:
        try:
            messagebox.showerror("Generate", str(exc))
        except Exception:
            pass
        return None
    finally:
        gui._v227_generate_running = False


def refresh_visible_links(gui, ns: dict[str, Any]) -> None:
    """Current visible Selected Plan -> Materials, Total, Checklist and Batch."""
    commit = _get(ns, "_v259_commit_open_selected_plan_editor")
    if callable(commit):
        try:
            commit(gui)
        except Exception:
            pass
    refresher = _get(ns, "_v260_refresh_linked_outputs_from_visible_plan") or _get(ns, "_v259_refresh_linked_outputs_from_visible_plan")
    if callable(refresher):
        refresher(gui)
    else:
        # Conservative fallback for older project copies.
        for fn_name in ("_v257_rebuild_materials_total", "_v257_refresh_checklist"):
            fn = _get(ns, fn_name)
            if callable(fn):
                try:
                    fn(gui)
                except Exception:
                    pass


def apply_change(gui, ns: dict[str, Any]):
    """Apply Change = keep the edited Selected Plan and update adjacent tabs."""
    if getattr(gui, "_v227_apply_running", False):
        return None
    gui._v227_apply_running = True
    try:
        refresh_visible_links(gui, ns)
        idx = getattr(gui, "_v227_active_index", getattr(gui, "_v2093_active_index", None))
        if idx is not None:
            _save_editor_to_index(gui, int(idx), ns)
            _save_visible_outputs_to_item(gui, int(idx))
        try:
            gui.schedule_autosave()
        except Exception:
            pass
        normalize_ui(gui, ns)
        return True
    except Exception as exc:
        try:
            messagebox.showerror("Apply Change", str(exc))
        except Exception:
            pass
        return None
    finally:
        gui._v227_apply_running = False


def delete_selected_plan_rows(gui, ns: dict[str, Any]):
    tree = getattr(gui, "pm_selected_plan_tree", None)
    if tree is None:
        return
    for iid in list(tree.selection()):
        try:
            tree.delete(iid)
        except Exception:
            pass
    # Renumber rows without rebuilding the plan.
    cols = list(tree["columns"])
    if "No" in cols:
        ni = cols.index("No")
        for n, iid in enumerate(tree.get_children(), 1):
            vals = list(tree.item(iid, "values"))
            vals += [""] * max(0, len(cols) - len(vals))
            vals[ni] = str(n)
            tree.item(iid, values=vals)
    apply_change(gui, ns)


def edit_unit_name(gui, ns: dict[str, Any]):
    for fn_name in ("_v276c_edit_unit", "_v269_open_unit_picker", "_v239_edit_selected_unit", "_v238_edit_selected_unit", "_v237_edit_selected_unit"):
        fn = _get(ns, fn_name)
        if callable(fn):
            try:
                return fn(gui)
            except Exception:
                continue
    try:
        messagebox.showinfo("Edit Unit name", "Select a row first, or double-click any editable cell.")
    except Exception:
        pass
    return None


def _install_plan_toolbar(gui, ns: dict[str, Any]) -> None:
    tree = getattr(gui, "pm_selected_plan_tree", None)
    if tree is None:
        return
    parent = tree.master
    # Remove legacy duplicate plan-local toolbars/buttons only.  Global Project
    # Manager actions are outside this frame and remain untouched.
    for child in list(parent.winfo_children()):
        if child is tree or isinstance(child, ttk.Scrollbar):
            continue
        try:
            texts = [str(w.cget("text") or "").strip() for w in _walk(child) if isinstance(w, ttk.Button)]
        except Exception:
            texts = []
        if any(t in {"Apply Plan", "Delete selected row", "Edit Unit name", "Edit selected cell", "Append row", "Reset table widths"} for t in texts):
            try:
                child.destroy()
            except Exception:
                pass
    old = getattr(gui, "_v227_plan_toolbar", None)
    try:
        if old is not None and old.winfo_exists():
            old.destroy()
    except Exception:
        pass
    try:
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_rowconfigure(2, weight=0)
        parent.grid_columnconfigure(0, weight=1)
        tree.grid(row=1, column=0, sticky="nsew")
        for child in parent.winfo_children():
            if isinstance(child, ttk.Scrollbar):
                orient = str(child.cget("orient")).lower()
                if orient == "vertical":
                    child.grid(row=1, column=1, sticky="ns")
                elif orient == "horizontal":
                    child.grid(row=2, column=0, sticky="ew")
    except Exception:
        pass
    bar = ttk.Frame(parent)
    gui._v227_plan_toolbar = bar
    bar.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 2))
    # Restore the compact V2.1.7 toolbar. Every editable column still supports
    # double-click editing; the explicit Unit-name action remains available.
    ttk.Button(bar, text="Delete selected row", command=lambda: delete_selected_plan_rows(gui, ns)).pack(side="left", padx=(0, 4))
    ttk.Button(bar, text="Edit Unit name", command=lambda: edit_unit_name(gui, ns)).pack(side="left", padx=(0, 4))
    bind_editor = _get(ns, "_v254_bind_selected_plan_editor")
    if callable(bind_editor):
        try:
            bind_editor(gui)
        except Exception:
            pass


def refresh_cleavage(gui, ns: dict[str, Any]):
    # Keep the legacy AUTO/manual preset semantics. Only the broken resin-name
    # combobox values are replaced; the selected cocktail remains per peptide.
    saver = _get(ns, "_v226_save_active") or _get(ns, "_v2093_save_active")
    if callable(saver):
        try:
            saver(gui)
        except Exception:
            pass
    fn = _get(ns, "_v2093_refresh_cleavage")
    result = fn(gui) if callable(fn) else None
    idx = getattr(gui, "_v227_active_index", getattr(gui, "_v2093_active_index", None))
    if idx is not None:
        _save_visible_outputs_to_item(gui, int(idx))
    return result


def _install_cleavage_controls(gui, ns: dict[str, Any]) -> None:
    tree = getattr(gui, "pm_cleavage_tree", None)
    if tree is None:
        ensure = _get(ns, "_v2093_ensure_cleavage_tab")
        if callable(ensure):
            tree = ensure(gui)
    if tree is None:
        return
    frame = tree.master
    old = getattr(gui, "_v227_cleavage_controls", None)
    try:
        if old is not None and old.winfo_exists():
            old.destroy()
    except Exception:
        pass
    # Remove duplicate old control rows, preserving tree/scrollbars.
    for child in list(frame.winfo_children()):
        if child is tree or isinstance(child, ttk.Scrollbar):
            continue
        if isinstance(child, ttk.Frame):
            try:
                child.destroy()
            except Exception:
                pass
    try:
        current = str(gui.cleavage_preset.get() or "").strip()
        if current not in CLEAVAGE_PRESETS:
            gui.cleavage_preset.set("AUTO")
    except Exception:
        pass
    ctl = ttk.Frame(frame)
    gui._v227_cleavage_controls = ctl
    ctl.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
    ttk.Label(ctl, text="Eq override (0=auto)").pack(side="left", padx=(0, 2))
    ttk.Entry(ctl, textvariable=gui.cleavage_eq_override, width=8).pack(side="left", padx=(0, 8))
    ttk.Label(ctl, text="Preset").pack(side="left", padx=(0, 2))
    combo = ttk.Combobox(ctl, textvariable=gui.cleavage_preset, values=CLEAVAGE_PRESETS, width=28, state="readonly")
    combo.pack(side="left", padx=(0, 8))
    ttk.Label(ctl, text="Custom components").pack(side="left", padx=(0, 2))
    ttk.Entry(ctl, textvariable=gui.cleavage_components_text, width=42).pack(side="left", padx=(0, 8), fill="x", expand=True)
    ttk.Button(ctl, text="Apply cleavage", command=lambda: refresh_cleavage(gui, ns)).pack(side="left")
    try:
        combo.bind("<<ComboboxSelected>>", lambda _e: None, add=False)
    except Exception:
        pass
    try:
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        tree.grid(row=1, column=0, sticky="nsew")
        for child in frame.winfo_children():
            if isinstance(child, ttk.Scrollbar):
                orient = str(child.cget("orient")).lower()
                if orient == "vertical":
                    child.grid(row=1, column=1, sticky="ns")
                elif orient == "horizontal":
                    child.grid(row=2, column=0, sticky="ew")
    except Exception:
        pass



def export_outputs(gui, ns: dict[str, Any]):
    """Export the current visible/edited Project Manager state without regenerating it."""
    from pathlib import Path
    import json
    from datetime import datetime

    try:
        if not _tree_rows(getattr(gui, "pm_selected_plan_tree", None)):
            generate(gui, ns)
        idx = getattr(gui, "_v227_active_index", getattr(gui, "_v2093_active_index", None))
        if idx is not None:
            _save_editor_to_index(gui, int(idx), ns)
            _save_plan_rows_to_item(gui, int(idx))

        plan_input = _get(ns, "_v226_plan_input") or _get(ns, "_v222_plan_input")
        inp = plan_input(gui) if callable(plan_input) else None
        try:
            out_text = gui.project_outdir.get() if hasattr(gui, "project_outdir") else ""
            if not str(out_text or "").strip() and hasattr(gui, "outdir"):
                out_text = gui.outdir.get()
            out = Path(str(out_text or "").strip() or "outputs/project_manager_exports")
        except Exception:
            out = Path("outputs/project_manager_exports")
        out.mkdir(parents=True, exist_ok=True)

        if inp is not None:
            try:
                from spps_planner.export import export_csvs, export_excel
                export_csvs(inp, out / "core_engine_outputs")
                export_excel(inp, out / "spps_plan_core_engine.xlsx")
            except Exception:
                pass

        visible_plan = pd.DataFrame(_tree_rows(getattr(gui, "pm_selected_plan_tree", None)))
        visible_mats = pd.DataFrame(_tree_rows(getattr(gui, "pm_selected_material_tree", None)))
        total_tree = getattr(gui, "pm_selected_total_tree", None) or getattr(gui, "pm_total_tree", None)
        visible_total = pd.DataFrame(_tree_rows(total_tree))
        visible_check = pd.DataFrame(_tree_rows(getattr(gui, "progress_tree", None)))
        visible_cleavage = pd.DataFrame(_tree_rows(getattr(gui, "pm_cleavage_tree", None)))
        try:
            from spps_planner.engine import cleavage_cocktail_presets, validate_plan, plan_summary
            presets = cleavage_cocktail_presets()
            validation = validate_plan(inp) if inp is not None else pd.DataFrame()
            summary = pd.DataFrame([plan_summary(inp)]) if inp is not None else pd.DataFrame()
        except Exception:
            presets = validation = summary = pd.DataFrame()

        item = {}
        try:
            if idx is not None and 0 <= int(idx) < len(gui.pm_items):
                item = dict(gui.pm_items[int(idx)])
        except Exception:
            pass
        editor_summary = pd.DataFrame([{
            "app_version": VERSION,
            "project": item.get("project", ""),
            "peptide": item.get("peptide", ""),
            "sequence": item.get("sequence", ""),
            "scale": item.get("scale", ""),
            "resin": item.get("resin", ""),
            "loading": item.get("loading", ""),
            "lot": item.get("lot", item.get("lot_no", "")),
            "chemistry": item.get("chemistry", ""),
            "copies": item.get("copies", ""),
            "cleavage_preset": item.get("cleavage_preset", ""),
        }])

        xlsx = out / "project_manager_selected_outputs_v2.2.7.xlsx"
        with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
            editor_summary.to_excel(writer, index=False, sheet_name="00_EDITOR_SUMMARY")
            visible_plan.to_excel(writer, index=False, sheet_name="01_SELECTED_PLAN_VISIBLE")
            visible_mats.to_excel(writer, index=False, sheet_name="02_SELECTED_MATERIALS_STEP")
            visible_total.to_excel(writer, index=False, sheet_name="03_SELECTED_TOTAL_MATERIALS")
            visible_check.to_excel(writer, index=False, sheet_name="04_SELECTED_CHECKLIST")
            visible_cleavage.to_excel(writer, index=False, sheet_name="05_CLEAVAGE_COCKTAIL")
            presets.to_excel(writer, index=False, sheet_name="06_CLEAVAGE_PRESETS")
            validation.to_excel(writer, index=False, sheet_name="07_VALIDATION")
            summary.to_excel(writer, index=False, sheet_name="08_SUMMARY")

        for filename, df in (
            ("01_SELECTED_PLAN_VISIBLE.csv", visible_plan),
            ("02_SELECTED_MATERIALS_STEP.csv", visible_mats),
            ("03_SELECTED_TOTAL_MATERIALS.csv", visible_total),
            ("04_SELECTED_CHECKLIST.csv", visible_check),
            ("05_CLEAVAGE_COCKTAIL.csv", visible_cleavage),
        ):
            df.to_csv(out / filename, index=False, encoding="utf-8-sig")

        state = {
            "app_version": VERSION,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "active_index": idx,
            "pm_items": list(getattr(gui, "pm_items", []) or []),
            "visible_selected_plan_source": "current edited TreeView; no regeneration during export",
        }
        (out / "project_manager_state_v2.2.7.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        gui.last_outdir = out
        try:
            messagebox.showinfo("Export complete", f"CSV/XLSX exported to:\n{out}")
        except Exception:
            pass
        return xlsx
    except Exception as exc:
        try:
            messagebox.showerror("Export error", str(exc))
        except Exception:
            pass
        return None

def _install_editor_actions(gui, ns: dict[str, Any]) -> None:
    buttons = []
    for w in _walk(gui):
        if isinstance(w, ttk.Button):
            try:
                text = str(w.cget("text") or "").strip()
            except Exception:
                continue
            if text in {"Generate", "Generate / Update", "Generate / Update Plan", "Apply Change", "Apply Plan", "Save Session Now"}:
                buttons.append((w, text))

    save_candidates = [w for w, t in buttons if t == "Save Session Now"]
    save_button = next((w for w in save_candidates if w.winfo_ismapped()), None) or (save_candidates[0] if save_candidates else None)
    parent = getattr(save_button, "master", None)
    generate_candidates = [w for w, t in buttons if t in {"Generate", "Generate / Update", "Generate / Update Plan"}]
    generate_button = next((w for w in generate_candidates if parent is not None and getattr(w, "master", None) is parent), None)
    if generate_button is None:
        generate_button = next((w for w in generate_candidates if w.winfo_ismapped()), None) or (generate_candidates[0] if generate_candidates else None)
    if parent is None:
        parent = getattr(generate_button, "master", None)
    if parent is None:
        return

    # Remove every old Apply/Generate duplicate from the action row, then repack
    # exactly Generate -> Apply Change -> Save Session Now.
    for w, text in buttons:
        if getattr(w, "master", None) is not parent:
            continue
        try:
            w.pack_forget()
        except Exception:
            try:
                w.grid_remove()
            except Exception:
                pass

    if generate_button is None or not generate_button.winfo_exists():
        generate_button = ttk.Button(parent, text="Generate")
    generate_button.configure(text="Generate", command=lambda _g=gui: generate(_g, ns))

    apply_button = getattr(gui, "_v227_apply_change_button", None)
    try:
        valid_apply = apply_button is not None and apply_button.winfo_exists() and apply_button.master is parent
    except Exception:
        valid_apply = False
    if not valid_apply:
        apply_button = next((w for w, t in buttons if t in {"Apply Change", "Apply Plan"} and getattr(w, "master", None) is parent), None)
    if apply_button is None:
        apply_button = ttk.Button(parent)
    gui._v227_apply_change_button = apply_button
    apply_button.configure(text="Apply Change", command=lambda _g=gui: apply_change(_g, ns))

    generate_button.pack(side="left", padx=(0, 4))
    apply_button.pack(side="left", padx=(0, 4))
    if save_button is not None and save_button.winfo_exists():
        save_button.pack(side="left", padx=(0, 4))


def _bind_buttons(gui, ns: dict[str, Any]) -> None:
    for w in _walk(gui):
        if not isinstance(w, ttk.Button):
            continue
        try:
            text = str(w.cget("text") or "").strip()
        except Exception:
            continue
        try:
            if text in {"Generate / Update", "Generate / Update Plan", "Generate"}:
                w.configure(text="Generate", command=lambda _g=gui: generate(_g, ns))
            elif text == "Apply Change":
                w.configure(command=lambda _g=gui: apply_change(_g, ns))
            elif text == "Apply cleavage":
                w.configure(command=lambda _g=gui: refresh_cleavage(_g, ns))
            elif text == "Export":
                w.configure(command=lambda _g=gui: export_outputs(_g, ns))
        except Exception:
            pass


def normalize_ui(gui, ns: dict[str, Any]) -> None:
    try:
        gui.title(TITLE)
    except Exception:
        pass
    for w in _walk(gui):
        try:
            if isinstance(w, ttk.Label) and str(w.cget("text") or "").startswith("SPPS Planner GitHub"):
                w.configure(text=TITLE)
        except Exception:
            pass
    _bind_buttons(gui, ns)
    _install_editor_actions(gui, ns)
    _install_plan_toolbar(gui, ns)
    _install_cleavage_controls(gui, ns)
    try:
        gui.pm_list.bind("<<ListboxSelect>>", lambda e, _g=gui: on_item_select(_g, ns, e), add=False)
        gui.pm_list.bind("<Return>", lambda e, _g=gui: on_item_select(_g, ns, e), add=False)
    except Exception:
        pass


def install(gui_cls, ns: dict[str, Any]) -> None:
    """Install the final non-destructive controller after all legacy layers load."""
    previous_build = gui_cls._build

    def build(gui):
        previous_build(gui)
        # Establish an index that does not depend on the Listbox's next selection.
        try:
            selected = list(gui.pm_list.curselection())
            index = int(selected[0]) if selected else 0
        except Exception:
            index = 0
        gui._v227_active_index = index
        try:
            _restore_item(gui, index, ns)
        except Exception:
            pass
        normalize_ui(gui, ns)
        # Historical layers schedule delayed rebindings.  Reassert only this final
        # controller after those callbacks without generating or deleting data.
        for delay in (80, 250, 700, 1500):
            try:
                gui.after(delay, lambda _g=gui: normalize_ui(_g, ns))
            except Exception:
                pass

    gui_cls._build = build
    gui_cls.generate_update_plan = lambda self, *a, **k: generate(self, ns)
    gui_cls.pm_generate_selected = lambda self, *a, **k: generate(self, ns)
    gui_cls.pm_calculate_all = lambda self, *a, **k: generate(self, ns)
    gui_cls.apply_change = lambda self, *a, **k: apply_change(self, ns)
    gui_cls.pm_apply_change = lambda self, *a, **k: apply_change(self, ns)
    gui_cls.apply_plan_mw_density = lambda self, *a, **k: apply_change(self, ns)
    gui_cls.pm_on_select = lambda self, event=None: on_item_select(self, ns, event)
    gui_cls.export_outputs = lambda self, *a, **k: export_outputs(self, ns)
