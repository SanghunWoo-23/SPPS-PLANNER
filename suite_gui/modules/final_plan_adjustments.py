"""Combined final parser, resin, and checklist adjustments.

This replaces two consecutive class-build wrappers with one equivalent layer.
"""
from __future__ import annotations

import re

from suite_gui.modules import v2213_operator_final_restore as operator_restore
from suite_gui.modules.v2214_final_three_fixes import (
    _compact_checklist,
    _patch_parser,
    _restore_resin_widgets,
)
from suite_gui.modules.v2215_ctc_synthesis_full_sequence_fix import (
    _preserve_operator_resin,
)


APP_VERSION = "V2.2.15"
VERSION_LABEL = "SPPS Planner GitHub V2.2.15"

RESIN_NORMALIZER_NAMES = (
    "_v224_normalize_saved_resin",
    "_v226_normalize_resin",
    "_v281_resin_display",
    "_v282_resin_display",
)


def _only_explicit_fmoc_row(row):
    unit = re.sub(
        r"[^a-z0-9]+",
        "",
        str(row.get("Unit name", "")).lower(),
    )
    return unit in {"fmocremoval", "deprotectiononly"}


def apply_post_build(gui):
    _restore_resin_widgets(gui)
    _compact_checklist(gui)
    try:
        gui.title(VERSION_LABEL)
    except Exception:
        pass


def install(gui_cls, namespace, *_args, **_kwargs):
    """Install the two accepted final corrections with one build wrapper."""

    _patch_parser()
    operator_restore._is_fmoc_removal = _only_explicit_fmoc_row
    for name in RESIN_NORMALIZER_NAMES:
        if name in namespace:
            namespace[name] = _preserve_operator_resin

    previous_build = gui_cls._build

    def build(self):
        previous_build(self)
        apply_post_build(self)

    gui_cls._build = build
    gui_cls.TITLE = VERSION_LABEL
    return gui_cls


__all__ = ["install"]
