"""Backward-compatible alias for the accepted Project Manager workflow."""
from __future__ import annotations

import sys

from suite_gui.modules import project_manager_workflow as _implementation

sys.modules[__name__] = _implementation
