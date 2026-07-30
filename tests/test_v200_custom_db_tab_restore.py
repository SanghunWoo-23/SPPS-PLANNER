from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v200_custom_db_restore_is_narrow_and_version_fixed():
    module = (ROOT / "suite_gui" / "modules" / "v200_custom_db_tab_restore.py").read_text(encoding="utf-8")
    classic = (ROOT / "suite_gui" / "legacy_controller.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "V2.0.0"' in module
    assert "_v245_add_custom_db_tab" in module
    assert 'data["custom_materials"]' in module
    assert "_compose_release(SPPSGui, globals(), _old_v27_build)" in classic


def test_legacy_custom_material_classes_and_connections_still_exist():
    classic = (ROOT / "suite_gui" / "legacy_controller.py").read_text(encoding="utf-8")
    for category in ["AA/Chemical", "Coupling reagent", "Catalyst/additive", "Base", "Solvent", "Cleavage cocktail", "Resin", "Other"]:
        assert category in classic
    for function_name in [
        "_v245_add_custom_material",
        "_v245_delete_custom_material",
        "_v245_lookup",
        "_v245_custom_options",
        "_v245_refresh_setup_comboboxes",
    ]:
        assert f"def {function_name}" in classic
