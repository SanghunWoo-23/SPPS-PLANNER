from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v4_ml_entry_is_visible_in_primary_action_row():
    text = (ROOT / 'suite_gui' / 'modules' / 'workspace_widgets.py').read_text(encoding='utf-8')
    assert 'Experimental / ML (V4)' in text
    assert 'command=gui.open_experimental_data' in text


def test_v4_startup_explicitly_clears_previous_outputs_after_initialization():
    text = (ROOT / 'suite_gui' / 'ui_build.py').read_text(encoding='utf-8')
    init_pos = text.index('initialize_experimental_data(gui)')
    clear_pos = text.index('plan_workflow._clear_editor_and_outputs(gui)', init_pos)
    theme_pos = text.index('ui_system.apply_theme(gui, "Standard")', clear_pos)
    assert init_pos < clear_pos < theme_pos


def test_checklist_progress_is_reset_when_outputs_are_cleared():
    text = (ROOT / 'suite_gui' / 'peptide_item_state.py').read_text(encoding='utf-8')
    assert 'gui.checklist_progress_var.set(0.0)' in text
    assert 'Progress: 0/0 (0.0%)' in text
