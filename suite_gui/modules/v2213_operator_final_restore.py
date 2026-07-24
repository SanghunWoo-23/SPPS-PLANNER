"""V2.2.13 operator-requested final restoration.

Restores position-based AA eq/doubling controls, exact sequence-length plan
construction, Apply Change synchronization, cleavage inclusion in totals,
compact checklist UI, operator-facing label cleanup, and stable peptide-item
state handling without deleting legacy functionality.
"""
from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk
from typing import Any

APP_VERSION = "V2.2.13"
VERSION_LABEL = "SPPS Planner GitHub V2.2.13"


def _walk(widget):
    try:
        children = widget.winfo_children()
    except Exception:
        return
    for child in children:
        yield child
        yield from _walk(child)


def _get(var, default=""):
    try:
        return var.get()
    except Exception:
        return default


def _set(var, value):
    try:
        var.set(value)
    except Exception:
        pass


def _num(value, default=0.0):
    try:
        return float(str(value).strip())
    except Exception:
        return default


def _parse_ranges(text: str, default: list[tuple[int, int, float]]) -> list[tuple[int, int, float]]:
    """Parse C-terminal position rules.

    Accepted forms include both ranges (``4-7:2``) and a single position
    (``7:2``).  A blank field means "no position-specific override"; it
    must not silently re-enable the old example/default rules.
    """
    raw = str(text or "").strip()
    if not raw:
        return []

    out: list[tuple[int, int, float]] = []
    for part in re.split(r"[,;]+", raw):
        m = re.fullmatch(
            r"\s*(\d+)(?:\s*-\s*(\d+))?\s*:\s*([0-9]+(?:\.[0-9]+)?)\s*",
            part,
        )
        if not m:
            continue
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) is not None else a
        v = float(m.group(3))
        out.append((min(a, b), max(a, b), v))
    return out


def _range_value(position: int, rules, fallback: float) -> float:
    for start, end, value in rules:
        if start <= position <= end:
            return value
    return fallback


def _sequence_length(gui) -> int:
    seq = str(_get(getattr(gui, "pm_sequence", None), "") or "").strip()
    try:
        from spps_planner.parser import parse_sequence
        return len(list(parse_sequence(seq).core_tokens or []))
    except Exception:
        return len(re.findall(r"[A-Za-z]", seq))


def _sequence_unit_count(gui) -> int:
    """Count all written synthesis units used by the shared C-term rules.

    Core tokens already include natural AA, d-AA, internal chemicals and
    linkers.  A terminal modifier/label/tag such as Ac, FITC, Biotin or His6
    is one additional synthesis unit.
    """
    seq = str(_get(getattr(gui, "pm_sequence", None), "") or "").strip()
    try:
        from spps_planner.parser import parse_sequence
        parsed = parse_sequence(seq)
        return len(list(parsed.core_tokens or [])) + (1 if str(parsed.nterm or "").strip() else 0)
    except Exception:
        return _sequence_length(gui)


def _is_aa_row(row: dict[str, Any]) -> bool:
    # Kept for compatibility with older callers.  Position-rule application
    # itself now uses every real synthesis unit, not only Fmoc AA rows.
    return str(row.get("Unit name", "")).strip().lower().startswith("fmoc-")


def _is_position_unit_row(row: dict[str, Any]) -> bool:
    """AA, d-AA, chemical, label, tag and linker share one position system."""
    return bool(str(row.get("Unit name", "") or "").strip()) and not _is_fmoc_removal(row)


def _is_fmoc_removal(row: dict[str, Any]) -> bool:
    text = " ".join(str(row.get(k, "")) for k in ("Unit name", "Note"))
    key = re.sub(r"[^a-z0-9]+", "", text.lower())
    return "fmocremoval" in key or "deprotectiononly" in key


