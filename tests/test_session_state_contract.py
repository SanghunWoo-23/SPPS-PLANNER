from __future__ import annotations

import json

from suite_gui.session_state import SessionStateMixin


class Variable:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Listbox:
    def curselection(self):
        return (1,)


class SessionHarness(SessionStateMixin):
    def __init__(self, path):
        self.state_file = path
        self.project_name = Variable("Project-001")
        self.seq = Variable("Ac-EEMQRR-NH2")
        self.pm_items = [{"project": "Project-001", "sequence": "Ac-EEMQRR-NH2"}]
        self.pm_list = Listbox()
        self.synced = 0
        self.closed = 0
        self.logs = []

    def pm_live_sync_selected(self):
        self.synced += 1

    def _batch_rows_from_tree(self):
        return [{"Project": "Project-001", "Scale mmol": "0.2"}]

    def _log(self, message):
        self.logs.append(message)

    def destroy(self):
        self.closed += 1


def test_session_state_keeps_the_accepted_json_shape(tmp_path):
    harness = SessionHarness(tmp_path / "session.json")
    state = harness._collect_state()

    assert harness.synced == 1
    assert state["app_version"] == "V3.0.0"
    assert state["selected_pm_index"] == 1
    assert state["pm_items"] == harness.pm_items
    assert state["batch_rows"] == [
        {"Project": "Project-001", "Scale mmol": "0.2"}
    ]
    assert state["defaults"]["project_name"] == "Project-001"
    assert state["defaults"]["seq"] == "Ac-EEMQRR-NH2"


def test_session_save_is_atomic_and_close_saves_before_destroy(tmp_path):
    path = tmp_path / "session.json"
    harness = SessionHarness(path)

    harness.save_autosave_state()
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["app_version"] == "V3.0.0"
    assert not path.with_suffix(".tmp").exists()

    harness.on_close()
    assert harness.closed == 1
    assert path.exists()
