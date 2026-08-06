"""Direct export route for the accepted V3.0.0 visible workspace."""
from __future__ import annotations

from typing import Any

from suite_gui import calculation_context
from suite_gui.modules import plan_workflow


def export(gui: Any, *_args: Any, **_kwargs: Any) -> Any:
    """Export visible edited tables through the accepted V3.0.0 exporter."""
    sync = getattr(gui, "_sync_modifier_to_aa", None)
    if callable(sync):
        sync()
    return plan_workflow.export_outputs(gui, calculation_context.namespace())


__all__ = ["export"]