def _apply_generated_position_rules(gui, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(r) for r in rows if not _is_fmoc_removal(r)]
    seq_units = _sequence_unit_count(gui)
    unit_indices = [i for i, r in enumerate(rows) if _is_position_unit_row(r)]
    # Preserve the established direct-loaded 2-CTC handling: if a historical
    # route emits an extra C-terminal loading unit, remove only that excess.
    if seq_units >= 0 and len(unit_indices) > seq_units:
        remove_count = len(unit_indices) - seq_units
        remove = set(unit_indices[:remove_count])
        rows = [r for i, r in enumerate(rows) if i not in remove]
        unit_indices = [i for i, r in enumerate(rows) if _is_position_unit_row(r)]

    use_eq = bool(_get(getattr(gui, "use_position_aa_eq", None), True))
    use_double = bool(_get(getattr(gui, "use_position_doubling", None), True))
    eq_rules = _parse_ranges(_get(getattr(gui, "position_aa_eq_rules", None), ""), [])
    dbl_rules = _parse_ranges(_get(getattr(gui, "position_doubling_rules", None), ""), [])
    follows = bool(_get(getattr(gui, "reagent_eq_follows_coupling_eq", None), True))
    # Direct-loaded 2-CTC omits the already resin-bound C-terminal residue
    # from the editable Plan. Keep that residue in the positional count.
    # Terminal chemical/label/tag units are included in seq_units, so every
    # real synthesis unit shares the same C-term position system.
    cterm_offset = max(0, seq_units - len(unit_indices))
    for ordinal, row_index in enumerate(unit_indices, start=1):
        # The editable Plan is ordered C -> N across all synthesis units.
        cterm_position = cterm_offset + ordinal
        row = rows[row_index]
        if use_eq:
            fallback = _num(row.get("Unit eq"), _num(_get(getattr(gui, "coupling_eq", None), 5), 5))
            eq = _range_value(cterm_position, eq_rules, fallback)
            row["Unit eq"] = str(int(eq)) if float(eq).is_integer() else str(eq)
            if follows:
                for name_col, eq_col in (("Reagent 1","R1 eq"),("Reagent 2 / catalyst","R2 eq"),("Base","Base eq")):
                    if str(row.get(name_col, "")).strip():
                        row[eq_col] = row["Unit eq"]
        if use_double:
            repeat = int(round(_range_value(cterm_position, dbl_rules, 1.0)))
            row["Repeat"] = str(max(1, repeat))
    for i, row in enumerate(rows, 1):
        row["No"] = str(i)
    return rows


