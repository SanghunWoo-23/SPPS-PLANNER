from suite_gui.runtime_selftest import run, BUILD_REVISION


def test_packaged_runtime_selftest_contract_is_current_and_passing():
    report = run()
    assert report["app_version"] == "V9.0.0"
    assert report["build_revision"] == BUILD_REVISION and "v9.0.0" in BUILD_REVISION
    assert report["checks"]["v9_reaction_method_roundtrip"] is True
    assert report["checks"]["v9_protected_cyclic_mass"] is True
    assert report["checks"]["v9_yield_is_operator_only"] is True
    assert report["checks"]["terminal_ac_plan"] is True
    assert report["checks"]["terminal_pal_plan"] is True
    assert report["ok"] is True
