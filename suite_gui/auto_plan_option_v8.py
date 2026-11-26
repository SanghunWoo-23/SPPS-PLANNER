"""Optional sequence-first Auto Plan confirmation UI.

The existing Project Manager Generate remains the calculation authority.
No empirical cleavage recommendation is manufactured by this preview.
"""
from __future__ import annotations
import math
import tkinter as tk
from tkinter import ttk, messagebox
from spps_planner.parser import parse_sequence
from suite_gui.sequence_risk_map_v8 import build_sequence_risk_map
from datetime import datetime, timezone
import json
from tkinter import filedialog


def preview_inputs(sequence, scale, resin, loading, chemistry, copies):
    if not str(sequence or "").strip():
        raise ValueError("Enter a peptide sequence first.")
    parsed = parse_sequence(str(sequence).strip())
    tokens = list(parsed.core_tokens)
    if not tokens:
        raise ValueError("The sequence has no recognized amino-acid residues.")
    try:
        amount, load = float(scale), float(loading)
        count = int(copies)
    except (TypeError, ValueError) as exc:
        raise ValueError("Scale, loading, and copies must be numeric.") from exc
    if not all(math.isfinite(v) and v > 0 for v in (amount, load)) or count < 1:
        raise ValueError("Scale, loading, and copies must be positive finite values.")
    if not str(resin).strip():
        raise ValueError("Select a resin before generating.")
    cys = sum(str(token).upper() == "C" for token in tokens)
    tfa_eq = 100 * cys if cys else (30 if len(tokens) <= 7 else 80 if len(tokens) <= 15 else 100)
    return {
        "sequence": str(sequence).strip(), "residues": len(tokens),
        "scale": amount, "resin": str(resin).strip(), "loading": load,
        "copies": count, "chemistry": str(chemistry).strip(),
        "resin_g": amount / load, "tfa_eq": tfa_eq,
        "cys_count": cys, "nterm": parsed.nterm, "cterm": parsed.cterm_text,
    }


def build_review_draft(sequence, scale, resin, loading, chemistry, copies):
    """Deterministic, review-only V9 draft; never changes the active project.

    Experimental conditions and cleavage recipes are intentionally not inferred.
    """
    fields = preview_inputs(sequence, scale, resin, loading, chemistry, copies)
    risks = build_sequence_risk_map(fields["sequence"])
    return {
        "format": "SPPS Planner V9.0.0 operator review draft",
        "schema": 1,
        "status": "DRAFT_NOT_APPROVED",
        "source": "Current Project Manager inputs",
        "inputs": fields,
        "risk": {
            "findings": risks["findings"],
            "parser_warnings": risks["parser_warnings"],
            "meaning": risks["score_meaning"],
        },
        "cleavage": {
            "tfa_basis_eq": fields["tfa_eq"],
            "cocktail": None,
            "time_minutes": None,
            "evidence": "Unverified rule-based planning basis; operator review required",
        },
        "operator_notes": "",
        "generation": "Existing chemistry engine only after confirmation",
    }


def draft_to_json(draft, notes=""):
    """Serializable review draft; no experimental approval implied by export."""
    document = dict(draft)
    document["operator_notes"] = str(notes)
    return json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)


