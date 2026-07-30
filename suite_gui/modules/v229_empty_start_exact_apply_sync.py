"""Backward-compatible alias for the accepted plan workflow."""
from __future__ import annotations

import sys

from suite_gui.modules import plan_workflow as _implementation

sys.modules[__name__] = _implementation