def _patch_v229(v229):
    if getattr(v229, "_v2213_patched", False):
        return

    old_generated = v229._generated_plan_rows
    old_recalc = v229._recalc_plan
    old_write_linked = v229._write_linked
    old_visible_protocol = v229._visible_protocol
    old_total_rows = v229._total_rows


    def visible_protocol(gui, ns, inp):
        """Return Materials/Checklist in the exact bench execution order.

        Operator-confirmed ordinary SPPS cycle:
          Deprotection x2 -> DMF wash x6 -> Coupling 1 -> DMF wash x2
          -> Coupling 2 -> DMF wash x2 -> ... -> next unit deprotection.

        Repeat=N therefore means N complete coupling reactions.  DMF x2 is
        placed between repeated couplings and, for a non-terminal unit, after
        the last coupling before the next unit starts.  The already accepted
        terminal flows (final Fmoc deprotection, Ac2O/Ac-AA final washes, etc.)
        are preserved exactly.  Direct 2-CTC loading keeps its special legacy
        loading/wash flow.
        """
        materials, checklist = old_visible_protocol(gui, ns, inp)
        plan = [v229._row_dict(gui.pm_selected_plan_tree, iid) for iid in gui.pm_selected_plan_tree.get_children()]
        if not plan:
            return materials, checklist

        try:
            from spps_planner.engine import working_volume_mL
            working_ml = _num(working_volume_mL(inp), 0)
        except Exception:
            working_ml = 0.0

        # ---------- Checklist: exact operation sequence ----------
        rebuilt_checklist = []
        reaction_index = 0
        for rec in checklist:
            op = str(rec.get("operation", "") or "")
            current_index = min(reaction_index, len(plan) - 1)
            current_row = plan[current_index] if plan else {}
            direct_loading = bool(
                current_row
                and v229._is_direct_2ctc_loading_row(inp, current_row, current_index)
            )

            # The ordinary pre-coupling wash is always DMF x6 after the two
            # deprotection reactions.  Direct 2-CTC loading is intentionally
            # excluded because it has its own established loading flow.
            if op == "DMF wash x2" and str(rec.get("note", "")) == "Before coupling" and not direct_loading:
                rebuilt_checklist.append(dict(rec, operation="DMF wash x6"))
                continue

            if op == "Coupling / reaction" and reaction_index < len(plan):
                row = plan[reaction_index]
                repeat = max(1, int(round(_num(row.get("Repeat"), 1))))
                base_note = str(rec.get("note", ""))
                for coupling_no in range(1, repeat + 1):
                    rebuilt_checklist.append(dict(
                        rec,
                        operation=(f"Coupling {coupling_no}" if repeat > 1 else "Coupling / reaction"),
                        note=base_note,
                    ))
                    if coupling_no < repeat:
                        rebuilt_checklist.append(dict(
                            rec,
                            operation="DMF wash x2",
                            note=f"Repeat coupling x{repeat}: inter-coupling wash after Coupling {coupling_no}",
                        ))
                reaction_index += 1
                continue

            # For an ordinary non-terminal unit, the wash after the final
            # coupling is DMF x2, then the next unit begins with deprotection
            # x2 -> DMF x6.  Keep direct-loading 2-CTC and all terminal flows.
            if op == "Post-coupling DMF wash x6" and reaction_index > 0:
                prev_index = reaction_index - 1
                prev_row = plan[prev_index]
                prev_direct = v229._is_direct_2ctc_loading_row(inp, prev_row, prev_index)
                if not prev_direct:
                    rebuilt_checklist.append(dict(rec, operation="Post-coupling DMF wash x2"))
                    continue

            rebuilt_checklist.append(rec)

        for i, rec in enumerate(rebuilt_checklist, 1):
            rec["line"] = i
            rec["next_step"] = rebuilt_checklist[i]["operation"] if i < len(rebuilt_checklist) else ""
        checklist = rebuilt_checklist

        # ---------- Materials: same exact step order as the checklist ----------
        # old_visible_protocol already emits each Plan step contiguously.  We
        # keep deprotection/final chemistry intact, change the ordinary wash
        # counts, split aggregate repeated-coupling material totals into each
        # actual coupling cycle, and insert DMF x2 at the exact interval.
        resin_rows = [dict(r) for r in materials if str(r.get("step", "")) == "resin"]
        rows_by_step = {}
        for rec in materials:
            step_key = str(rec.get("step", ""))
            if step_key == "resin":
                continue
            rows_by_step.setdefault(step_key, []).append(dict(rec))

        def _div(value, divisor):
            if divisor <= 1:
                return value
            text = str(value or "").strip()
            if not text:
                return value
            try:
                return v229._fmt(_num(text, 0.0) / divisor)
            except Exception:
                return value

        rebuilt_materials = list(resin_rows)
        for row_index, row in enumerate(plan):
            step = str(row.get("No", "") or (row_index + 1))
            step_rows = rows_by_step.get(step, [])
            repeat = max(1, int(round(_num(row.get("Repeat"), 1))))
            direct_loading = v229._is_direct_2ctc_loading_row(inp, row, row_index)

            before = []
            coupling = []
            after = []
            seen_coupling = False
            for rec in step_rows:
                if str(rec.get("phase", "")) == "Coupling":
                    seen_coupling = True
                    coupling.append(rec)
                elif not seen_coupling:
                    before.append(rec)
                else:
                    after.append(rec)

            # Correct ordinary pre-coupling DMF wash to x6.
            for rec in before:
                if str(rec.get("class", "")) == "Pre-coupling wash solvent" and not direct_loading:
                    rec["planned_mL"] = v229._fmt(working_ml * 6) if working_ml > 0 else rec.get("planned_mL", "")
                    rec["use_count"] = 6
                    rec["repeat"] = 6
                    rec["note"] = "DMF wash x6 before coupling"
                rebuilt_materials.append(rec)

            # Split repeat-aggregated coupling totals into actual Coupling 1..N
            # blocks so Materials is visually and numerically in bench order.
            if coupling:
                for coupling_no in range(1, repeat + 1):
                    for source in coupling:
                        rec = dict(source)
                        for key in ("planned_mmol", "planned_g", "planned_mL"):
                            rec[key] = _div(rec.get(key, ""), repeat)
                        rec["use_count"] = 1
                        rec["repeat"] = 1
                        rec["phase"] = f"Coupling {coupling_no}" if repeat > 1 else "Coupling"
                        note = str(rec.get("note", "") or "")
                        if repeat > 1:
                            rec["note"] = (note + f" | Coupling {coupling_no}/{repeat}").strip(" |")
                        rebuilt_materials.append(rec)

                    if coupling_no < repeat and working_ml > 0:
                        extra = v229._material_row(
                            gui, ns, step, "DMF", "Inter-coupling wash solvent",
                            amount=f"{v229._fmt(working_ml * 2)} mL",
                            phase="DMF wash",
                            note=f"Repeat coupling x{repeat}: DMF wash x2 after Coupling {coupling_no}",
                            source="Repeat coupling protocol",
                            use_count=2,
                            repeat=2,
                        )
                        if extra:
                            rebuilt_materials.append(extra)

            # Correct ordinary post-final-coupling wash to x2.  Terminal rows
            # and direct 2-CTC loading keep their established special sequence.
            for rec in after:
                if str(rec.get("class", "")) == "Post-coupling wash solvent" and not direct_loading:
                    # The terminal Fmoc flow already uses x2; this assignment is
                    # therefore idempotent and preserves its accepted behavior.
                    rec["planned_mL"] = v229._fmt(working_ml * 2) if working_ml > 0 else rec.get("planned_mL", "")
                    rec["use_count"] = 2
                    rec["repeat"] = 2
                    rec["note"] = "DMF wash x2 after final coupling of this unit"
                rebuilt_materials.append(rec)

        # Preserve any non-plan rows added by the legacy controller, in their
        # original relative order, without allowing them to jump ahead of the
        # synthesis steps above.
        known_steps = {str(r.get("No", "") or (i + 1)) for i, r in enumerate(plan)} | {"resin"}
        for rec in materials:
            if str(rec.get("step", "")) not in known_steps:
                rebuilt_materials.append(dict(rec))

        return rebuilt_materials, checklist

    def total_rows(materials):
        rows = list(old_total_rows(materials))
        def cls(row):
            text = (str(row.get("class", "")) + " " + str(row.get("material", ""))).lower()
            key = re.sub(r"[^a-z0-9가-힣]+", "", text)
            if "resin" in key: return 0
            if "solvent" in key or any(x in key for x in ("dmf","dcm","mcdcm","nmp","meoh","methanol")): return 1
            if "base" in key or any(x in key for x in ("diea","dipea","piperidine")): return 2
            if "catalyst" in key or "additive" in key or "couplingreagent" in key or any(x in key for x in ("dic","hobt","hbtu","hatu","comu","oxyma")): return 3
            if "acidcleavage" in key or "cleavagereagent" in key or any(x in key for x in ("tfa","hcl","aceticacid")): return 5
            return 4
        return sorted(rows, key=lambda r: (cls(r), str(r.get("material", "")).lower()))

    def generated(gui, ns, inp):
        # Position rules are applied after the legacy engine has built each row.
        # Keep the legacy baseline so a changed eq/repeat can also be reflected
        # in the actual mmol/amount/solvent calculations, not only in the
        # visible Unit eq / Repeat cells.
        baseline_rows = []
        for source_row in old_generated(gui, ns, inp):
            row = dict(source_row)
            row["__v2213_old_repeat"] = row.get("Repeat", "1")
            for eq_col, mmol_col in (("Unit eq", "Unit mmol"), ("R1 eq", "R1 mmol"), ("R2 eq", "R2 mmol"), ("Base eq", "Base mmol")):
                row[f"__v2213_old_{eq_col}"] = row.get(eq_col, "")
                row[f"__v2213_old_{mmol_col}"] = row.get(mmol_col, "")
            row["__v2213_old_solvent_ml"] = row.get("Solvent mL", "")
            baseline_rows.append(row)

        rows = _apply_generated_position_rules(gui, baseline_rows)
        for row in rows:
            old_repeat = max(1.0, _num(row.pop("__v2213_old_repeat", row.get("Repeat", 1)), 1.0))
            new_repeat = max(1.0, _num(row.get("Repeat", 1), 1.0))
            repeat_ratio = new_repeat / old_repeat

            for name_col, eq_col, mw_col, den_col, mmol_col, amount_col in (
                ("Unit name", "Unit eq", "MW", "Density(g/mL)", "Unit mmol", "Unit amount"),
                ("Reagent 1", "R1 eq", "R1 MW", "R1 Density", "R1 mmol", "R1 amount"),
                ("Reagent 2 / catalyst", "R2 eq", "R2 MW", "R2 Density", "R2 mmol", "R2 amount"),
                ("Base", "Base eq", "Base MW", "Base Density", "Base mmol", "Base amount"),
            ):
                old_eq = _num(row.pop(f"__v2213_old_{eq_col}", row.get(eq_col, 0)), 0.0)
                old_mmol = _num(row.pop(f"__v2213_old_{mmol_col}", row.get(mmol_col, 0)), 0.0)
                new_eq = _num(row.get(eq_col, 0), 0.0)
                eq_ratio = (new_eq / old_eq) if old_eq > 0 else 1.0
                new_mmol = old_mmol * repeat_ratio * eq_ratio
                row[mmol_col] = v229._fmt(new_mmol)
                row[amount_col] = v229._amount(
                    str(row.get(name_col, "") or ""),
                    new_mmol,
                    _num(row.get(mw_col), 0.0),
                    _num(row.get(den_col), 0.0),
                )

            old_solvent_ml = _num(row.pop("__v2213_old_solvent_ml", row.get("Solvent mL", 0)), 0.0)
            if str(row.get("Coupling solvent", "") or "").strip():
                row["Solvent mL"] = v229._fmt(old_solvent_ml * repeat_ratio)
            else:
                row["Solvent mL"] = ""
        return rows

    def recalc(gui, ns, inp):
        tree = gui.pm_selected_plan_tree
        dirty = getattr(gui, "_v229_dirty_columns", {})

        # Apply the *current* C-term repeat rule when Apply Change is pressed.
        # Previously the range was only evaluated during Generate, so checking
        # Doubling or changing e.g. 4-7:3 after a Plan already existed had no
        # effect.  Keep direct 2-CTC loading chemistry untouched; all actual
        # coupling rows receive Repeat=N (N may be 2, 3, 4, ...).
        current_rows = [v229._row_dict(tree, iid) for iid in tree.get_children()]
        unit_indices = [i for i, row in enumerate(current_rows) if _is_position_unit_row(row)]
        seq_units = _sequence_unit_count(gui)
        cterm_offset = max(0, seq_units - len(unit_indices))
        use_repeat_rule = bool(_get(getattr(gui, "use_position_doubling", None), True))
        repeat_rules = _parse_ranges(
            _get(getattr(gui, "position_doubling_rules", None), ""),
            [],
        )
        ordinal_by_index = {row_index: ordinal for ordinal, row_index in enumerate(unit_indices, start=1)}
        for position, iid in enumerate(tree.get_children()):
            if position not in ordinal_by_index:
                continue
            row = v229._row_dict(tree, iid)
            if v229._is_direct_2ctc_loading_row(inp, row, position):
                continue
            cterm_position = cterm_offset + ordinal_by_index[position]
            new_repeat = 1
            if use_repeat_rule:
                new_repeat = max(1, int(round(_range_value(cterm_position, repeat_rules, 1.0))))
            old_repeat_value = max(1, int(round(_num(row.get("Repeat"), 1))))
            if old_repeat_value != new_repeat:
                row["Repeat"] = str(new_repeat)
                v229._write_row(tree, iid, row)
                dirty.setdefault(iid, set()).add("Repeat")
        gui._v229_dirty_columns = dirty

        preserve = {}
        for iid in tree.get_children():
            if "Unit name" in set(dirty.get(iid, set())):
                row = v229._row_dict(tree, iid)
                preserve[iid] = {k: row.get(k, "") for k in ("Unit eq","R1 eq","R2 eq","Base eq","Repeat")}
        old_recalc(gui, ns, inp)
        for iid, values in preserve.items():
            row = v229._row_dict(tree, iid)
            row.update(values)
            v229._write_row(tree, iid, row)

    def write_linked(gui, ns, inp, *, include_cleavage: bool):
        old_write_linked(gui, ns, inp, include_cleavage=include_cleavage)
        if not include_cleavage:
            return
        try:
            frame = v229._refresh_cleavage(gui, ns, inp)
            if frame is None or getattr(frame, "empty", True):
                return
            materials = []
            for iid in gui.pm_selected_material_tree.get_children():
                materials.append(v229._row_dict(gui.pm_selected_material_tree, iid))
            for rec in frame.fillna("").to_dict("records"):
                component = str(rec.get("component", "")).strip()
                if not component or component in {"Total cocktail", "Cys warning", "2-CTC/Trityl warning"}:
                    continue
                ml = _num(rec.get("volume_mL"), 0)
                grams = _num(rec.get("approx_g"), 0)
                materials.append({
                    "step": "cleavage", "material": component, "class": "Acid/Cleavage reagent",
                    "MW": "", "density_g_per_mL": rec.get("density_g_mL", ""),
                    "planned_mmol": "", "planned_g": grams if grams and not ml else "",
                    "planned_mL": ml if ml else "", "use_count": 1, "repeat": 1,
                    "phase": "Cleavage", "note": f"{rec.get('percent','')}% {rec.get('percent_basis','')}",
                    "source": "Cleavage cocktail",
                })
            import suite_gui.modules.v228_fast_legacy_exact_workflow as v228
            v228._write_rows(gui.pm_selected_material_tree, materials, v229.MATERIAL_COLUMNS, v229.MATERIAL_WIDTHS)
            v228._write_rows(gui.pm_selected_total_tree, v229._total_rows(materials), v229.TOTAL_COLUMNS, v229.TOTAL_WIDTHS)
        except Exception:
            pass

    v229._generated_plan_rows = generated
    v229._recalc_plan = recalc
    v229._visible_protocol = visible_protocol
    v229._total_rows = total_rows
    v229._write_linked = write_linked
    v229._v2213_patched = True


