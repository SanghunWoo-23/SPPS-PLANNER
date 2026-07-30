"""Single active planning/operator workflow for the accepted desktop release."""
from __future__ import annotations

from suite_gui.modules import operator_workflow
from suite_gui.modules import plan_workflow


PLAN_VERSION = "V2.2.9"
PLAN_TITLE = (
    "SPPS Planner GitHub V2.2.9 - Full Classic UI + Empty Start + "
    "Exact Apply Sync"
)
OPERATOR_VERSION = "V2.2.15"
OPERATOR_TITLE = "SPPS Planner GitHub V2.2.15"


def install(gui_cls, namespace, original_build):
    """Install plan routes and operator routes with one active build wrapper."""
    namespace["APP_VERSION"] = PLAN_VERSION
    namespace["VERSION_LABEL"] = PLAN_TITLE
    gui_cls.TITLE = PLAN_TITLE
    plan_build = plan_workflow.install(
        gui_cls,
        namespace,
        original_build,
        wrap_build=False,
        return_build=True,
    )

    namespace["APP_VERSION"] = OPERATOR_VERSION
    namespace["VERSION_LABEL"] = OPERATOR_TITLE
    gui_cls.TITLE = OPERATOR_TITLE
    operator_post_build = operator_workflow.install(
        gui_cls,
        namespace,
        original_build,
        wrap_build=False,
        return_post_build=True,
    )

    def build(self):
        plan_build(self)
        operator_post_build(self)

    gui_cls._build = build
    gui_cls.TITLE = OPERATOR_TITLE
    return gui_cls


__all__ = ["install"]
