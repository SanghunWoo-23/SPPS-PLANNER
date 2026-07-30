"""Single active controller layer for the accepted SPPS Planner V2.0.0 release."""
from __future__ import annotations

from suite_gui.modules import v200_custom_db_tab_restore as custom_db
from suite_gui.modules import v200_final_release as final_ui


def install(gui_cls, ns, *_args, **_kwargs):
    """Compose final UI and Custom DB behavior without nested build wrappers."""
    base_build = gui_cls._build

    final_ui.install(gui_cls, ns, wrap_build=False)
    custom_db_post_build = custom_db.install(
        gui_cls,
        ns,
        wrap_build=False,
        return_post_build=True,
    )

    def build(self):
        base_build(self)
        final_ui.apply_post_build(self, ns)
        custom_db_post_build(self)

    gui_cls._build = build
    gui_cls.TITLE = final_ui.VERSION_LABEL
    return gui_cls