def _find_setup_notebook(gui):
    for w in _walk(gui):
        if isinstance(w, ttk.Notebook):
            try:
                labels = [str(w.tab(t, "text")) for t in w.tabs()]
            except Exception:
                continue
            if "Unit defaults" in labels:
                return w
    return None


def _tab_frame(nb, label):
    for tab in nb.tabs():
        try:
            if str(nb.tab(tab, "text")) == label:
                return nb.nametowidget(tab)
        except Exception:
            pass
    return None


def _install_position_ui(gui):
    gui.use_position_aa_eq = getattr(gui, "use_position_aa_eq", tk.BooleanVar(value=True))
    gui.position_aa_eq_rules = getattr(gui, "position_aa_eq_rules", tk.StringVar(value=""))
    gui.use_position_doubling = getattr(gui, "use_position_doubling", tk.BooleanVar(value=True))
    gui.position_doubling_rules = getattr(gui, "position_doubling_rules", tk.StringVar(value=""))
    nb = _find_setup_notebook(gui)
    frame = _tab_frame(nb, "Unit defaults") if nb else None
    if frame is None:
        return
    # Remove the incorrect V2.2.12 helper checkboxes and explanatory text.
    bad_prefixes = (
        "Use default AA eq", "Use default doubling", "Use the same eq/doubling",
        "Manual per-unit values", "Default AA doubling",
    )
    for w in list(frame.winfo_children()):
        try:
            text = str(w.cget("text"))
        except Exception:
            text = ""
        if text.startswith(bad_prefixes):
            try: w.destroy()
            except Exception: pass
    max_row = 0
    for w in frame.winfo_children():
        try: max_row = max(max_row, int(w.grid_info().get("row", 0)))
        except Exception: pass
    box = ttk.LabelFrame(frame, text="Position rules from C-terminus")
    box.grid(row=max_row+1, column=0, columnspan=8, sticky="ew", padx=4, pady=(8,4))
    box.columnconfigure(2, weight=1)
    ttk.Checkbutton(box, text="AAs eq", variable=gui.use_position_aa_eq).grid(row=0,column=0,sticky="w",padx=5,pady=4)
    ttk.Label(box, text="C-term ranges").grid(row=0,column=1,sticky="e",padx=4)
    ttk.Entry(box, textvariable=gui.position_aa_eq_rules, width=28).grid(row=0,column=2,sticky="ew",padx=4)
    ttk.Checkbutton(box, text="Doubling", variable=gui.use_position_doubling).grid(row=1,column=0,sticky="w",padx=5,pady=4)
    ttk.Label(box, text="C-term ranges").grid(row=1,column=1,sticky="e",padx=4)
    ttk.Entry(box, textvariable=gui.position_doubling_rules, width=28).grid(row=1,column=2,sticky="ew",padx=4)
    ttk.Label(box, text="Example: AAs eq 1-3:1.5, 4-6:2 / Doubling 4-6:2").grid(row=2,column=0,columnspan=3,sticky="w",padx=5,pady=(0,4))


