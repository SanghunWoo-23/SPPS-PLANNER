"""Controller-facing V5 experimental-data workflow."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from suite_gui import experimental_data, ml_advisor_v5, condition_optimizer_v5, model_registry_v5

_SEEDED_DB_PATHS: set[str] = set()


def db_path(gui: Any = None) -> Path:
    override = getattr(gui, "experimental_db_path", None) if gui is not None else None
    return Path(override) if override else experimental_data.default_db_path()


def initialize(gui: Any = None) -> Path:
    path = experimental_data.initialize(db_path(gui))
    try:
        cache_key = str(Path(path).expanduser().resolve())
    except Exception:
        cache_key = str(path)
    if cache_key in _SEEDED_DB_PATHS:
        return path
    from spps_planner.build_profile import BUNDLE_EXPERIMENTAL_SEEDS
    if not BUNDLE_EXPERIMENTAL_SEEDS:
        _SEEDED_DB_PATHS.add(cache_key)
        return path
    # Private seed observations are imported as Parsed evidence, never silently
    # promoted to Verified. Public ships the same code with an empty seed folder.
    root = Path(__file__).resolve().parents[1] / "apps" / "spps_planner_app" / "data" / "experimental_seed"
    for seed in (
        root / "loading_history_seed.csv",
        root / "Cleavage_Report_seed.xlsx",
        root / "synthesis_sequence_history_seed.csv",
        root / "cleavage_usage_seed.csv",
    ):
        if not seed.is_file():
            continue
        try:
            experimental_data.import_path(seed, path)
        except Exception as exc:
            try:
                gui._log(f"Bundled experimental seed import warning: {seed}: {exc}\n")
            except Exception:
                _seed_import_log_error = exc
    _SEEDED_DB_PATHS.add(cache_key)
    return path


def data_health(gui: Any) -> dict[str, Any]:
    return experimental_data.data_health(db_path(gui))


def preview_import(gui: Any, path: str | Path) -> dict[str, Any]:
    return experimental_data.preview_path(path)


def import_file(gui: Any, path: str | Path) -> list[dict[str, Any]]:
    result = experimental_data.import_path(path, db_path(gui))
    try:
        gui._log(f"Experimental data import: {path} -> {result}\n")
    except Exception as exc:
        _ignored_log_error = exc
    return result


def loading_records(gui: Any, statuses=None):
    return experimental_data.list_records("loading", db_path(gui), statuses=statuses)


def cleavage_records(gui: Any, statuses=None):
    return experimental_data.list_records("cleavage", db_path(gui), statuses=statuses)


def sequence_records(gui: Any, statuses=None):
    return experimental_data.list_records("sequence", db_path(gui), statuses=statuses)

def cleavage_usage_records(gui: Any, statuses=None):
    return experimental_data.list_records("cleavage_usage", db_path(gui), statuses=statuses)

def outcome_records(gui: Any, statuses=None):
    return experimental_data.list_records("outcome", db_path(gui), statuses=statuses)

def issue_records(gui: Any, statuses=None):
    return experimental_data.list_records("issue", db_path(gui), statuses=statuses)

def review_cleavage_usage_units(gui: Any, record_id: str, units: dict[str,str]):
    return experimental_data.review_cleavage_usage_units(record_id, units, db_path(gui))

def validation_snapshot(gui: Any):
    return ml_advisor_v5.validation_snapshot(db_path(gui))

def similar_experiments(gui: Any, sequence: str, limit: int = 12):
    return ml_advisor_v5.similar_experiments(sequence, db_path=db_path(gui), limit=limit)

def sequence_difficulty(gui: Any, sequence: str):
    return ml_advisor_v5.sequence_difficulty_map(sequence)

def loading_model_info(gui: Any = None):
    return model_registry_v5.loading_model_info()

def loading_rebuild_status(gui: Any = None):
    return model_registry_v5.loading_rebuild_status(db_path(gui))

def rebuild_loading_model(gui: Any = None):
    return model_registry_v5.rebuild_loading_model(db_path(gui))

def stage_risks(gui: Any, sequence: str):
    try:
        from suite_gui.modules import gui_common
        gui_common.save_active(gui)
        items=list(getattr(gui, "pm_items", []) or [])
        idx=gui_common.active_index(gui)
        item=items[int(idx)] if idx is not None and 0 <= int(idx) < len(items) else {}
    except Exception:
        item={}
    return ml_advisor_v5.stage_risk_advisor(
        sequence=sequence, product=str(item.get("peptide") or getattr(getattr(gui,"pm_peptide",None),"get",lambda:"")()),
        resin=str(item.get("resin") or getattr(getattr(gui,"pm_resin",None),"get",lambda:"")()),
        scale_mmol=item.get("scale") or getattr(getattr(gui,"pm_scale",None),"get",lambda:"")(),
        selected_plan_rows=item.get("selected_plan_rows") or [], db_path=db_path(gui),
    )

def loading_model_history(gui: Any = None):
    return model_registry_v5.loading_model_history()

def promote_latest_loading_candidate(gui: Any = None):
    return model_registry_v5.promote_latest_loading_candidate()


def rollback_loading_model(gui: Any = None):
    return model_registry_v5.rollback_loading_model()



def active_run_context(gui: Any) -> dict[str, str]:
    """Return the active Work Item/Run identity without exposing it in simple UI.

    Every result/issue recorded through the V5 workflow is tagged to this run so
    later evidence can be traced back to the exact plan snapshot.
    """
    try:
        from suite_gui import data_system
        from suite_gui.modules import gui_common
        gui_common.save_active(gui)
        items=list(getattr(gui, "pm_items", []) or [])
        idx=gui_common.active_index(gui)
        if idx is None or not (0 <= int(idx) < len(items)):
            return {"work_item_id":"", "run_id":"", "run_name":""}
        item=items[int(idx)]
        run=data_system.sync_active_run(item)
        return {
            "work_item_id":str(item.get("work_item_id") or ""),
            "run_id":str(run.get("run_id") or ""),
            "run_name":str(run.get("name") or ""),
        }
    except Exception:
        return {"work_item_id":"", "run_id":"", "run_name":""}


def _attach_run_context(gui: Any, values: dict[str, Any]) -> dict[str, Any]:
    payload=dict(values)
    context=active_run_context(gui)
    if not str(payload.get("work_item_id") or "").strip():
        payload["work_item_id"]=context.get("work_item_id", "")
    if not str(payload.get("run_id") or "").strip():
        payload["run_id"]=context.get("run_id", "")
    return payload


def set_status(gui: Any, kind: str, ids, status: str) -> int:
    return experimental_data.set_status(kind, ids, status, db_path(gui))

def update_record(gui: Any, kind: str, record_id: str, changes: dict[str, Any]):
    return experimental_data.update_record(kind, record_id, changes, db_path(gui))



def add_loading_record(gui: Any, values: dict[str, Any], *, status: str = "verified"):
    return experimental_data.add_record("loading", _attach_run_context(gui, values), db_path(gui), status=status)


def add_cleavage_record(gui: Any, values: dict[str, Any], *, status: str = "verified"):
    return experimental_data.add_record("cleavage", _attach_run_context(gui, values), db_path(gui), status=status)

def add_outcome_record(gui: Any, values: dict[str, Any], *, status: str = "verified"):
    return experimental_data.add_outcome(_attach_run_context(gui, values), db_path(gui), status=status)

def add_issue_record(gui: Any, values: dict[str, Any], *, status: str = "verified"):
    return experimental_data.add_issue(_attach_run_context(gui, values), db_path(gui), status=status)


def record_coupling_review(gui: Any, *, actual_yield_percent: Any = None, actual_purity_percent: Any = None, failure_flag: Any = None, doubling_required: Any = None, operator_note: str = ""):
    """Record a simple operator coupling outcome on the active Work Item."""
    from suite_gui import ml_dataset
    from suite_gui.modules import gui_common
    gui_common.save_active(gui)
    items = list(getattr(gui, "pm_items", []) or [])
    idx = gui_common.active_index(gui)
    if idx is None or not (0 <= int(idx) < len(items)):
        raise ValueError("Select a peptide item before recording a coupling result.")
    item = items[int(idx)]
    version = ml_dataset.review_item(
        item, actual_yield_percent=actual_yield_percent, actual_purity_percent=actual_purity_percent,
        failure_flag=failure_flag, doubling_required=doubling_required, included=True,
        review_reason="Operator lab result entry", operator_note=operator_note,
    )
    gui_common.save_active(gui)
    def _tri(value):
        text=str(value or '').strip().lower()
        if text in {'yes','y','true','1','fail','failed'}: return 1
        if text in {'no','n','false','0','success','passed'}: return 0
        return None
    try:
        context=active_run_context(gui)
        experimental_data.add_outcome({
            "stage": "coupling", "product": item.get("peptide", ""), "sequence": item.get("sequence", ""),
            "work_item_id": item.get("work_item_id", ""), "run_id": context.get("run_id", ""), "result": "failed" if _tri(failure_flag)==1 else "completed" if _tri(failure_flag)==0 else "recorded",
            "success_flag": (0 if _tri(failure_flag)==1 else 1 if _tri(failure_flag)==0 else None),
            "yield_percent": actual_yield_percent, "purity_percent": actual_purity_percent,
            "doubling_required": _tri(doubling_required), "observation": operator_note,
            "source_locator": "Record Coupling / active Work Item",
        }, db_path(gui), status="verified")
    except Exception as exc:
        try: gui._log(f"V5 coupling outcome DB warning: {exc}\n")
        except Exception: pass
    return version

def advise_loading(gui: Any, **query: Any):
    return ml_advisor_v5.loading_advice(db_path=db_path(gui), **query)


def advise_cleavage(gui: Any, **query: Any):
    return ml_advisor_v5.cleavage_advice(db_path=db_path(gui), **query)


def recommend_loading(gui: Any, **query: Any):
    return ml_advisor_v5.loading_recommendation(db_path=db_path(gui), **query)


def recommend_cleavage(gui: Any, **query: Any):
    return ml_advisor_v5.cleavage_recommendation(db_path=db_path(gui), **query)


def advise_coupling(gui: Any):
    try:
        from suite_gui.modules import gui_common
        gui_common.save_active(gui)
    except Exception as exc:
        try:
            gui._log(f"Coupling advisor save-active warning: {exc}\n")
        except Exception as log_exc:
            _coupling_save_log_error = log_exc
    items = list(getattr(gui, "pm_items", []) or [])
    active = None
    try:
        from suite_gui.modules import gui_common
        idx = gui_common.active_index(gui)
        if idx is not None and 0 <= int(idx) < len(items):
            active = items[int(idx)]
    except Exception as exc:
        active = None
        try:
            gui._log(f"Coupling advisor active-item warning: {exc}\n")
        except Exception as log_exc:
            _coupling_active_log_error = log_exc
    if active is None:
        active = {
            "sequence": getattr(getattr(gui, "pm_sequence", None), "get", lambda: "")(),
            "resin": getattr(getattr(gui, "pm_resin", None), "get", lambda: "")(),
        }
    return condition_optimizer_v5.coupling_advice(items, active)


def open_window(gui: Any) -> Any:
    from suite_gui.modules.experimental_data_panel import ExperimentalDataWindow
    existing = getattr(gui, "_experimental_data_window", None)
    if existing is not None:
        try:
            if existing.winfo_exists():
                existing.deiconify(); existing.lift(); return existing
        except Exception as exc:
            _ignored_window_probe_error = exc
    window = ExperimentalDataWindow(gui)
    gui._experimental_data_window = window
    return window


def open_advisor(gui: Any, kind: str) -> Any:
    window = open_window(gui)
    try:
        window.focus_advisor(kind)
    except Exception as exc:
        try:
            gui._log(f"Experimental advisor focus warning: {exc}\n")
        except Exception as log_exc:
            _ignored_focus_log_error = log_exc
    return window


def open_condition_optimizer(gui: Any) -> Any:
    window = open_window(gui)
    try:
        window.focus_optimizer()
    except Exception as exc:
        try:
            gui._log(f"Condition optimizer focus warning: {exc}\n")
        except Exception as log_exc:
            _condition_optimizer_log_error = log_exc
    return window

__all__ = ["initialize", "data_health", "preview_import", "import_file", "loading_records", "cleavage_records", "sequence_records", "cleavage_usage_records", "outcome_records", "issue_records", "review_cleavage_usage_units", "validation_snapshot", "similar_experiments", "sequence_difficulty", "stage_risks", "loading_model_info", "loading_rebuild_status", "loading_model_history", "rebuild_loading_model", "promote_latest_loading_candidate", "rollback_loading_model", "active_run_context", "set_status", "update_record", "add_loading_record", "add_cleavage_record", "add_outcome_record", "add_issue_record", "record_coupling_review", "advise_loading", "advise_cleavage", "recommend_loading", "recommend_cleavage", "advise_coupling", "open_window", "open_advisor", "open_condition_optimizer", "db_path"]
