"""V2.2.9 exact legacy workflow restoration.

This controller keeps the proven classic layout but removes the stacked-patch
behaviour that caused startup samples, duplicate loading controls, broken eq
visibility, and Apply Change not propagating edited units.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

from suite_gui.modules import v228_fast_legacy_exact_workflow as v228

VERSION = "V2.0.0"
TITLE = "SPPS Planner V2.0.0"

PLAN_COLUMNS = [
    "No", "Unit name", "MW", "Density(g/mL)", "Unit eq", "Unit mmol", "Unit amount",
    "Reagent 1", "R1 eq", "R1 MW", "R1 Density", "R1 mmol", "R1 amount",
    "Reagent 2 / catalyst", "R2 eq", "R2 MW", "R2 Density", "R2 mmol", "R2 amount",
    "Base", "Base eq", "Base MW", "Base Density", "Base mmol", "Base amount",
    "Coupling solvent", "Solvent mL", "Repeat", "Note",
]
PLAN_WIDTHS = {
    "No": 50, "Unit name": 280, "MW": 85, "Density(g/mL)": 105,
    "Unit eq": 80, "Unit mmol": 95, "Unit amount": 115,
    "Reagent 1": 120, "R1 eq": 75, "R1 MW": 80, "R1 Density": 95,
    "R1 mmol": 95, "R1 amount": 110,
    "Reagent 2 / catalyst": 170, "R2 eq": 75, "R2 MW": 80, "R2 Density": 95,
    "R2 mmol": 95, "R2 amount": 110,
    "Base": 110, "Base eq": 75, "Base MW": 80, "Base Density": 95,
    "Base mmol": 95, "Base amount": 110,
    "Coupling solvent": 160, "Solvent mL": 95, "Repeat": 70, "Note": 430,
}

MATERIAL_COLUMNS = list(v228.MATERIAL_COLUMNS)
MATERIAL_WIDTHS = dict(v228.MATERIAL_WIDTHS)
TOTAL_COLUMNS = list(v228.TOTAL_COLUMNS)
TOTAL_WIDTHS = dict(v228.TOTAL_WIDTHS)
CHECK_COLUMNS = list(v228.CHECK_COLUMNS)
CHECK_WIDTHS = dict(v228.CHECK_WIDTHS)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(str(value).replace(",", "").replace("mL", "").replace("ml", "").replace("g", "").strip())
    except Exception:
        return default


def _fmt(value: Any, digits: int = 6) -> str:
    try:
        number = float(value)
    except Exception:
        return "" if value is None else str(value)
    if abs(number) < 1e-12:
        return ""
    if abs(number - round(number)) < 1e-10:
        return str(int(round(number)))
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def _var(gui, name: str, default: Any = "") -> Any:
    value = getattr(gui, name, None)
    try:
        return value.get()
    except Exception:
        return default


def _set(gui, name: str, value: Any) -> None:
    try:
        getattr(gui, name).set(value)
    except Exception:
        pass


def _active_index(gui) -> int | None:
    value = getattr(gui, "_v229_active_index", None)
    try:
        value = int(value)
        if 0 <= value < len(gui.pm_items):
            return value
    except Exception:
        pass
    return None


def _lookup(gui, ns: dict[str, Any], name: str) -> tuple[float, float]:
    if not str(name or "").strip():
        return 0.0, 0.0
    for fn_name in ("_v251_lookup", "_v248_lookup", "_v216_lookup_mw_density", "_v29_material_lookup"):
        fn = ns.get(fn_name)
        if callable(fn):
            try:
                mw, density = fn(gui, name)
                mwf, denf = _num(mw), _num(density)
                if mwf or denf:
                    return mwf, denf
            except Exception:
                pass
    key = re.sub(r"[^a-z0-9]+", "", str(name).lower())
    fallback = {
        "aceticanhydrideac2ofornterminalacetylation": (102.09, 1.08),
        "aceticanhydrideac2o": (102.09, 1.08), "ac2o": (102.09, 1.08),
        "dic": (126.20, 0.815), "diea": (129.25, 0.742), "dipea": (129.25, 0.742),
        "hobt": (135.13, 0.0), "hobtanhydrous": (135.13, 0.0),
        "dmf": (73.09, 0.944), "dcm": (84.93, 1.325), "mcdcm": (84.93, 1.325),
        "nmp": (99.13, 1.03), "piperidine": (85.15, 0.862),
    }
    return fallback.get(key, (0.0, 0.0))


def _is_liquid(name: str, density: float) -> bool:
    key = re.sub(r"[^a-z0-9]+", "", str(name or "").lower())
    return density > 0 and key in {
        "aceticanhydrideac2ofornterminalacetylation", "aceticanhydrideac2o", "ac2o",
        "dic", "diea", "dipea", "dmf", "dcm", "mcdcm", "nmp", "piperidine",
        "tfa", "tis", "water", "dwwater", "acoh", "tfe", "methanol", "meoh",
    }


def _amount(name: str, mmol: float, mw: float, density: float) -> str:
    if mmol <= 0 or mw <= 0:
        return ""
    grams = mmol * mw / 1000.0
    if _is_liquid(name, density) and density > 0:
        return f"{_fmt(grams / density, 4)} mL"
    return f"{_fmt(grams, 4)} g"


def _canonical(ns: dict[str, Any], value: str) -> str:
    raw = str(value or "").strip()
    simple = re.sub(r"[^a-z0-9]+", "", raw.lower())
    # Preserve the operator-facing names used by the established legacy UI.
    if simple in {"hobt", "hobtanhydrous"}:
        return "HOBt"
    if simple == "dic":
        return "DIC"
    if simple in {"diea", "dipea"}:
        return "DIEA"
    fn = ns.get("_v251_canon")
    if callable(fn):
        try:
            return str(fn(raw))
        except Exception:
            pass
    return raw


def _unit_options(gui, ns: dict[str, Any], column: str) -> list[str]:
    fn = ns.get("_v251_options_for_col") or ns.get("_v249_options_for_col")
    if callable(fn):
        try:
            return list(fn(gui, column))
        except Exception:
            pass
    return []


def _sequence_aa_eq(gui) -> float:
    seq = str(_var(gui, "pm_sequence", "") or "").strip()
    default_eq = _num(_var(gui, "coupling_eq", 5), 5.0)
    try:
        from spps_planner.parser import parse_sequence
        parsed = parse_sequence(seq)
        count = len(list(parsed.core_tokens or []))
    except Exception:
        count = len([x for x in re.split(r"[-\s]+", seq) if x and x.upper() not in {"AC", "NH2", "OH"}])
    return 2.0 if 0 < count <= 5 else default_eq


def _is_ac2o(unit: str) -> bool:
    key = re.sub(r"[^a-z0-9]+", "", str(unit or "").lower())
    return key in {"ac", "ac2o", "aceticanhydride", "aceticanhydrideac2o", "aceticanhydrideac2ofornterminalacetylation"}


def _is_fmoc(unit: str) -> bool:
    return str(unit or "").strip().lower().startswith("fmoc-")


def _is_ac_aa_oh(unit: str) -> bool:
    """Return True for an N-acetyl amino-acid coupling unit, not Ac2O."""
    text = str(unit or "").strip().lower()
    return text.startswith("ac-") and text.endswith("-oh") and "acetic anhydride" not in text and "ac2o" not in text


def _is_terminal_chemical(unit: str) -> bool:
    text = str(unit or "").strip().lower()
    if not text:
        return False
    return not text.startswith("fmoc-")


def _build_plan_input(gui, ns: dict[str, Any]):
    seq = str(_var(gui, "pm_sequence", "") or "").strip()
    if not seq:
        raise ValueError("Sequence is empty. Enter a sequence before Generate or Apply Change.")
    base_fn = ns.get("_v226_plan_input") or ns.get("_v222_plan_input") or ns.get("_v218_plan_input")
    if not callable(base_fn):
        raise RuntimeError("PlanInput controller is unavailable.")
    base = base_fn(gui)
    follows = bool(_var(gui, "reagent_eq_follows_coupling_eq", True))
    chemistry = str(_var(gui, "pm_chemistry", "") or "").upper()

    reagent_name = str(getattr(base, "default_coupling_reagent", "") or "")
    reagent_eq = _num(_var(gui, "default_reagent_eq", 5), 5.0)
    reagent_count = max(0, int(round(_num(_var(gui, "default_reagent_count", 1), 1))))
    catalyst_name = str(getattr(base, "default_catalyst", "") or "")
    catalyst_eq = _num(_var(gui, "default_catalyst_eq", 5), 5.0)
    catalyst_count = max(0, int(round(_num(_var(gui, "default_catalyst_count", 1), 1))))
    base_name = str(getattr(base, "default_base", "") or "")
    base_eq = _num(_var(gui, "default_base_eq", 0), 0.0)
    base_count = max(0, int(round(_num(_var(gui, "default_base_count", 0), 0))))
    reaction_solvent = str(getattr(base, "default_reaction_solvent", "") or "DMF")

    if "HBTU" in chemistry and "10EQ" in chemistry:
        follows = False
        reagent_name, reagent_eq, reagent_count = "HBTU", 10.0, 1
        catalyst_name, catalyst_eq, catalyst_count = "", 0.0, 0
        base_name, base_eq, base_count = "DIEA", 5.0, 1
        reaction_solvent = "NMP"

    return replace(
        base,
        sequence=seq,
        scale_mmol=_num(_var(gui, "pm_scale", 0), 0.0),
        resin=str(_var(gui, "pm_resin", "") or "Rink Amide AM"),
        resin_loading_mmol_g=_num(_var(gui, "pm_loading", 0), 0.0),
        coupling_eq=_num(_var(gui, "coupling_eq", 5), 5.0),
        ac_eq=_num(_var(gui, "modifier_eq", 3), 3.0),
        default_coupling_reagent=reagent_name,
        default_reagent_eq=reagent_eq,
        default_reagent_count=reagent_count,
        default_catalyst=catalyst_name,
        default_catalyst_eq=catalyst_eq,
        default_catalyst_count=catalyst_count,
        default_base=base_name,
        default_base_eq=base_eq,
        default_base_count=base_count,
        default_reaction_solvent=reaction_solvent,
        reagent_eq_follows_coupling_eq=follows,
        auto_short_peptide_eq=True,
        short_peptide_max_len=5,
        short_peptide_coupling_eq=2.0,
        cleavage_preset=str(_var(gui, "cleavage_preset", "") or ""),
        cleavage_components_text=str(_var(gui, "cleavage_components_text", "") or ""),
        cleavage_eq_override=_num(_var(gui, "cleavage_eq_override", 0), 0.0),
        apply_resin_loading=bool(_var(gui, "apply_loading_calc", False)),
    )


def _generated_plan_rows(gui, ns: dict[str, Any], inp) -> list[dict[str, Any]]:
    from spps_planner.engine import generate_step_reagent_plan, working_volume_mL
    frame = generate_step_reagent_plan(inp)
    rows: list[dict[str, Any]] = []
    for _, record in frame.iterrows():
        repeat = max(1, int(round(_num(record.get("coupling_repeat"), 1))))
        unit = str(record.get("protected_reagent", "") or record.get("unit", "") or "").strip()
        unit_eq = _num(record.get("reagent_eq"), 0.0)
        unit_mmol = _num(record.get("planned_reagent_mmol"), 0.0)
        unit_mw = _num(record.get("reagent_mw"), 0.0)
        _, unit_den = _lookup(gui, ns, unit)

        r1 = str(record.get("coupling_reagent", "") or "").strip()
        r1_eq = _num(record.get("coupling_reagent_eq"), 0.0)
        r1_count = max(0, int(round(_num(record.get("coupling_reagent_count"), 0))))
        r1_mmol = inp.scale_mmol * r1_eq * r1_count * repeat if r1 else 0.0
        r1_mw, r1_den = _lookup(gui, ns, r1)

        r2 = str(record.get("catalyst", "") or record.get("additive", "") or "").strip()
        r2_eq = _num(record.get("catalyst_eq"), 0.0)
        r2_count = max(0, int(round(_num(record.get("catalyst_count"), 0))))
        r2_mmol = inp.scale_mmol * r2_eq * r2_count * repeat if r2 else 0.0
        r2_mw, r2_den = _lookup(gui, ns, r2)

        base = str(record.get("base", "") or "").strip()
        base_eq = _num(record.get("base_eq"), 0.0)
        base_count = max(0, int(round(_num(record.get("base_count"), 0))))
        base_mmol = inp.scale_mmol * base_eq * base_count * repeat if base else 0.0
        base_mw, base_den = _lookup(gui, ns, base)

        solvent = str(record.get("reaction_solvent", "") or "").strip()
        solvent_ml = working_volume_mL(inp) * repeat if solvent else 0.0
        phase = str(record.get("phase", "") or "")
        note = str(record.get("note", "") or "")
        if phase and phase.lower() not in note.lower():
            note = f"{phase}: {note}" if note else phase
        rows.append({
            "No": _fmt(record.get("step", "")),
            "Unit name": unit, "MW": _fmt(unit_mw), "Density(g/mL)": _fmt(unit_den),
            "Unit eq": _fmt(unit_eq), "Unit mmol": _fmt(unit_mmol),
            "Unit amount": _amount(unit, unit_mmol, unit_mw, unit_den),
            "Reagent 1": r1, "R1 eq": _fmt(r1_eq), "R1 MW": _fmt(r1_mw), "R1 Density": _fmt(r1_den),
            "R1 mmol": _fmt(r1_mmol), "R1 amount": _amount(r1, r1_mmol, r1_mw, r1_den),
            "Reagent 2 / catalyst": r2, "R2 eq": _fmt(r2_eq), "R2 MW": _fmt(r2_mw), "R2 Density": _fmt(r2_den),
            "R2 mmol": _fmt(r2_mmol), "R2 amount": _amount(r2, r2_mmol, r2_mw, r2_den),
            "Base": base, "Base eq": _fmt(base_eq), "Base MW": _fmt(base_mw), "Base Density": _fmt(base_den),
            "Base mmol": _fmt(base_mmol), "Base amount": _amount(base, base_mmol, base_mw, base_den),
            "Coupling solvent": solvent, "Solvent mL": _fmt(solvent_ml), "Repeat": str(repeat), "Note": note,
        })
    return rows


def _row_dict(tree, iid) -> dict[str, str]:
    columns = list(tree["columns"])
    values = list(tree.item(iid, "values"))
    values += [""] * max(0, len(columns) - len(values))
    return {column: str(values[i] if i < len(values) else "") for i, column in enumerate(columns)}


def _write_row(tree, iid, row: dict[str, Any]) -> None:
    tree.item(iid, values=[str(row.get(column, "") or "") for column in tree["columns"]])


def _chemistry_defaults(gui, ns, inp, unit: str) -> dict[str, Any]:
    if _is_ac2o(unit):
        return {
            "unit_eq": _num(_var(gui, "modifier_eq", 3), 3.0),
            "r1": "", "r1_eq": 0.0, "r2": "", "r2_eq": 0.0,
            "base": "DIEA", "base_eq": _num(_var(gui, "default_base_eq", 5), 5.0) or 5.0,
            "solvent": str(_var(gui, "default_coupling_solution_solvent", "DMF") or "DMF"),
        }
    unit_eq = _sequence_aa_eq(gui) if _is_fmoc(unit) else _num(_var(gui, "modifier_eq", 3), 3.0)
    follows = bool(getattr(inp, "reagent_eq_follows_coupling_eq", True))
    chemistry = str(_var(gui, "pm_chemistry", "") or "").upper()
    r1_eq = unit_eq if follows else _num(getattr(inp, "default_reagent_eq", 0), 0.0)
    r2_eq = unit_eq if follows else _num(getattr(inp, "default_catalyst_eq", 0), 0.0)
    base_eq = unit_eq if follows else _num(getattr(inp, "default_base_eq", 0), 0.0)
    if "10EQ" in chemistry:
        r1_eq = _num(getattr(inp, "default_reagent_eq", 10), 10.0)
        r2_eq = _num(getattr(inp, "default_catalyst_eq", 0), 0.0)
        base_eq = _num(getattr(inp, "default_base_eq", 5), 5.0)
    return {
        "unit_eq": unit_eq,
        "r1": str(getattr(inp, "default_coupling_reagent", "") or ""), "r1_eq": r1_eq,
        "r2": str(getattr(inp, "default_catalyst", "") or ""), "r2_eq": r2_eq,
        "base": str(getattr(inp, "default_base", "") or ""), "base_eq": base_eq,
        "solvent": str(getattr(inp, "default_reaction_solvent", "") or "DMF"),
    }


def _is_direct_2ctc_loading_row(inp, row: dict[str, Any], position: int) -> bool:
    """Identify the existing direct-loading row without reclassifying Plan edits.

    Apply Change must preserve the first 2-CTC loading row as loading.  The
    visible row already contains the exact loading AA/DIEA amounts generated by
    the engine; treating it as an ordinary Fmoc coupling would incorrectly add
    DIC/HOBt and overwrite those loading values.
    """
    if position != 0 or not bool(getattr(inp, "apply_resin_loading", False)):
        return False
    try:
        from spps_planner.engine import resin_profile
        if str(resin_profile(getattr(inp, "resin", ""))) != "CTC_DIRECT":
            return False
    except Exception:
        resin_key = re.sub(r"[^a-z0-9]+", "", str(getattr(inp, "resin", "")).lower())
        if resin_key != "2ctc":
            return False
    note = str(row.get("Note", "") or "").lower()
    return "direct loading" in note or "loading stoichiometry" in note


def _recalc_direct_loading_row(gui, ns: dict[str, Any], inp, row: dict[str, str], dirty: set[str]) -> dict[str, str]:
    """Recalculate only explicitly edited cells while preserving loading chemistry.

    In particular, blank coupling-reagent/catalyst cells remain blank and the
    existing loading AA, DIEA and solvent values are not replaced by the
    general coupling defaults during Apply Change.
    """
    scale = _num(inp.scale_mmol, 0.0)
    repeat = max(1, int(round(_num(row.get("Repeat"), 1))))
    row["Repeat"] = str(repeat)

    unit = _canonical(ns, row.get("Unit name", ""))
    row["Unit name"] = unit
    unit_mw, unit_den = _lookup(gui, ns, unit)
    if "Unit name" in dirty:
        if "MW" not in dirty and unit_mw:
            row["MW"] = _fmt(unit_mw)
        if "Density(g/mL)" not in dirty:
            row["Density(g/mL)"] = _fmt(unit_den) if unit_den else ""
    if {"Unit eq", "Repeat"} & dirty:
        unit_mmol = scale * _num(row.get("Unit eq"), 0.0) * repeat
        row["Unit mmol"] = _fmt(unit_mmol)
    else:
        unit_mmol = _num(row.get("Unit mmol"), 0.0)
    if {"Unit name", "MW", "Density(g/mL)", "Unit eq", "Repeat"} & dirty:
        row["Unit amount"] = _amount(
            unit, unit_mmol, _num(row.get("MW"), unit_mw), _num(row.get("Density(g/mL)"), unit_den)
        )

    for name_col, eq_col, mw_col, den_col, mmol_col, amount_col, count_name in (
        ("Reagent 1", "R1 eq", "R1 MW", "R1 Density", "R1 mmol", "R1 amount", "default_reagent_count"),
        ("Reagent 2 / catalyst", "R2 eq", "R2 MW", "R2 Density", "R2 mmol", "R2 amount", "default_catalyst_count"),
        ("Base", "Base eq", "Base MW", "Base Density", "Base mmol", "Base amount", "default_base_count"),
    ):
        related = {name_col, eq_col, mw_col, den_col, "Repeat"}
        if not (related & dirty):
            continue
        name = _canonical(ns, row.get(name_col, ""))
        row[name_col] = name
        if not name:
            for column in (eq_col, mw_col, den_col, mmol_col, amount_col):
                row[column] = ""
            continue
        mw, den = _lookup(gui, ns, name)
        if name_col in dirty:
            if mw_col not in dirty and mw:
                row[mw_col] = _fmt(mw)
            if den_col not in dirty:
                row[den_col] = _fmt(den) if den else ""
        count = max(1, int(round(_num(_var(gui, count_name, 1), 1))))
        mmol = scale * _num(row.get(eq_col), 0.0) * count * repeat
        row[mmol_col] = _fmt(mmol)
        row[amount_col] = _amount(name, mmol, _num(row.get(mw_col), mw), _num(row.get(den_col), den))

    if {"Coupling solvent", "Repeat"} & dirty:
        solvent = _canonical(ns, row.get("Coupling solvent", ""))
        row["Coupling solvent"] = solvent
        try:
            from spps_planner.engine import working_volume_mL
            row["Solvent mL"] = _fmt(working_volume_mL(inp) * repeat) if solvent else ""
        except Exception:
            pass
    return row


def _recalc_plan(gui, ns: dict[str, Any], inp) -> None:
    tree = gui.pm_selected_plan_tree
    dirty_map = getattr(gui, "_v229_dirty_columns", {})
    scale = _num(inp.scale_mmol, 0.0)
    for position, iid in enumerate(list(tree.get_children())):
        row = _row_dict(tree, iid)
        dirty = set(dirty_map.get(iid, set()))
        if _is_direct_2ctc_loading_row(inp, row, position):
            _write_row(tree, iid, _recalc_direct_loading_row(gui, ns, inp, row, dirty))
            continue
        unit = _canonical(ns, row.get("Unit name", ""))
        row["Unit name"] = unit
        defaults = _chemistry_defaults(gui, ns, inp, unit)

        if "Unit name" in dirty:
            # Changing the unit selects the appropriate legacy chemistry defaults,
            # but any other cell explicitly edited before Apply Change wins.
            if "Unit eq" not in dirty:
                row["Unit eq"] = _fmt(defaults["unit_eq"])
            if "Reagent 1" not in dirty:
                row["Reagent 1"] = defaults["r1"]
            if "R1 eq" not in dirty:
                row["R1 eq"] = _fmt(defaults["r1_eq"]) if row.get("Reagent 1", "").strip() else ""
            if "Reagent 2 / catalyst" not in dirty:
                row["Reagent 2 / catalyst"] = defaults["r2"]
            if "R2 eq" not in dirty:
                row["R2 eq"] = _fmt(defaults["r2_eq"]) if row.get("Reagent 2 / catalyst", "").strip() else ""
            if "Base" not in dirty:
                row["Base"] = defaults["base"]
            if "Base eq" not in dirty:
                row["Base eq"] = _fmt(defaults["base_eq"]) if row.get("Base", "").strip() else ""
            if "Coupling solvent" not in dirty:
                row["Coupling solvent"] = defaults["solvent"]
            if "Note" not in dirty:
                if _is_ac_aa_oh(unit):
                    row["Note"] = (
                        "Plan-edited N-terminal Ac-AA coupling; terminal STD: "
                        "coupling -> final DMF wash x3 -> MC/DCM wash x3; "
                        "no deprotection."
                    )
                elif _is_ac2o(unit):
                    row["Note"] = (
                        "N-terminal Ac2O acetylation; terminal STD: "
                        "acetylation -> final DMF wash x3 -> MC/DCM wash x3; "
                        "no deprotection."
                    )
        else:
            if not row.get("Unit eq", "").strip():
                row["Unit eq"] = _fmt(defaults["unit_eq"])
            if not row.get("Reagent 1", "").strip() and defaults["r1"] and not _is_ac2o(unit):
                row["Reagent 1"] = defaults["r1"]
            if row.get("Reagent 1", "").strip() and not row.get("R1 eq", "").strip():
                row["R1 eq"] = _fmt(defaults["r1_eq"])
            if not row.get("Reagent 2 / catalyst", "").strip() and defaults["r2"] and not _is_ac2o(unit):
                row["Reagent 2 / catalyst"] = defaults["r2"]
            if row.get("Reagent 2 / catalyst", "").strip() and not row.get("R2 eq", "").strip():
                row["R2 eq"] = _fmt(defaults["r2_eq"])
            if not row.get("Base", "").strip() and defaults["base"]:
                row["Base"] = defaults["base"]
            if row.get("Base", "").strip() and not row.get("Base eq", "").strip():
                row["Base eq"] = _fmt(defaults["base_eq"])
            if not row.get("Coupling solvent", "").strip():
                row["Coupling solvent"] = defaults["solvent"]

        # If Unit eq changed and eq-follow is active, propagate it unless the
        # corresponding reagent eq was explicitly edited.
        if "Unit eq" in dirty and bool(getattr(inp, "reagent_eq_follows_coupling_eq", True)):
            unit_eq_for_follow = _num(row.get("Unit eq"), defaults["unit_eq"])
            if "R1 eq" not in dirty and row.get("Reagent 1", "").strip():
                row["R1 eq"] = _fmt(unit_eq_for_follow)
            if "R2 eq" not in dirty and row.get("Reagent 2 / catalyst", "").strip():
                row["R2 eq"] = _fmt(unit_eq_for_follow)
            if "Base eq" not in dirty and row.get("Base", "").strip():
                row["Base eq"] = _fmt(unit_eq_for_follow)

        repeat = max(1, int(round(_num(row.get("Repeat"), 1))))
        row["Repeat"] = str(repeat)
        unit_eq = _num(row.get("Unit eq"), 0.0)
        unit_mmol = scale * unit_eq * repeat
        unit_mw, unit_den = _lookup(gui, ns, unit)
        if unit_mw and "MW" not in dirty:
            row["MW"] = _fmt(unit_mw)
        if unit_den and "Density(g/mL)" not in dirty:
            row["Density(g/mL)"] = _fmt(unit_den)
        elif "Unit name" in dirty and "Density(g/mL)" not in dirty:
            # Unknown/new solid units should not inherit the previous unit's density.
            row["Density(g/mL)"] = ""
        row["Unit mmol"] = _fmt(unit_mmol)
        row["Unit amount"] = _amount(unit, unit_mmol, _num(row.get("MW"), unit_mw), _num(row.get("Density(g/mL)"), unit_den))

        for name_col, eq_col, mw_col, den_col, mmol_col, amount_col, count_name in (
            ("Reagent 1", "R1 eq", "R1 MW", "R1 Density", "R1 mmol", "R1 amount", "default_reagent_count"),
            ("Reagent 2 / catalyst", "R2 eq", "R2 MW", "R2 Density", "R2 mmol", "R2 amount", "default_catalyst_count"),
            ("Base", "Base eq", "Base MW", "Base Density", "Base mmol", "Base amount", "default_base_count"),
        ):
            name = _canonical(ns, row.get(name_col, ""))
            row[name_col] = name
            if not name:
                for column in (eq_col, mw_col, den_col, mmol_col, amount_col):
                    row[column] = ""
                continue
            eq = _num(row.get(eq_col), 0.0)
            count = max(1, int(round(_num(_var(gui, count_name, 1), 1))))
            mmol = scale * eq * count * repeat
            mw, den = _lookup(gui, ns, name)
            if mw and mw_col not in dirty:
                row[mw_col] = _fmt(mw)
            if den and den_col not in dirty:
                row[den_col] = _fmt(den)
            elif name_col in dirty and den_col not in dirty:
                row[den_col] = ""
            row[mmol_col] = _fmt(mmol)
            row[amount_col] = _amount(name, mmol, _num(row.get(mw_col), mw), _num(row.get(den_col), den))

        solvent = _canonical(ns, row.get("Coupling solvent", ""))
        row["Coupling solvent"] = solvent
        try:
            from spps_planner.engine import working_volume_mL
            row["Solvent mL"] = _fmt(working_volume_mL(inp) * repeat) if solvent else ""
        except Exception:
            pass
        _write_row(tree, iid, row)
    gui._v229_dirty_columns = {}


def _parse_amount(text: str) -> tuple[float, float]:
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", str(text or "").replace(",", ""))
    if not match:
        return 0.0, 0.0
    value = _num(match.group(0), 0.0)
    return (0.0, value) if "ml" in str(text).lower() else (value, 0.0)


def _split_solvent(name: str, total_ml: float) -> list[tuple[str, float]]:
    text = str(name or "").strip()
    matches = re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*%\s*([^/]+)", text)
    if matches:
        return [(component.strip(), total_ml * _num(percent) / 100.0) for percent, component in matches]
    return [(text, total_ml)] if text and total_ml else []


def _material_row(gui, ns, step, material, cls, mmol=0.0, amount="", phase="", note="", source="", use_count="", repeat=""):
    if not str(material or "").strip():
        return None
    mw, density = _lookup(gui, ns, material)
    grams, mls = _parse_amount(amount)
    if not amount and mmol and mw:
        amount = _amount(material, mmol, mw, density)
        grams, mls = _parse_amount(amount)
    return {
        "step": step, "material": material, "class": cls,
        "MW": _fmt(mw), "density_g_per_mL": _fmt(density),
        "planned_mmol": _fmt(mmol), "planned_g": _fmt(grams), "planned_mL": _fmt(mls),
        "use_count": use_count, "repeat": repeat, "phase": phase,
        "note": note, "source": source,
    }


def _visible_protocol(gui, ns: dict[str, Any], inp) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from spps_planner.engine import working_volume_mL, resin_profile
    tree = gui.pm_selected_plan_tree
    plan_rows = [ _row_dict(tree, iid) for iid in tree.get_children() ]
    materials: list[dict[str, Any]] = []
    checklist: list[dict[str, Any]] = []
    line = 1
    working_ml = _num(working_volume_mL(inp), 0.0)
    scale = _num(inp.scale_mmol, 0.0)
    loading = _num(inp.resin_loading_mmol_g, 0.0)
    resin_g = scale / loading if loading > 0 else 0.0
    materials.append({
        "step": "resin", "material": str(inp.resin), "class": "Resin", "MW": "", "density_g_per_mL": "",
        "planned_mmol": _fmt(scale), "planned_g": _fmt(resin_g), "planned_mL": "", "use_count": 1, "repeat": 1,
        "phase": "Resin", "note": f"Resin loading {_fmt(loading)} mmol/g", "source": "scale/loading",
    })

    def operation(step, op, unit, note=""):
        nonlocal line
        checklist.append({"line": line, "done": "", "checked_at": "", "operation": op, "unit": unit, "next_step": "", "note": note})
        line += 1

    def add_solvent(step, name, total_ml, cls, phase, note, count=1):
        for component, ml in _split_solvent(name, total_ml):
            row = _material_row(gui, ns, step, component, cls, amount=f"{_fmt(ml)} mL", phase=phase, note=note, source="Visible Selected Plan / SPPS protocol", use_count=count, repeat=count)
            if row:
                materials.append(row)

    profile = resin_profile(inp.resin)
    depro_count = max(0, int(round(_num(getattr(inp, "deprotection_count", 2), 2))))
    depro_text = str(getattr(inp, "deprotection_ratio", "20% in DMF") or "20% in DMF")
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%", depro_text)
    base_fraction = _num(match.group(1), 20.0) / 100.0 if match else 0.2
    depro_base = str(getattr(inp, "deprotection_base", "Piperidine") or "Piperidine")
    final_index = len(plan_rows) - 1

    for idx, row in enumerate(plan_rows):
        step = row.get("No") or str(idx + 1)
        unit = row.get("Unit name", "")
        is_first = idx == 0
        is_last = idx == final_index
        is_terminal = _is_terminal_chemical(unit)

        if is_first and profile == "CTC_DIRECT" and bool(getattr(inp, "apply_resin_loading", False)):
            add_solvent(step, "MC/DCM", working_ml, "Swell solvent", "Swell", "2-CTC DCM swell x1")
            operation(step, "Swell: MC/DCM x1", unit, "Direct-loading 2-CTC")
        else:
            # Regular cycles: deprotect twice, then DMF wash x2. Final coupling uses DMF wash x6.
            if not (is_first and profile == "CTC_DIRECT"):
                total_solution = working_ml * depro_count
                add_solvent(step, depro_base, total_solution * base_fraction, "Deprotection base", "Deprotection", depro_text, depro_count)
                add_solvent(step, "DMF", total_solution * (1.0 - base_fraction), "Deprotection solvent", "Deprotection", depro_text, depro_count)
                for rep in range(1, depro_count + 1):
                    operation(step, f"Deprotection {rep}", unit, depro_text)
                prewash = 6 if is_last or is_terminal else 2
                add_solvent(step, "DMF", working_ml * prewash, "Pre-coupling wash solvent", "DMF wash", f"DMF wash x{prewash} before coupling", prewash)
                operation(step, f"DMF wash x{prewash}", unit, "Before coupling")

        for material, cls, eq_key, mmol_key, amount_key in (
            (row.get("Unit name", ""), "AA/Chemical", "Unit eq", "Unit mmol", "Unit amount"),
            (row.get("Reagent 1", ""), "Coupling reagent", "R1 eq", "R1 mmol", "R1 amount"),
            (row.get("Reagent 2 / catalyst", ""), "Catalyst/additive", "R2 eq", "R2 mmol", "R2 amount"),
            (row.get("Base", ""), "Base", "Base eq", "Base mmol", "Base amount"),
        ):
            rec = _material_row(gui, ns, step, material, cls, _num(row.get(mmol_key), 0), row.get(amount_key, ""), "Coupling", f"{eq_key}={row.get(eq_key,'')}", "Visible Selected Plan", 1, row.get("Repeat", "1"))
            if rec:
                materials.append(rec)
        solvent_ml = _num(row.get("Solvent mL"), 0.0)
        add_solvent(step, row.get("Coupling solvent", ""), solvent_ml, "Coupling solvent", "Coupling", "Visible Selected Plan coupling solvent")
        operation(step, "Coupling / reaction", unit, f"Unit eq={row.get('Unit eq','')}; R1={row.get('Reagent 1','')} {row.get('R1 eq','')} eq; R2={row.get('Reagent 2 / catalyst','')} {row.get('R2 eq','')} eq; Base={row.get('Base','')} {row.get('Base eq','')} eq")

        if is_last:
            is_fmoc_aa = _is_fmoc(unit)
            is_acetylation = _is_ac2o(unit)
            is_ac_aa = _is_ac_aa_oh(unit)

            if is_fmoc_aa or is_acetylation or is_ac_aa:
                # Operator-confirmed terminal STD:
                #   Fmoc-AA: coupling -> DMF x2 -> 20% piperidine/DMF x2
                #            -> final DMF x3 -> final MC/DCM x3.
                #   Ac2O:    acetylation -> final DMF x3
                #            -> final MC/DCM x3.
                #   Ac-AA:   coupling -> final DMF x3
                #            -> final MC/DCM x3; no deprotection.
                # There is no separate DMF x6 wash after the terminal
                # deprotection in these final sequences.
                if is_fmoc_aa:
                    add_solvent(step, "DMF", working_ml * 2, "Post-coupling wash solvent", "DMF wash", "DMF wash x2 after final coupling", 2)
                    operation(step, "Post-coupling DMF wash x2", unit)

                    phase = "Last deprotection"
                    total_solution = working_ml * depro_count
                    add_solvent(step, depro_base, total_solution * base_fraction, "Deprotection base", phase, depro_text, depro_count)
                    add_solvent(step, "DMF", total_solution * (1.0 - base_fraction), "Deprotection solvent", phase, depro_text, depro_count)
                    for rep in range(1, depro_count + 1):
                        operation(step, f"Last Fmoc deprotection {rep}", unit, depro_text)

                if is_acetylation:
                    final_note = "after acetylation"
                elif is_ac_aa:
                    final_note = "after terminal Ac-AA coupling"
                else:
                    final_note = "after terminal deprotection"
                add_solvent(step, "DMF", working_ml * 3, "Final wash solvent", "Final wash", f"DMF x3 {final_note}", 3)
                operation(step, "Final DMF wash x3", unit)
                add_solvent(step, "MC/DCM", working_ml * 3, "Final wash solvent", "Final wash", f"MC/DCM x3 {final_note}", 3)
                operation(step, "Final MC/DCM wash x3", unit)
            else:
                # Preserve all other accepted terminal chemical/label/tag flows.
                post_dmf = 3
                add_solvent(step, "DMF", working_ml * post_dmf, "Final wash solvent", "Final wash", "DMF x3 after final coupling", post_dmf)
                operation(step, "Final DMF wash x3", unit)
                add_solvent(step, "MC/DCM", working_ml * 3, "Final wash solvent", "Final wash", "MC/DCM x3 after final coupling", 3)
                operation(step, "Final MC/DCM wash x3", unit)
        else:
            postwash = 6
            add_solvent(step, "DMF", working_ml * postwash, "Post-coupling wash solvent", "DMF wash", "DMF wash x6 after coupling", postwash)
            operation(step, "Post-coupling DMF wash x6", unit)

    for i in range(len(checklist) - 1):
        checklist[i]["next_step"] = checklist[i + 1]["operation"]
    return materials, checklist


def _total_rows(materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for row in materials:
        material = str(row.get("material", "") or "").strip()
        if not material:
            continue
        rec = groups.setdefault(material, {
            "material": material, "class": set(), "MW": row.get("MW", ""),
            "Density(g/mL)": row.get("density_g_per_mL", ""), "mmol": 0.0, "g": 0.0, "mL": 0.0,
        })
        if row.get("class"):
            rec["class"].add(str(row.get("class")))
        rec["mmol"] += _num(row.get("planned_mmol"), 0.0)
        rec["g"] += _num(row.get("planned_g"), 0.0)
        rec["mL"] += _num(row.get("planned_mL"), 0.0)
        if not rec.get("MW") and row.get("MW"):
            rec["MW"] = row.get("MW")
        if not rec.get("Density(g/mL)") and row.get("density_g_per_mL"):
            rec["Density(g/mL)"] = row.get("density_g_per_mL")
    out = []
    for rec in groups.values():
        amount = ""
        if rec["mL"]:
            amount = f"{_fmt(rec['mL'], 4)} mL"
        elif rec["g"]:
            amount = f"{_fmt(rec['g'], 4)} g"
        out.append({
            "material": rec["material"], "class": " / ".join(sorted(rec["class"])),
            "MW": rec["MW"], "Density(g/mL)": rec["Density(g/mL)"],
            "total mmol": _fmt(rec["mmol"]), "total amount": amount,
            "note": "Merged from visible Selected Plan and protocol",
        })
    return out


def _write_linked(gui, ns: dict[str, Any], inp, *, include_cleavage: bool) -> None:
    materials, checklist = _visible_protocol(gui, ns, inp)
    v228._write_rows(gui.pm_selected_material_tree, materials, MATERIAL_COLUMNS, MATERIAL_WIDTHS)
    v228._write_rows(gui.pm_selected_total_tree, _total_rows(materials), TOTAL_COLUMNS, TOTAL_WIDTHS)
    v228._write_rows(gui.progress_tree, checklist, CHECK_COLUMNS, CHECK_WIDTHS)
    try:
        gui._update_progress_widgets()
    except Exception:
        pass
    if include_cleavage:
        _refresh_cleavage(gui, ns, inp)
    else:
        # Generate creates the synthesis plan only.  Cleavage is operator-driven
        # and is created when Apply Change is pressed after entering a cocktail.
        v228._clear_tree(getattr(gui, "pm_cleavage_tree", None))


def _refresh_cleavage(gui, ns: dict[str, Any], inp=None):
    """Generate cleavage only from an explicit operator entry/preset."""
    components = str(_var(gui, "cleavage_components_text", "") or "").strip()
    preset = str(_var(gui, "cleavage_preset", "") or "").strip()
    if not components and preset.upper() in {"", "AUTO"}:
        v228._clear_tree(getattr(gui, "pm_cleavage_tree", None))
        return pd.DataFrame()
    try:
        inp = inp or _build_plan_input(gui, ns)
        from spps_planner.engine import generate_cleavage_cocktail
        frame = generate_cleavage_cocktail(inp)
        v228._write_rows(gui.pm_cleavage_tree, frame.fillna("").to_dict("records"))
        return frame
    except Exception:
        v228._clear_tree(getattr(gui, "pm_cleavage_tree", None))
        return pd.DataFrame()


def _snapshot(gui) -> None:
    index = _active_index(gui)
    if index is None:
        return
    item = gui.pm_items[index]
    item.update(v228._editor_payload(gui))
    item["selected_plan_rows"] = v228._tree_rows(gui.pm_selected_plan_tree)
    item["selected_material_rows"] = v228._tree_rows(gui.pm_selected_material_tree)
    item["selected_total_rows"] = v228._tree_rows(gui.pm_selected_total_tree)
    item["selected_checklist_rows"] = v228._tree_rows(gui.progress_tree)
    item["selected_cleavage_rows"] = v228._tree_rows(gui.pm_cleavage_tree)
    try:
        v228._refresh_list_label(gui, index)
    except Exception:
        pass


def _save_active(gui, include_outputs=True) -> None:
    index = _active_index(gui)
    if index is None or getattr(gui, "_v229_switching", False):
        return
    gui.pm_items[index].update(v228._editor_payload(gui))
    if include_outputs:
        _commit_editor(gui)
        _snapshot(gui)


def _clear_editor_and_outputs(gui) -> None:
    gui._v229_switching = True
    try:
        for name in ("pm_project", "pm_peptide", "pm_sequence", "pm_scale", "pm_resin", "pm_loading", "pm_lot", "pm_chemistry", "pm_copies"):
            _set(gui, name, "")
        _set(gui, "cleavage_preset", "")
        _set(gui, "cleavage_eq_override", "0")
        _set(gui, "cleavage_components_text", "")
        for tree_name in ("pm_selected_plan_tree", "pm_selected_material_tree", "pm_selected_total_tree", "progress_tree", "pm_cleavage_tree"):
            v228._clear_tree(getattr(gui, tree_name, None))
        try:
            gui.pm_list.selection_clear(0, "end")
        except Exception:
            pass
        gui._v229_active_index = None
        gui._v229_dirty_columns = {}
    finally:
        gui._v229_switching = False


def _restore_item(gui, index: int, ns: dict[str, Any]) -> None:
    if not (0 <= int(index) < len(gui.pm_items)):
        return
    item = gui.pm_items[int(index)]
    gui._v229_switching = True
    try:
        for name, key, default in (
            ("pm_project", "project", ""), ("pm_peptide", "peptide", ""), ("pm_sequence", "sequence", ""),
            ("pm_scale", "scale", "0.2"), ("pm_resin", "resin", "Rink Amide AM"),
            ("pm_loading", "loading", "0.8"), ("pm_lot", "lot", ""),
            ("pm_chemistry", "chemistry", "DIC/HOBt"), ("pm_copies", "copies", "1"),
            ("loading_aa_eq", "loading_aa_eq", "2"), ("loading_diea_eq", "loading_diea_eq", "4"),
            ("cleavage_preset", "cleavage_preset", ""), ("cleavage_eq_override", "cleavage_eq_override", "0"),
            ("cleavage_components_text", "cleavage_components_text", ""),
        ):
            _set(gui, name, item.get(key, item.get("lot_no", default) if key == "lot" else default))
        try:
            gui.apply_loading_calc.set(bool(item.get("apply_loading_calc", False)))
        except Exception:
            pass
        gui._v229_active_index = int(index)
        gui.pm_list.selection_clear(0, "end")
        gui.pm_list.selection_set(index)
        gui.pm_list.activate(index)
    finally:
        gui._v229_switching = False
    v228._write_rows(gui.pm_selected_plan_tree, item.get("selected_plan_rows", []), PLAN_COLUMNS, PLAN_WIDTHS)
    v228._write_rows(gui.pm_selected_material_tree, item.get("selected_material_rows", []), MATERIAL_COLUMNS, MATERIAL_WIDTHS)
    v228._write_rows(getattr(gui, "pm_selected_total_tree", getattr(gui, "pm_total_tree", None)), item.get("selected_total_rows", []), TOTAL_COLUMNS, TOTAL_WIDTHS)
    v228._write_rows(gui.progress_tree, item.get("selected_checklist_rows", []), CHECK_COLUMNS, CHECK_WIDTHS)
    v228._write_rows(gui.pm_cleavage_tree, item.get("selected_cleavage_rows", []))
    gui._v229_dirty_columns = {}
    _bind_plan_editor(gui, ns)


def _single_select(gui, _event=None):
    # Selection alone does not replace the editor. Double-click is the explicit
    # restore operation requested by the operator.
    return None


def _double_click(gui, ns: dict[str, Any], _event=None):
    try:
        selected = list(gui.pm_list.curselection())
        if not selected:
            return "break"
        new_index = int(selected[0])
    except Exception:
        return "break"
    old = _active_index(gui)
    if old is not None and old != new_index:
        _save_active(gui, include_outputs=True)
    _restore_item(gui, new_index, ns)
    return "break"


def _live_sync(gui):
    if getattr(gui, "_v229_switching", False):
        return
    index = _active_index(gui)
    if index is None:
        return
    gui.pm_items[index].update(v228._editor_payload(gui))
    try:
        v228._refresh_list_label(gui, index)
        gui.schedule_autosave()
    except Exception:
        pass


def _commit_editor(gui):
    """Commit the currently open Plan cell before Apply Change reads the tree.

    Calling the editor callback directly avoids a Tk focus/event ordering race
    when the operator clicks Apply Change while a combobox or entry is still
    active. The legacy Return-event fallback is retained for older editors.
    """
    tree = getattr(gui, "pm_selected_plan_tree", None)
    editor = getattr(tree, "_v229_editor", None) if tree is not None else None
    try:
        if editor is None or not editor.winfo_exists():
            return
        callback = getattr(editor, "_v229_commit", None)
        if callable(callback):
            callback()
        else:
            editor.event_generate("<Return>")
            gui.update()
    except Exception:
        pass


def _mark_visible_plan_edits(gui) -> None:
    """Mark edits made by either Plan editor path before recalculation.

    The legacy ``Edit Unit name`` dialog writes directly to the visible tree
    and does not populate ``_v229_dirty_columns``. Compare the visible Plan
    with the last accepted snapshot so Apply Change treats those edits exactly
    like a double-click cell edit, without regenerating the Plan from Sequence.
    """
    index = _active_index(gui)
    if index is None:
        return
    try:
        previous_rows = list(gui.pm_items[index].get("selected_plan_rows", []) or [])
    except Exception:
        previous_rows = []
    previous_by_no = {
        str(row.get("No", "") or "").strip(): row
        for row in previous_rows
        if isinstance(row, dict) and str(row.get("No", "") or "").strip()
    }
    editable_columns = {
        "Unit name", "MW", "Density(g/mL)", "Unit eq",
        "Reagent 1", "R1 eq", "R1 MW", "R1 Density",
        "Reagent 2 / catalyst", "R2 eq", "R2 MW", "R2 Density",
        "Base", "Base eq", "Base MW", "Base Density",
        "Coupling solvent", "Solvent mL", "Repeat", "Note",
    }
    tree = getattr(gui, "pm_selected_plan_tree", None)
    if tree is None:
        return
    dirty_map = getattr(gui, "_v229_dirty_columns", {})
    for position, iid in enumerate(tree.get_children()):
        current = _row_dict(tree, iid)
        number = str(current.get("No", "") or "").strip()
        previous = previous_by_no.get(number)
        if previous is None and position < len(previous_rows):
            previous = previous_rows[position]
        if not isinstance(previous, dict):
            dirty_map.setdefault(iid, set()).update(editable_columns)
            continue
        for column in editable_columns:
            before = str(previous.get(column, "") or "").strip()
            after = str(current.get(column, "") or "").strip()
            if before != after:
                dirty_map.setdefault(iid, set()).add(column)
    gui._v229_dirty_columns = dirty_map


def _bind_plan_editor(gui, ns: dict[str, Any]) -> None:
    tree = gui.pm_selected_plan_tree
    editable_names = {"Unit name", "Reagent 1", "Reagent 2 / catalyst", "Base", "Coupling solvent"}

    def begin(event):
        if tree.identify("region", event.x, event.y) != "cell":
            return
        iid = tree.identify_row(event.y)
        column_id = tree.identify_column(event.x)
        if not iid or not column_id:
            return
        index = int(column_id[1:]) - 1
        columns = list(tree["columns"])
        if index < 0 or index >= len(columns):
            return
        column = columns[index]
        if column in {"No", "Unit mmol", "Unit amount", "R1 mmol", "R1 amount", "R2 mmol", "R2 amount", "Base mmol", "Base amount"}:
            return
        bbox = tree.bbox(iid, column_id)
        if not bbox:
            return
        row = _row_dict(tree, iid)
        x, y, width, height = bbox
        if column in editable_names:
            editor = ttk.Combobox(tree, values=_unit_options(gui, ns, column), state="normal")
            editor.set(row.get(column, ""))
        else:
            editor = ttk.Entry(tree)
            editor.insert(0, row.get(column, ""))
        editor.place(x=x, y=y, width=max(width, 100), height=height)
        editor.focus_set()
        try:
            editor.select_range(0, "end")
        except Exception:
            pass
        tree._v229_editor = editor

        def commit(_e=None):
            try:
                if not editor.winfo_exists():
                    return
                value = editor.get()
                if column in editable_names:
                    value = _canonical(ns, value)
                row[column] = value
                _write_row(tree, iid, row)
                gui._v229_dirty_columns.setdefault(iid, set()).add(column)
            finally:
                try:
                    editor.destroy()
                except Exception:
                    pass
                tree._v229_editor = None

        def cancel(_e=None):
            try:
                editor.destroy()
            except Exception:
                pass
            tree._v229_editor = None

        # Apply Change can call this exact callback even before Tk dispatches
        # FocusOut/Return, so the latest visible value is never skipped.
        editor._v229_commit = commit
        editor.bind("<Return>", commit)
        editor.bind("<FocusOut>", commit)
        editor.bind("<Escape>", cancel)

    tree.bind("<Double-1>", begin, add=False)


def generate(gui, ns: dict[str, Any]):
    if getattr(gui, "_v229_generating", False):
        return None
    gui._v229_generating = True
    try:
        _save_active(gui, include_outputs=False)
        inp = _build_plan_input(gui, ns)
        rows = _generated_plan_rows(gui, ns, inp)
        v228._write_rows(gui.pm_selected_plan_tree, rows, PLAN_COLUMNS, PLAN_WIDTHS)
        gui._v229_dirty_columns = {}
        _bind_plan_editor(gui, ns)
        _write_linked(gui, ns, inp, include_cleavage=False)
        index = _active_index(gui)
        if index is not None:
            gui.pm_items[index]["status"] = "Calculated"
            _snapshot(gui)
        return True
    except Exception as exc:
        try:
            messagebox.showerror("Generate", str(exc))
        except Exception:
            pass
        return None
    finally:
        gui._v229_generating = False


def apply_change(gui, ns: dict[str, Any]):
    if getattr(gui, "_v229_applying", False):
        return None
    gui._v229_applying = True
    try:
        _commit_editor(gui)
        if not list(gui.pm_selected_plan_tree.get_children()):
            raise ValueError("Selected Plan is empty. Use Generate first.")
        _mark_visible_plan_edits(gui)
        inp = _build_plan_input(gui, ns)
        _recalc_plan(gui, ns, inp)
        _write_linked(gui, ns, inp, include_cleavage=True)
        index = _active_index(gui)
        if index is not None:
            gui.pm_items[index]["status"] = "Changed"
            _snapshot(gui)
        try:
            if hasattr(gui, "refresh_batch_workspace_preview"):
                gui.after_idle(gui.refresh_batch_workspace_preview)
        except Exception:
            pass
        return True
    except Exception as exc:
        try:
            messagebox.showerror("Apply Change", str(exc))
        except Exception:
            pass
        return None
    finally:
        gui._v229_applying = False


def _delete_selected(gui, ns):
    for iid in list(gui.pm_selected_plan_tree.selection()):
        gui.pm_selected_plan_tree.delete(iid)
    for number, iid in enumerate(gui.pm_selected_plan_tree.get_children(), 1):
        row = _row_dict(gui.pm_selected_plan_tree, iid)
        row["No"] = str(number)
        _write_row(gui.pm_selected_plan_tree, iid, row)
    apply_change(gui, ns)


def _install_plan_toolbar(gui, ns):
    tree = gui.pm_selected_plan_tree
    parent = tree.master
    for widget in v228._walk(parent):
        if isinstance(widget, ttk.Button):
            text = str(widget.cget("text"))
            if text in {"Apply Plan", "Apply Change"}:
                widget.destroy()
            elif text == "Delete selected row":
                widget.configure(command=lambda: _delete_selected(gui, ns))
    _bind_plan_editor(gui, ns)


def _install_action_buttons(gui, ns):
    v228._install_action_buttons(gui, ns)
    # v228 creates buttons bound to its controller; reconnect exact V2.2.9 routes.
    for widget in v228._walk(gui):
        if not isinstance(widget, ttk.Button):
            continue
        try:
            text = str(widget.cget("text"))
        except Exception:
            continue
        if text == "Generate":
            widget.configure(command=lambda: generate(gui, ns))
        elif text == "Apply Change":
            widget.configure(command=lambda: apply_change(gui, ns))


def _find_setup_notebook(gui):
    for widget in v228._walk(gui):
        if not isinstance(widget, ttk.Notebook):
            continue
        try:
            labels = [str(widget.tab(tab, "text")) for tab in widget.tabs()]
        except Exception:
            continue
        if "Unit defaults" in labels and "Reagents" in labels and "Solvents / Wash" in labels:
            return widget
    return None


def _install_loading_controls(gui):
    """Keep legacy direct-loading controls, but remove duplicated loading rate.

    Resin loading (mmol/g) belongs only to the Selected peptide editor.  The
    legacy setup tab remains useful for direct 2-CTC loading AA/DIEA settings,
    so it is normalized instead of replaced with another parallel panel.
    """
    if not hasattr(gui, "apply_loading_calc"):
        gui.apply_loading_calc = tk.BooleanVar(value=False)
    # The V2.2.8 normalizer removes the duplicated pm_loading and loading
    # solvent controls, renames the tab to Direct loading, and preserves the
    # useful checkbox plus loading AA/DIEA eq controls.
    try:
        v228._normalize_setup_panel(gui)
    except Exception:
        pass

    notebook = _find_setup_notebook(gui)
    if notebook is None:
        return
    # Defensive cleanup for older legacy layouts whose label wording differs.
    pm_loading_var = str(getattr(gui, "pm_loading", ""))
    loading_solvent_var = str(getattr(gui, "default_loading_dissolve_solvent", ""))
    for tab in notebook.tabs():
        label = str(notebook.tab(tab, "text"))
        if label not in {"Loading rate", "Resin loading", "Direct loading"}:
            continue
        frame = notebook.nametowidget(tab)
        notebook.tab(tab, text="Direct loading")
        rows_to_remove = set()
        for child in list(frame.winfo_children()):
            try:
                text = str(child.cget("text")).strip()
            except Exception:
                text = ""
            try:
                textvariable = str(child.cget("textvariable"))
            except Exception:
                textvariable = ""
            if text in {"Loading rate", "Resin loading", "Resin loading (mmol/g)", "Loading solvent"} or textvariable in {pm_loading_var, loading_solvent_var}:
                try:
                    rows_to_remove.add(int(child.grid_info().get("row", -1)))
                except Exception:
                    pass
                child.destroy()
        for child in list(frame.winfo_children()):
            try:
                row = int(child.grid_info().get("row", -1))
                text = str(child.cget("text")).strip()
            except Exception:
                continue
            if row in rows_to_remove and text in {"mmol/g", ""} and isinstance(child, ttk.Label):
                child.destroy()
        # Remove explanatory duplicate-loading labels; the editor label is
        # already explicit and is the single source of truth.
        for child in list(frame.winfo_children()):
            if isinstance(child, ttk.Label):
                try:
                    text = str(child.cget("text"))
                except Exception:
                    continue
                if "edited only in Selected peptide editor" in text or "edited once in the peptide editor" in text:
                    child.destroy()
        break

def _install_eq_follow_control(gui):
    if not hasattr(gui, "reagent_eq_follows_coupling_eq"):
        gui.reagent_eq_follows_coupling_eq = tk.BooleanVar(value=True)
    notebook = _find_setup_notebook(gui)
    if notebook is None:
        return
    for tab in notebook.tabs():
        if str(notebook.tab(tab, "text")) == "Reagents":
            frame = notebook.nametowidget(tab)
            ttk.Checkbutton(frame, text="Reagent / catalyst / base eq follows AA eq (1-5 mer: 2 eq, longer: Default AA eq)", variable=gui.reagent_eq_follows_coupling_eq).grid(row=6, column=0, columnspan=8, sticky="w", pady=(7, 2))
            break


def _rename_editor_loading(gui):
    # Exactly one operator-facing loading-rate field remains: the peptide editor.
    for widget in v228._walk(gui):
        if isinstance(widget, ttk.Label):
            try:
                if str(widget.cget("text")) == "Loading" and widget.master is getattr(gui.pm_loading, "_root", None):
                    widget.configure(text="Resin loading (mmol/g)")
            except Exception:
                pass
    # Parent matching above is intentionally conservative; use geometry proximity fallback.
    for widget in v228._walk(gui):
        if isinstance(widget, ttk.Label):
            try:
                if str(widget.cget("text")) == "Loading":
                    parent = widget.master
                    if any(isinstance(c, ttk.Entry) and str(c.cget("textvariable")) == str(gui.pm_loading) for c in parent.winfo_children()):
                        widget.configure(text="Resin loading (mmol/g)")
            except Exception:
                pass


def _install_cleavage(gui):
    notebook = v228._find_results_notebook(gui)
    if notebook is None:
        return
    frame = v228._tab_frame(notebook, "Cleavage Cocktail")
    if frame is None:
        return
    for child in list(frame.winfo_children()):
        try:
            child.destroy()
        except Exception:
            pass
    frame.rowconfigure(1, weight=1)
    frame.columnconfigure(0, weight=1)
    controls = ttk.Frame(frame, padding=(4, 4))
    controls.grid(row=0, column=0, columnspan=2, sticky="ew")
    ttk.Label(controls, text="Eq override (0=auto)").pack(side="left", padx=(0, 3))
    ttk.Entry(controls, textvariable=gui.cleavage_eq_override, width=8).pack(side="left", padx=(0, 8))
    ttk.Label(controls, text="Preset / custom name").pack(side="left", padx=(0, 3))
    ttk.Combobox(controls, textvariable=gui.cleavage_preset, values=[""] + v228._cocktail_presets(), state="normal", width=28).pack(side="left", padx=(0, 8))
    ttk.Label(controls, text="Components (example: TFA=95;TIS=2.5;Water=2.5)").pack(side="left", padx=(0, 3))
    ttk.Entry(controls, textvariable=gui.cleavage_components_text, width=48).pack(side="left", fill="x", expand=True)
    ttk.Label(controls, text="Apply with Apply Change").pack(side="left", padx=(8, 0))
    columns = ["component", "role", "recommended_eq", "percent", "percent_basis", "volume_mL", "density_g_mL", "approx_g", "physical_state", "selected_preset", "auto_recommended_preset", "include", "note"]
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for column in columns:
        tree.heading(column, text=column)
        tree.column(column, width=125 if column != "note" else 420, minwidth=45, anchor="w", stretch=False)
    ybar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    xbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=ybar.set, xscrollcommand=xbar.set)
    tree.grid(row=1, column=0, sticky="nsew")
    ybar.grid(row=1, column=1, sticky="ns")
    xbar.grid(row=2, column=0, sticky="ew")
    gui.pm_cleavage_tree = tree


def _install_result_tabs(gui, ns):
    v228._install_result_tabs(gui, ns)
    gui.pm_selected_total_tree = getattr(gui, "pm_total_tree", getattr(gui, "pm_selected_total_tree", None))
    v228._write_rows(gui.pm_selected_plan_tree, [], PLAN_COLUMNS, PLAN_WIDTHS)
    _install_plan_toolbar(gui, ns)
    _install_cleavage(gui)


def _install_traces(gui):
    names = [
        "pm_project", "pm_peptide", "pm_sequence", "pm_scale", "pm_resin", "pm_loading", "pm_lot", "pm_chemistry", "pm_copies",
        "apply_loading_calc", "loading_aa_eq", "loading_diea_eq", "cleavage_preset", "cleavage_eq_override", "cleavage_components_text",
    ]
    gui._v229_trace_tokens = []
    for name in names:
        variable = getattr(gui, name, None)
        if variable is None or not hasattr(variable, "trace_info"):
            continue
        try:
            for modes, callback_name in list(variable.trace_info()):
                for mode in modes:
                    try:
                        variable.trace_remove(mode, callback_name)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            token = variable.trace_add("write", lambda *_a, _gui=gui: _gui.after_idle(lambda: _live_sync(_gui)))
            gui._v229_trace_tokens.append((variable, token))
        except Exception:
            pass


def _session_path(gui) -> Path:
    try:
        path = gui._state_file_path()
    except Exception:
        path = Path.home() / ".spps_planner" / "spps_planner_session_v1.json"
    gui.state_file = path
    return path


def _load_items_only(gui) -> None:
    path = _session_path(gui)
    items = []
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            items = [dict(item) for item in data.get("pm_items", []) if isinstance(item, dict)]
    except Exception:
        items = []
    if not items:
        # Keep one empty project slot without loading it into the editor.
        items = [{
            "project": "Project-001", "peptide": "Peptide-001", "sequence": "", "copies": "1",
            "scale": "0.2", "resin": "Rink Amide AM", "loading": "0.8", "lot": "",
            "chemistry": "DIC/HOBt", "status": "Ready", "cleavage_preset": "",
        }]
    gui.pm_items = items
    gui.pm_list.delete(0, "end")
    for item in items:
        try:
            gui.pm_list.insert("end", gui.pm_display_name(item))
        except Exception:
            gui.pm_list.insert("end", f"{item.get('project','')} | {item.get('peptide','')}")


def save_session(gui):
    try:
        _save_active(gui, include_outputs=True)
        path = _session_path(gui)
        path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "app_version": VERSION,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
            "selected_pm_index": _active_index(gui) if _active_index(gui) is not None else 0,
            "pm_items": list(gui.pm_items),
            "defaults": {},
        }
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(state, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        temp.replace(path)
        gui._autosave_after_id = None
        return path
    except Exception:
        gui._autosave_after_id = None
        return None


def schedule_autosave(gui):
    try:
        pending = getattr(gui, "_autosave_after_id", None)
        if pending:
            gui.after_cancel(pending)
    except Exception:
        pass
    try:
        gui._autosave_after_id = gui.after(700, lambda: save_session(gui))
    except Exception:
        gui._autosave_after_id = None


def add_item(gui, item=None):
    _save_active(gui)
    number = len(gui.pm_items) + 1
    item = dict(item or {
        "project": f"Project-{number:03d}", "peptide": f"Peptide-{number:03d}", "sequence": "", "copies": "1",
        "scale": "0.2", "resin": "Rink Amide AM", "loading": "0.8", "lot": "",
        "chemistry": "DIC/HOBt", "status": "Ready", "cleavage_preset": "",
    })
    gui.pm_items.append(item)
    gui.pm_list.insert("end", gui.pm_display_name(item))
    required = ("pm_selected_plan_tree", "pm_selected_material_tree", "pm_total_tree", "progress_tree", "pm_cleavage_tree")
    if all(hasattr(gui, name) for name in required):
        _restore_item(gui, len(gui.pm_items) - 1, gui._v229_ns)
    else:
        gui._v229_active_index = len(gui.pm_items) - 1


def duplicate_item(gui):
    index = _active_index(gui)
    if index is None:
        return
    _save_active(gui)
    item = json.loads(json.dumps(gui.pm_items[index], default=str))
    item["peptide"] = f"{item.get('peptide','Peptide')}_copy"
    add_item(gui, item)


def delete_item(gui):
    index = _active_index(gui)
    if index is None:
        try:
            selected = list(gui.pm_list.curselection())
            index = int(selected[0]) if selected else None
        except Exception:
            index = None
    if index is None:
        return
    del gui.pm_items[index]
    gui.pm_list.delete(index)
    _clear_editor_and_outputs(gui)
    if not gui.pm_items:
        add_item(gui)
        _clear_editor_and_outputs(gui)


def _bind_item_actions(gui, ns):
    gui.pm_list.bind("<<ListboxSelect>>", lambda e: _single_select(gui, e), add=False)
    gui.pm_list.bind("<Double-Button-1>", lambda e: _double_click(gui, ns, e), add=False)
    gui.pm_list.bind("<Return>", lambda e: _double_click(gui, ns, e), add=False)
    try:
        parent = gui.pm_list.master
        for widget in v228._walk(parent):
            if isinstance(widget, ttk.Button):
                text = str(widget.cget("text"))
                if text == "Add":
                    widget.configure(command=lambda: add_item(gui))
                elif text == "Duplicate":
                    widget.configure(command=lambda: duplicate_item(gui))
                elif text == "Delete":
                    widget.configure(command=lambda: delete_item(gui))
    except Exception:
        pass


def export_outputs(gui, ns):
    """Export the exact visible V2.0.0 state without replacing manual edits."""
    try:
        if not v228._tree_rows(getattr(gui, "pm_selected_plan_tree", None)):
            if not generate(gui, ns):
                return None
        _commit_editor(gui)
        _save_active(gui, include_outputs=True)
        inp = _build_plan_input(gui, ns)
        try:
            out_text = gui.project_outdir.get() if hasattr(gui, "project_outdir") else ""
            if not str(out_text or "").strip() and hasattr(gui, "outdir"):
                out_text = gui.outdir.get()
            out = Path(str(out_text or "").strip() or "outputs/project_manager_exports")
        except Exception:
            out = Path("outputs/project_manager_exports")
        out.mkdir(parents=True, exist_ok=True)

        try:
            from spps_planner.export import export_csvs, export_excel
            export_csvs(inp, out / "core_engine_outputs")
            export_excel(inp, out / "spps_plan_core_engine.xlsx")
        except Exception:
            pass

        visible_plan = pd.DataFrame(v228._tree_rows(getattr(gui, "pm_selected_plan_tree", None)))
        visible_materials = pd.DataFrame(v228._tree_rows(getattr(gui, "pm_selected_material_tree", None)))
        total_tree = getattr(gui, "pm_selected_total_tree", None) or getattr(gui, "pm_total_tree", None)
        visible_total = pd.DataFrame(v228._tree_rows(total_tree))
        visible_checklist = pd.DataFrame(v228._tree_rows(getattr(gui, "progress_tree", None)))
        visible_cleavage = pd.DataFrame(v228._tree_rows(getattr(gui, "pm_cleavage_tree", None)))
        try:
            from spps_planner.engine import cleavage_cocktail_presets, validate_plan, plan_summary
            presets = cleavage_cocktail_presets()
            validation = validate_plan(inp)
            summary = pd.DataFrame([plan_summary(inp)])
        except Exception:
            presets = validation = summary = pd.DataFrame()

        index = _active_index(gui)
        item = dict(gui.pm_items[index]) if index is not None and 0 <= index < len(gui.pm_items) else v228._editor_payload(gui)
        editor_summary = pd.DataFrame([{
            "app_version": VERSION,
            "project": item.get("project", ""), "peptide": item.get("peptide", ""),
            "sequence": item.get("sequence", ""), "scale": item.get("scale", ""),
            "resin": item.get("resin", ""), "loading": item.get("loading", ""),
            "lot": item.get("lot", item.get("lot_no", "")), "chemistry": item.get("chemistry", ""),
            "copies": item.get("copies", ""), "apply_loading_calc": item.get("apply_loading_calc", False),
            "loading_aa_eq": item.get("loading_aa_eq", ""), "loading_diea_eq": item.get("loading_diea_eq", ""),
            "cleavage_preset": item.get("cleavage_preset", ""),
            "cleavage_components_text": item.get("cleavage_components_text", ""),
        }])

        xlsx = out / "project_manager_selected_outputs_v2.0.0.xlsx"
        with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
            editor_summary.to_excel(writer, index=False, sheet_name="00_EDITOR_SUMMARY")
            visible_plan.to_excel(writer, index=False, sheet_name="01_SELECTED_PLAN_VISIBLE")
            visible_materials.to_excel(writer, index=False, sheet_name="02_SELECTED_MATERIALS_STEP")
            visible_total.to_excel(writer, index=False, sheet_name="03_SELECTED_TOTAL_MATERIALS")
            visible_checklist.to_excel(writer, index=False, sheet_name="04_SELECTED_CHECKLIST")
            visible_cleavage.to_excel(writer, index=False, sheet_name="05_CLEAVAGE_COCKTAIL")
            presets.to_excel(writer, index=False, sheet_name="06_CLEAVAGE_PRESETS")
            validation.to_excel(writer, index=False, sheet_name="07_VALIDATION")
            summary.to_excel(writer, index=False, sheet_name="08_SUMMARY")

        for filename, frame in (
            ("01_SELECTED_PLAN_VISIBLE.csv", visible_plan),
            ("02_SELECTED_MATERIALS_STEP.csv", visible_materials),
            ("03_SELECTED_TOTAL_MATERIALS.csv", visible_total),
            ("04_SELECTED_CHECKLIST.csv", visible_checklist),
            ("05_CLEAVAGE_COCKTAIL.csv", visible_cleavage),
        ):
            frame.to_csv(out / filename, index=False, encoding="utf-8-sig")

        state = {
            "app_version": VERSION, "saved_at": datetime.now().isoformat(timespec="seconds"),
            "active_index": index, "pm_items": list(getattr(gui, "pm_items", []) or []),
            "visible_selected_plan_source": "current edited TreeView; Apply Change-linked V2.0.0 tables; no regeneration during export",
        }
        (out / "project_manager_state_v2.0.0.json").write_text(
            json.dumps(state, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
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


def _normalize_title(gui) -> None:
    gui.title(TITLE)
    for widget in v228._walk(gui):
        if isinstance(widget, ttk.Label):
            try:
                text = str(widget.cget("text"))
            except Exception:
                continue
            if text.startswith("SPPS Planner GitHub"):
                widget.configure(text=TITLE)
                break


def install(gui_cls, ns: dict[str, Any], original_build):
    def no_op(_self, *args, **kwargs):
        return None

    def build(gui):
        gui._v229_ns = ns
        gui._v228_ns = ns
        gui._v229_switching = True
        original_build(gui)
        gui._v229_switching = False
        try:
            v228._cancel_pending_legacy_jobs(gui)
        except Exception:
            pass
        v228._hide_non_workbench_tabs(gui)
        _normalize_title(gui)
        _install_result_tabs(gui, ns)
        _install_action_buttons(gui, ns)
        _install_loading_controls(gui)
        _install_eq_follow_control(gui)
        _rename_editor_loading(gui)
        _install_traces(gui)
        _load_items_only(gui)
        _bind_item_actions(gui, ns)
        _clear_editor_and_outputs(gui)
        try:
            v228._cancel_pending_legacy_jobs(gui)
        except Exception:
            pass

    gui_cls._build = build
    # Prevent the hidden old single-plan table from generating sample output after _build.
    gui_cls.rebuild_table = no_op
    gui_cls.refresh_outputs_from_tree = no_op
    gui_cls.pm_live_sync_selected = _live_sync
    gui_cls.pm_on_select = _single_select
    gui_cls.pm_on_double_click = lambda self, event=None: _double_click(self, ns, event)
    gui_cls.pm_generate_selected = lambda self, *a, **k: generate(self, ns)
    gui_cls.pm_calculate_all = lambda self, *a, **k: generate(self, ns)
    gui_cls.generate_update_plan = lambda self, *a, **k: generate(self, ns)
    gui_cls.apply_change = lambda self, *a, **k: apply_change(self, ns)
    gui_cls.pm_apply_change = lambda self, *a, **k: apply_change(self, ns)
    gui_cls.apply_plan_mw_density = lambda self, *a, **k: apply_change(self, ns)
    gui_cls.pm_add_peptide = lambda self, item=None: add_item(self, item)
    gui_cls.pm_duplicate_peptide = lambda self: duplicate_item(self)
    gui_cls.pm_delete_peptide = lambda self: delete_item(self)
    gui_cls.save_autosave_state = lambda self: save_session(self)
    gui_cls.schedule_autosave = lambda self: schedule_autosave(self)
    gui_cls.export_outputs = lambda self: export_outputs(self, ns)
    gui_cls.export_selected_outputs = lambda self: export_outputs(self, ns)
