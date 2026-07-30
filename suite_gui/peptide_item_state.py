"""Project Manager peptide-item editor and output snapshot state."""
from __future__ import annotations


EDITOR_FIELDS = (
    ("pm_project", "project", ""),
    ("pm_peptide", "peptide", ""),
    ("pm_sequence", "sequence", ""),
    ("pm_scale", "scale", "0.2"),
    ("pm_resin", "resin", "Rink Amide AM"),
    ("pm_loading", "loading", "0.8"),
    ("pm_lot", "lot", ""),
    ("pm_chemistry", "chemistry", "DIC/HOBt"),
    ("pm_copies", "copies", "1"),
    ("loading_aa_eq", "loading_aa_eq", "2"),
    ("loading_diea_eq", "loading_diea_eq", "4"),
    ("cleavage_preset", "cleavage_preset", ""),
    ("cleavage_eq_override", "cleavage_eq_override", "0"),
    ("cleavage_components_text", "cleavage_components_text", ""),
)

OUTPUT_TREES = (
    ("selected_plan_rows", "pm_selected_plan_tree"),
    ("selected_material_rows", "pm_selected_material_tree"),
    ("selected_total_rows", "pm_selected_total_tree"),
    ("selected_checklist_rows", "progress_tree"),
    ("selected_cleavage_rows", "pm_cleavage_tree"),
)


def snapshot(gui, adapter, active_index):
    index = active_index(gui)
    if index is None:
        return
    item = gui.pm_items[index]
    item.update(adapter._editor_payload(gui))
    for item_key, tree_name in OUTPUT_TREES:
        item[item_key] = adapter._tree_rows(getattr(gui, tree_name, None))
    try:
        adapter._refresh_list_label(gui, index)
    except Exception:
        pass


def save_active(
    gui,
    adapter,
    active_index,
    commit_editor,
    *,
    include_outputs=True,
):
    index = active_index(gui)
    if index is None or getattr(gui, "_v229_switching", False):
        return
    gui.pm_items[index].update(adapter._editor_payload(gui))
    if include_outputs:
        commit_editor(gui)
        snapshot(gui, adapter, active_index)


def clear_editor_and_outputs(gui, adapter, set_value):
    gui._v229_switching = True
    try:
        for name in (
            "pm_project", "pm_peptide", "pm_sequence", "pm_scale",
            "pm_resin", "pm_loading", "pm_lot", "pm_chemistry", "pm_copies",
        ):
            set_value(gui, name, "")
        set_value(gui, "cleavage_preset", "")
        set_value(gui, "cleavage_eq_override", "0")
        set_value(gui, "cleavage_components_text", "")
        for _, tree_name in OUTPUT_TREES:
            adapter._clear_tree(getattr(gui, tree_name, None))
        try:
            gui.pm_list.selection_clear(0, "end")
        except Exception:
            pass
        gui._v229_active_index = None
        gui._v229_dirty_columns = {}
    finally:
        gui._v229_switching = False


def restore_item(
    gui,
    index,
    adapter,
    set_value,
    bind_plan_editor,
    namespace,
    *,
    plan_columns,
    plan_widths,
    material_columns,
    material_widths,
    total_columns,
    total_widths,
    check_columns,
    check_widths,
):
    if not (0 <= int(index) < len(gui.pm_items)):
        return
    item = gui.pm_items[int(index)]
    gui._v229_switching = True
    try:
        for name, key, default in EDITOR_FIELDS:
            current = item.get(
                key,
                item.get("lot_no", default) if key == "lot" else default,
            )
            set_value(gui, name, current)
        try:
            gui.apply_loading_calc.set(
                bool(item.get("apply_loading_calc", False))
            )
        except Exception:
            pass
        gui._v229_active_index = int(index)
        gui.pm_list.selection_clear(0, "end")
        gui.pm_list.selection_set(index)
        gui.pm_list.activate(index)
    finally:
        gui._v229_switching = False
    adapter._write_rows(
        gui.pm_selected_plan_tree,
        item.get("selected_plan_rows", []),
        plan_columns,
        plan_widths,
    )
    adapter._write_rows(
        gui.pm_selected_material_tree,
        item.get("selected_material_rows", []),
        material_columns,
        material_widths,
    )
    total_tree = getattr(
        gui, "pm_selected_total_tree", getattr(gui, "pm_total_tree", None)
    )
    adapter._write_rows(
        total_tree,
        item.get("selected_total_rows", []),
        total_columns,
        total_widths,
    )
    adapter._write_rows(
        gui.progress_tree,
        item.get("selected_checklist_rows", []),
        check_columns,
        check_widths,
    )
    adapter._write_rows(
        gui.pm_cleavage_tree,
        item.get("selected_cleavage_rows", []),
    )
    gui._v229_dirty_columns = {}
    bind_plan_editor(gui, namespace)


def live_sync(gui, adapter, active_index):
    if getattr(gui, "_v229_switching", False):
        return
    index = active_index(gui)
    if index is None:
        return
    gui.pm_items[index].update(adapter._editor_payload(gui))
    try:
        adapter._refresh_list_label(gui, index)
        gui.schedule_autosave()
    except Exception:
        pass


__all__ = [
    "EDITOR_FIELDS",
    "OUTPUT_TREES",
    "clear_editor_and_outputs",
    "live_sync",
    "restore_item",
    "save_active",
    "snapshot",
]