def open_auto_plan(gui):
    try:
        data = build_review_draft(gui.pm_sequence.get(), gui.pm_scale.get(),
                              gui.pm_resin.get(), gui.pm_loading.get(),
                              gui.pm_chemistry.get(), gui.pm_copies.get())
    except (ValueError, KeyError, AttributeError) as exc:
        messagebox.showerror("Auto Plan — check inputs", str(exc), parent=gui)
        return
    inputs = data["inputs"]
    win = tk.Toplevel(gui)
    win.title("Auto Plan | SPPS Planner V9.0.0")
    win.geometry("720x590")
    win.minsize(580, 450)
    win.transient(gui)
    body = ttk.Frame(win, padding=16)
    body.pack(fill="both", expand=True)
    ttk.Label(body, text="Auto Plan — review before generation", font=("Segoe UI", 15, "bold")).pack(anchor="w")
    ttk.Label(body, text="Optional: existing Generate and Step 1 / Step 2 remain unchanged.", wraplength=660).pack(anchor="w", pady=(4, 12))
    text = tk.Text(body, height=19, wrap="word", font=("Consolas", 10), relief="flat", borderwidth=6)
    text.pack(fill="both", expand=True)
    details = [
        "CURRENT PROJECT INPUTS (not changed by opening this window)",
        f"Sequence       {inputs['sequence']}",
        f"Residues       {inputs['residues']}",
        f"N-terminal     {inputs['nterm'] or 'none'}",
        f"C-terminal     {inputs['cterm'] or 'from resin / sequence notation'}",
        f"Scale          {inputs['scale']:g} mmol  ×  {inputs['copies']} copies",
        f"Resin          {inputs['resin']}",
        f"Loading        {inputs['loading']:g} mmol/g",
        f"Resin mass     {inputs['resin_g']:g} g per copy (theoretical)",
        f"Chemistry      {inputs['chemistry']}",
        "",
        "CLEAVAGE PLANNING — RULE-BASED, NOT VERIFIED RECIPE",
        f"TFA basis      {inputs['tfa_eq']} eq (Cys count: {inputs['cys_count']})",
        "Cocktail       NOT auto-selected; use verified operator conditions",
        "Time           NOT inferable from sequence alone",
        "TIS / NH4I     NEVER automatically added",
        "",
        "GENERATE WILL UPDATE",
        "Plan · Materials · Checklist · Total Materials · Cleavage / Workup",
        "using the existing engine and active Project Manager settings.",
        "Inspect the resulting tables and evidence before laboratory use.",
    ]
    text.insert("1.0", "\n".join(details))
    findings = data["risk"]["findings"]
    details.extend(["", f"SEQUENCE RISK — {len(findings)} rule-based findings (not failure probability)"])
    for finding in findings[:15]:
        details.append(f"[{finding['severity']}] {finding['rule_id']}: {finding['title']} (positions {finding['positions']})")
    if len(findings) > 15:
        details.append(f"... {len(findings) - 15} more findings; consult Sequence Risk Map")
    if data["risk"]["parser_warnings"]:
        details.extend(["PARSER WARNINGS:", *map(str, data["risk"]["parser_warnings"])])
    text.delete("1.0", "end")
    text.insert("1.0", "\n".join(details))
    text.configure(state="disabled")
    ttk.Label(body, text="Review notes (exported with draft; not an approved SOP):").pack(anchor="w")
    review_notes = tk.Text(body, height=3, wrap="word")
    review_notes.pack(fill="x", pady=(0, 6))
    status = ttk.Label(body, text="Review the above assumptions before applying.", foreground="#815500")
    status.pack(anchor="w", pady=(8, 6))
    buttons = ttk.Frame(body)
    buttons.pack(fill="x")

    def generate():
        try:
            latest = build_review_draft(gui.pm_sequence.get(), gui.pm_scale.get(), gui.pm_resin.get(),
                                    gui.pm_loading.get(), gui.pm_chemistry.get(), gui.pm_copies.get())
            if latest != data:
                messagebox.showwarning("Auto Plan", "Project values changed since preview. Reopen Auto Plan to review the new inputs.", parent=win)
                return
            gui.pm_generate_selected()
            idx = gui.pm_current_index()
            item = gui.pm_items[idx] if idx is not None else None
            if not item or item.get("status") != "Calculated":
                status.configure(text="Generation did not complete; inspect the Project Manager error.")
                return
            status.configure(text="Plan generated. Review Plan, Materials, Checklist and Cleavage tabs.", foreground="#176b3a")
            messagebox.showinfo("Auto Plan", "Existing engine generated the selected project outputs.\nReview the tables and confirm cleavage conditions before use.", parent=win)
        except Exception as exc:
            status.configure(text="Generation failed; no successful result was confirmed.")
            messagebox.showerror("Auto Plan", str(exc), parent=win)

    def export_draft():
        try:
            latest = build_review_draft(gui.pm_sequence.get(), gui.pm_scale.get(), gui.pm_resin.get(),
                                        gui.pm_loading.get(), gui.pm_chemistry.get(), gui.pm_copies.get())
            if latest != data:
                messagebox.showwarning("Auto Plan", "Project values changed; reopen preview before export.", parent=win)
                return
            destination = filedialog.asksaveasfilename(parent=win, title="Export unapproved review draft",
                 defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if not destination:
                return
            payload = draft_to_json(data, review_notes.get("1.0", "end-1c"))
            # No reliance on private persistence implementation: use same-directory temp + replace.
            from pathlib import Path
            import os, tempfile
            target = Path(destination)
            fd, temp = tempfile.mkstemp(dir=str(target.parent), prefix=".v9draft_", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, target)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
            status.configure(text="Unapproved draft exported (not an experimental SOP).", foreground="#176b3a")
        except Exception as exc:
            messagebox.showerror("Export draft", str(exc), parent=win)

    ttk.Button(buttons, text="Generate Full Plan", command=generate).pack(side="left")
    ttk.Button(buttons, text="Export Draft JSON", command=export_draft).pack(side="left", padx=(8, 0))
    ttk.Button(buttons, text="Close", command=win.destroy).pack(side="right")
    return win
