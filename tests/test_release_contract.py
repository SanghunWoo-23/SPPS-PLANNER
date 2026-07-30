from __future__ import annotations


def test_active_release_routes_are_semantic_and_not_legacy_patch_functions():
    from suite_gui.release import SPPSGui
    from suite_gui.release_contract import active_route_report

    report = active_route_report(SPPSGui)
    assert report
    assert all(details["callable"] for details in report.values())
    assert all(
        details["module"] in details["allowed_modules"]
        for details in report.values()
    )
    assert all(
        details["module"] != "suite_gui.legacy_controller"
        for details in report.values()
    )


def test_release_composition_uses_semantic_workflow_boundaries():
    from suite_gui import release_composition
    from suite_gui.modules import classic_workflow, workbench_workflow

    layers = {layer.name: layer for layer in release_composition.RELEASE_LAYERS}
    assert layers["classic_workflow_restore"].installer is classic_workflow.install
    assert (
        layers["fast_legacy_exact_workflow"].installer
        is workbench_workflow.install
    )


def test_active_audit_separates_runtime_routes_from_historical_bindings():
    from tools.audit_monkey_patches import audit_active_release

    report = audit_active_release()
    assert report["route_count"] >= 10
    assert report["legacy_controller_routes"] == []
