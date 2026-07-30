"""UI-independent JSON persistence for planner sessions and projects."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def normalize_items(items: Iterable[Any] | None) -> list[dict[str, Any]]:
    """Copy dictionary rows and discard malformed entries."""
    return [dict(item) for item in (items or []) if isinstance(item, Mapping)]


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object; a non-object root represents an empty state."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return dict(data) if isinstance(data, Mapping) else {}


def atomic_write_json(path: Path, state: Mapping[str, Any]) -> Path:
    """Write readable UTF-8 JSON and atomically replace the destination."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(dict(state), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination


def project_state(
    *,
    app_version: str,
    saved_at: str,
    selected_pm_index: int,
    pm_items: Iterable[Any] | None,
    defaults: Mapping[str, Any] | None = None,
    batch_rows: Iterable[Any] | None = None,
    active_index: int | None = None,
    base: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the legacy-compatible state envelope used by save actions."""
    state = dict(base or {})
    state.update(
        {
            "app_version": app_version,
            "saved_at": saved_at,
            "selected_pm_index": int(selected_pm_index),
            "pm_items": normalize_items(pm_items),
            "defaults": dict(defaults or {}),
        }
    )
    if batch_rows is not None:
        state["batch_rows"] = normalize_items(batch_rows)
    if active_index is not None:
        state["active_index"] = int(active_index)
    return state


__all__ = [
    "atomic_write_json",
    "normalize_items",
    "project_state",
    "read_json_object",
]
