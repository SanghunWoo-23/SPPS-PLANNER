"""Canonical SPPS Planner desktop release surface.

The historical implementation still contains the accepted GUI and calculation
behaviour.  This module gives launchers, tests, and future refactors one stable
import boundary so callers no longer depend on a version-named implementation
module.
"""
from __future__ import annotations

from suite_gui.legacy_controller import SPPSGui, main
from suite_gui.release_contract import validate_release_controller


validate_release_controller(SPPSGui)


def launch() -> None:
    """Launch the fully composed desktop application."""
    main()


__all__ = ["SPPSGui", "main", "launch"]
