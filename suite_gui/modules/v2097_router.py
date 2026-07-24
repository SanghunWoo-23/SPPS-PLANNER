"""Compatibility shim for V2.1.9 modular GUI actions."""
from __future__ import annotations
try:
    from spps_planner.version import VERSION_NAME
except Exception:
    VERSION_NAME = "SPPS Planner GitHub V2.1.9 - UI Rollback to V2.0.94 Layout"
VERSION_LABEL = VERSION_NAME

def install_v2097_router(SPPSGui, ns: dict | None = None) -> None:
    """Compatibility installer that marks old router imports as handled."""
    try: setattr(SPPSGui, '_v2097_router_installed', True)
    except Exception: pass
