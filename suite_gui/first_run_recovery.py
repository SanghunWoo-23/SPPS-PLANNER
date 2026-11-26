"""Small, reversible startup helpers based on the 2026-11-16 working GUI."""
from __future__ import annotations


def has_saved_peptide(gui):
    return any(isinstance(row, dict) and str(row.get("sequence", "") or "").strip()
               for row in (getattr(gui, "pm_items", []) or []))


def offer_first_add(gui):
    if has_saved_peptide(gui):
        return False
    def show():
        try:
            if gui.winfo_exists() and not has_saved_peptide(gui):
                from suite_gui.modules.add_peptide_dialog import open_dialog
                open_dialog(gui)
        except Exception as exc:
            try: gui._log("First-run Add window warning: " + repr(exc) + "\n")
            except Exception: pass
    gui.after(250, show)
    return True


def register_unsaved_sequence(gui):
    """Create one real Project row from an initially empty direct editor."""
    sequence = getattr(gui, "pm_sequence", None)
    sequence = str(sequence.get()).strip() if hasattr(sequence, "get") else ""
    if not sequence or has_saved_peptide(gui):
        return False
    from suite_gui.quick_synthesis import current_project_payload
    from suite_gui.modules.add_peptide_dialog import _commit_project_item
    from suite_gui.modules.workspace_widgets import _editor_payload
    payload = current_project_payload(gui)
    # The startup editor is already populated.  Persist *all* of its active
    # Plan/recipe fields before the new Project row is restored; otherwise the
    # 2-CTC direct-loading checkbox and exact reagent equivalents are reset.
    payload.update(_editor_payload(gui))
    payload["sequence"] = sequence
    payload["project"] = str(payload.get("project") or "Project-001")
    payload["peptide"] = str(payload.get("peptide") or "Peptide-001")
    _commit_project_item(gui, payload)
    return True