def _clean_selected_labels(gui):
    replacements = {
        "Selected Peptide Editor":"Peptide Editor", "Selected Plan":"Plan",
        "Selected Materials":"Materials", "Selected Total Materials":"Total Materials",
        "Selected Checklist":"Checklist", "Selected Cleavage Cocktail":"Cleavage Cocktail",
    }
    for w in _walk(gui):
        try:
            text = str(w.cget("text"))
        except Exception:
            continue
        new = replacements.get(text)
        if not new and text.lower().startswith("selected "):
            new = text[len("Selected "):]
        if new:
            try: w.configure(text=new)
            except Exception: pass
    for w in _walk(gui):
        if isinstance(w, ttk.Notebook):
            for tab in w.tabs():
                try:
                    text = str(w.tab(tab, "text"))
                    if text in replacements:
                        w.tab(tab, text=replacements[text])
                    elif text.lower().startswith("selected "):
                        w.tab(tab, text=text[len("Selected "):])
                except Exception:
                    pass


def _compact_checklist(gui):
    tree = getattr(gui, "progress_tree", None)
    if tree is not None:
        widths = {"line":45,"done":55,"checked_at":105,"operation":180,"unit":115,"next_step":185,"note":240}
        try:
            for col in tree["columns"]:
                tree.column(col, width=widths.get(col, 100), minwidth=35, stretch=(col in {"operation","next_step","note"}))
        except Exception:
            pass
    # Reduce large fixed spacer panes above checklist where possible.
    for w in _walk(gui):
        if isinstance(w, ttk.Panedwindow):
            try:
                w.after_idle(lambda p=w: [p.sashpos(i, 140) for i in range(max(0, len(p.panes())-1))])
            except Exception:
                pass


def _remove_cleavage_apply_text(gui):
    for w in list(_walk(gui)):
        try: text = str(w.cget("text"))
        except Exception: continue
        if "Apply with Apply Change" in text:
            try: w.destroy()
            except Exception: pass


def _install_title(gui):
    try: gui.title(VERSION_LABEL)
    except Exception: pass
    for w in _walk(gui):
        try:
            if isinstance(w, ttk.Label) and str(w.cget("text")).startswith("SPPS Planner GitHub"):
                w.configure(text=VERSION_LABEL)
        except Exception: pass


def install(gui_cls, ns: dict[str, Any], *_args, **_kwargs):
    import suite_gui.modules.v229_empty_start_exact_apply_sync as v229
    _patch_v229(v229)
    old_build = gui_cls._build

    def build(self):
        old_build(self)
        _install_title(self)
        _install_position_ui(self)
        _clean_selected_labels(self)
        _compact_checklist(self)
        _remove_cleavage_apply_text(self)

    gui_cls._build = build
    gui_cls.TITLE = VERSION_LABEL
    return gui_cls
