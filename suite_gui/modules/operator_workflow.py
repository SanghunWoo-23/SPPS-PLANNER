"""Flattened operator-facing post-build workflow for the accepted release."""
from __future__ import annotations

from suite_gui.modules import final_plan_adjustments
from suite_gui.modules import project_manager_workflow
from suite_gui.modules import v2211_function_preserved_safe_clean as safe_clean
from suite_gui.modules import v2213_operator_final_restore as operator_restore
from suite_gui.modules import plan_workflow


APP_VERSION = "V2.2.15"
VERSION_LABEL = "SPPS Planner GitHub V2.2.15"


def install(
    gui_cls,
    namespace,
    original_build=None,
    *,
    wrap_build=True,
    return_post_build=False,
):
    """Apply four historical layers but retain only one active build wrapper."""

    base_build = gui_cls._build

    # Preserve every non-build side effect and public method route in the exact
    # historical order. Their temporary build wrappers are flattened below.
    safe_clean.install(gui_cls, namespace, original_build)
    project_manager_workflow.install(gui_cls, namespace, original_build)
    operator_restore.install(gui_cls, namespace, original_build)
    final_plan_adjustments.install(gui_cls, namespace, original_build)

    def apply_post_build(self):
        safe_clean.apply_post_build(self)
        project_manager_workflow.apply_post_build(
            self,
            plan_workflow,
            namespace,
        )
        operator_restore.apply_post_build(self)
        final_plan_adjustments.apply_post_build(self)

    def build(self):
        base_build(self)
        apply_post_build(self)

    # The historical installers above temporarily wrap _build. Restore the
    # caller's build when a semantic composer requests post-build behavior only.
    gui_cls._build = build if wrap_build else base_build
    gui_cls.TITLE = VERSION_LABEL
    if return_post_build:
        return apply_post_build
    return gui_cls


__all__ = ["install"]
