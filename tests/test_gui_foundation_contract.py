from __future__ import annotations


def test_tk_free_constant_preserves_the_legacy_get_contract():
    from suite_gui.gui_primitives import StaticValue, const_var

    marker = object()
    value = const_var(marker)
    assert isinstance(value, StaticValue)
    assert value.get() is marker


def test_legacy_controller_uses_the_shared_gui_foundation():
    from suite_gui import catalogs
    from suite_gui import legacy_controller
    from suite_gui.gui_primitives import EditableTree, StaticValue

    assert legacy_controller.EditableTree is EditableTree
    assert legacy_controller._StaticValue is StaticValue
    assert legacy_controller.SPPSGui.PLAN_COLUMNS is catalogs.PLAN_COLUMNS
    assert legacy_controller.SPPSGui.MATERIAL_COLUMNS is catalogs.MATERIAL_COLUMNS
    assert legacy_controller.SPPSGui.REAGENT_VALUES is catalogs.REAGENT_VALUES
    assert legacy_controller.SPPSGui.CATALYST_VALUES is catalogs.CATALYST_VALUES
    assert legacy_controller.SPPSGui.BASE_VALUES is catalogs.BASE_VALUES
    assert legacy_controller.SPPSGui.DEPRO_VALUES is catalogs.DEPRO_VALUES
    assert legacy_controller.SPPSGui.RATIO_VALUES is catalogs.RATIO_VALUES
    assert legacy_controller.SPPSGui.SOLVENT_VALUES is catalogs.SOLVENT_VALUES
    assert legacy_controller.SPPSGui.MW_FALLBACK is catalogs.MW_FALLBACK
    assert legacy_controller.SPPSGui.LIQUID_DENSITY is catalogs.LIQUID_DENSITY
    assert (
        legacy_controller.SPPSGui.AA_LIKE_LINKER_TOKENS
        is catalogs.AA_LIKE_LINKER_TOKENS
    )
    assert (
        legacy_controller.SPPSGui.CHEMICAL_LABEL_TOKENS
        is catalogs.CHEMICAL_LABEL_TOKENS
    )
    assert (
        legacy_controller.SPPSGui.CHEMICAL_DISPLAY_NAMES
        is catalogs.CHEMICAL_DISPLAY_NAMES
    )


def test_session_foundation_remains_in_the_final_controller_mro():
    from suite_gui.legacy_controller import SPPSGui
    from suite_gui.session_state import SessionStateMixin

    assert SessionStateMixin in SPPSGui.__mro__
    assert callable(SPPSGui._collect_state)
    assert callable(SPPSGui.load_autosave_state)
    assert callable(SPPSGui.on_close)
