"""V2.2.15 historical CTC alias compatibility.

The removed CTC(합성용) label is accepted only when reading older data and is
immediately migrated to the surviving CTC(합성기) resin profile.
"""
from __future__ import annotations

APP_VERSION = "V2.2.15"
VERSION_LABEL = "SPPS Planner GitHub V2.2.15"


def _preserve_operator_resin(value):
    text = str(value or "").strip()
    if text in {"CTC(합성용)", "CTC 합성용", "CTC-synthesis", "CTC synthesis"}:
        return "CTC(합성기)"
    return text or "Rink Amide AM"


def install(gui_cls, ns, *_a, **_k):
    # Migrate the removed historical label to the sole surviving synthesizer option.
    for name in (
        "_v224_normalize_saved_resin",
        "_v226_normalize_resin",
        "_v281_resin_display",
        "_v282_resin_display",
    ):
        if name in ns:
            ns[name] = _preserve_operator_resin

    old_build = gui_cls._build
    def build(self):
        old_build(self)
        try:
            self.title(VERSION_LABEL)
        except Exception:
            pass
    gui_cls._build = build
    gui_cls.TITLE = VERSION_LABEL
    return gui_cls
