"""Compatibility shim for V2.1.9.

Old projects may still import suite_gui.modules.v2095_router. The active GUI no
longer uses this patch router, but this shim preserves the public installer name.
"""
from __future__ import annotations
try:
    from spps_planner.version import VERSION_NAME
except Exception:
    VERSION_NAME = "SPPS Planner GitHub V2.1.9 - UI Rollback to V2.0.94 Layout"
VERSION_LABEL = VERSION_NAME

def install_v2095_router(SPPSGui, ns: dict | None = None) -> None:
    """Compatibility no-op; modern GUI uses suite_gui.modern_tk_gui."""
    try: setattr(SPPSGui, '_v2095_router_installed', True)
    except Exception: pass
