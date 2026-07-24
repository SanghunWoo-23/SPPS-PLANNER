from types import SimpleNamespace

import suite_gui.classic_2094_tk_gui as gui_mod


class Var:
    def __init__(self, value=''):
        self.value = value
    def set(self, value):
        self.value = value
    def get(self):
        return self.value


def _fake_gui():
    calls = {'autosave': 0}
    gui = SimpleNamespace(
        pm_chemistry=Var(''),
        default_reagent=Var(''),
        default_catalyst=Var(''),
        default_base=Var(''),
        default_coupling_solution_solvent=Var(''),
        coupling_eq=Var(''),
        default_reagent_eq=Var(''),
        default_reagent_count=Var(''),
        default_catalyst_eq=Var(''),
        default_catalyst_count=Var(''),
        default_base_eq=Var(''),
        default_base_count=Var(''),
        batch_hbtu_eq=Var(''),
        batch_hbtu_conc=Var(''),
        schedule_autosave=lambda: calls.__setitem__('autosave', calls['autosave'] + 1),
    )
    return gui, calls


def test_dic_hobt_button_updates_chemistry_without_generating_plan(monkeypatch):
    gui, calls = _fake_gui()
    generated = {'count': 0}
    monkeypatch.setattr(gui_mod, '_v218_generate', lambda *_a, **_k: generated.__setitem__('count', generated['count'] + 1))
    monkeypatch.setattr(gui_mod, '_v2093_save_active', lambda *_a, **_k: None)

    gui_mod._v218_apply_dic_hobt_preset(gui)

    assert generated['count'] == 0
    assert gui.pm_chemistry.get() == 'DIC/HOBt'
    assert gui.default_reagent.get() == 'DIC'
    assert gui.default_catalyst.get() == 'HOBt'
    assert gui.default_coupling_solution_solvent.get() == 'DMF'
    assert calls['autosave'] == 1


def test_hbtu_nmp_button_updates_chemistry_without_generating_plan(monkeypatch):
    gui, calls = _fake_gui()
    generated = {'count': 0}
    monkeypatch.setattr(gui_mod, '_v218_generate', lambda *_a, **_k: generated.__setitem__('count', generated['count'] + 1))
    monkeypatch.setattr(gui_mod, '_v2093_save_active', lambda *_a, **_k: None)

    gui_mod._v218_apply_hbtu_nmp_preset(gui)

    assert generated['count'] == 0
    assert gui.pm_chemistry.get() == 'HBTU/NMP 10eq'
    assert gui.default_reagent.get() == 'HBTU'
    assert gui.default_base.get() == 'DIEA'
    assert gui.default_coupling_solution_solvent.get() == 'NMP'
    assert gui.batch_hbtu_eq.get() == '10'
    assert gui.batch_hbtu_conc.get() == '0.4'
    assert calls['autosave'] == 1
