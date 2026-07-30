"""Semantic boundary for the accepted classic calculation baseline.

The implementation retains its historical filename for import compatibility.
Release composition imports this module so new code does not depend on a
version-numbered module name.
"""
from __future__ import annotations

from suite_gui.modules.v227_classic_workflow_restore import install

__all__ = ["install"]
