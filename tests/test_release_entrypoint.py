from __future__ import annotations


def test_public_entrypoint_exports_the_canonical_release():
    from suite_gui import release
    from suite_gui import spps_tk_gui

    assert spps_tk_gui.SPPSGui is release.SPPSGui
    assert spps_tk_gui.main is release.main
    assert spps_tk_gui.launch is release.launch


def test_direct_launch_guard_is_after_final_release_composition():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "suite_gui"
        / "legacy_controller.py"
    ).read_text(encoding="utf-8")

    guard = 'if __name__ == "__main__":'
    final_install = "_compose_release(SPPSGui, globals(), _old_v27_build)"
    assert source.count(guard) == 1
    assert source.index(guard) > source.index(final_install)


def test_release_layers_keep_the_accepted_order_and_final_identity():
    from suite_gui.release_composition import RELEASE_LAYERS

    assert [layer.name for layer in RELEASE_LAYERS] == [
        "classic_workflow_restore",
        "fast_legacy_exact_workflow",
        "planner_workflow",
        "final_release_workflow",
    ]
    assert RELEASE_LAYERS[-1].internal_version == "V2.0.0"
    assert RELEASE_LAYERS[-1].title == "SPPS Planner V2.0.0"


def test_final_controller_surface_matches_the_accepted_release():
    from suite_gui.release import SPPSGui

    required_routes = (
        "_build",
        "destroy",
        "generate_update_plan",
        "pm_generate_selected",
        "pm_calculate_all",
        "apply_change",
        "pm_apply_change",
        "export_outputs",
        "pm_on_select",
        "save_autosave_state",
        "schedule_autosave",
        "restore_custom_db_tab",
    )
    assert all(callable(getattr(SPPSGui, name, None)) for name in required_routes)
    assert SPPSGui.TITLE == "SPPS Planner V2.0.0"
    assert SPPSGui.RESIN_VALUES == [
        "Rink Amide AM",
        "Rink Amide MBHA",
        "Rink Amide ChemMatrix",
        "Rink Amide Tentagel",
        "2-CTC",
        "CTC(합성기)",
        "Wang",
        "HMPB",
        "Sieber Amide",
        "PAL resin",
        "Tentagel",
        "Manual",
    ]


def test_historical_workflow_imports_resolve_to_semantic_modules():
    from suite_gui.modules import plan_workflow
    from suite_gui.modules import project_manager_workflow
    from suite_gui.modules import v2212_peptide_items_multiselect_restore
    from suite_gui.modules import v229_empty_start_exact_apply_sync

    assert v229_empty_start_exact_apply_sync is plan_workflow
    assert (
        v2212_peptide_items_multiselect_restore
        is project_manager_workflow
    )


def test_active_build_chain_is_flattened_to_two_composed_layers():
    from suite_gui.release import SPPSGui

    modules = []
    seen = set()

    def visit(function):
        if not callable(function) or id(function) in seen:
            return
        seen.add(id(function))
        module = getattr(function, "__module__", "")
        if module.startswith("suite_gui"):
            modules.append(module)
        for cell in getattr(function, "__closure__", None) or ():
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if callable(value) and getattr(value, "__module__", "").startswith(
                "suite_gui"
            ):
                visit(value)

    visit(SPPSGui._build)
    build_modules = {
        module
        for module in modules
        if module
        in {
            "suite_gui.modules.planner_workflow",
            "suite_gui.modules.final_release_workflow",
        }
    }
    assert build_modules == {
        "suite_gui.modules.planner_workflow",
        "suite_gui.modules.final_release_workflow",
    }
    assert "suite_gui.modules.v2211_function_preserved_safe_clean" not in modules
    assert "suite_gui.modules.project_manager_workflow" not in modules
    assert "suite_gui.modules.v2213_operator_final_restore" not in modules
    assert "suite_gui.modules.final_plan_adjustments" not in modules


def test_final_release_workflow_preserves_post_build_order(monkeypatch):
    from suite_gui.modules import final_release_workflow

    events = []

    class Controller:
        TITLE = ""

        def _build(self):
            events.append("base")

    def install_final(gui_cls, _ns, *, wrap_build):
        assert wrap_build is False
        events.append("install-final")

    def install_custom(
        gui_cls,
        _ns,
        *,
        wrap_build,
        return_post_build,
    ):
        assert wrap_build is False
        assert return_post_build is True
        events.append("install-custom")
        return lambda self: events.append("custom")

    monkeypatch.setattr(final_release_workflow.final_ui, "install", install_final)
    monkeypatch.setattr(
        final_release_workflow.final_ui,
        "apply_post_build",
        lambda _self, _ns: events.append("final"),
    )
    monkeypatch.setattr(
        final_release_workflow.custom_db,
        "install",
        install_custom,
    )

    final_release_workflow.install(Controller, {})
    Controller()._build()

    assert events == [
        "install-final",
        "install-custom",
        "base",
        "final",
        "custom",
    ]


def test_planner_workflow_preserves_versions_and_build_order(monkeypatch):
    from suite_gui.modules import planner_workflow

    events = []
    namespace = {}

    class Controller:
        TITLE = ""

    def original_build(self):
        events.append("original")

    def install_plan(
        gui_cls,
        ns,
        received_original,
        *,
        wrap_build,
        return_build,
    ):
        assert received_original is original_build
        assert wrap_build is False
        assert return_build is True
        events.append(("install-plan", ns["APP_VERSION"], gui_cls.TITLE))
        return lambda self: events.append("plan")

    def install_operator(
        gui_cls,
        ns,
        received_original,
        *,
        wrap_build,
        return_post_build,
    ):
        assert received_original is original_build
        assert wrap_build is False
        assert return_post_build is True
        events.append(("install-operator", ns["APP_VERSION"], gui_cls.TITLE))
        return lambda self: events.append("operator")

    monkeypatch.setattr(planner_workflow.plan_workflow, "install", install_plan)
    monkeypatch.setattr(
        planner_workflow.operator_workflow,
        "install",
        install_operator,
    )

    planner_workflow.install(Controller, namespace, original_build)
    Controller()._build()

    assert events == [
        ("install-plan", "V2.2.9", planner_workflow.PLAN_TITLE),
        ("install-operator", "V2.2.15", planner_workflow.OPERATOR_TITLE),
        "plan",
        "operator",
    ]
    assert namespace["APP_VERSION"] == "V2.2.15"
    assert Controller.TITLE == planner_workflow.OPERATOR_TITLE
