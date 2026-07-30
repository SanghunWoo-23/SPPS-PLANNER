"""Restore the accepted legacy Custom DB tab for SPPS Planner V2.0.0.

The underlying custom-material implementation already exists in the accepted
11:27 FINAL_CTC_OPTION_FIX source. Later setup-panel/session layers only stopped
the visible tab from being reattached and stopped persisting its data. This
narrow final layer restores that legacy UI and its autosave field without
changing synthesis calculations, project behavior, resin rules, or versioning.
"""
from __future__ import annotations

import json

APP_VERSION = "V2.0.0"


def install(
    gui_cls,
    ns,
    *_args,
    wrap_build=True,
    return_post_build=False,
    **_kwargs,
):
    old_build = gui_cls._build
    old_save = gui_cls.save_autosave_state
    init_custom = ns.get("_v245_init_custom_db")
    add_tab = ns.get("_v245_add_custom_db_tab")
    refresh = ns.get("_v245_refresh_setup_comboboxes")
    fix_setup_button = ns.get("_v219_fix_setup_button")

    try:
        from suite_gui.modules import v229_empty_start_exact_apply_sync as v229
    except Exception:
        v229 = None

    def session_path(self):
        if v229 is not None:
            try:
                return v229._session_path(self)
            except Exception:
                pass
        return getattr(self, "state_file", None)

    def load_custom(self):
        try:
            if callable(init_custom):
                init_custom(self)
            path = session_path(self)
            if path is not None and path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                custom = data.get("custom_materials", {}) if isinstance(data, dict) else {}
                if isinstance(custom, dict):
                    self.custom_materials = custom
        except Exception:
            pass

    def merge_custom_into_session(self, path=None):
        try:
            path = path or session_path(self)
            if path is None:
                return path
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if path.exists():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    data = {}
            if not isinstance(data, dict):
                data = {}
            if callable(init_custom):
                init_custom(self)
            data["custom_materials"] = dict(getattr(self, "custom_materials", {}) or {})
            temp = path.with_suffix(path.suffix + ".tmp")
            temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            temp.replace(path)
            return path
        except Exception:
            return path

    def save_autosave_state(self):
        path = None
        try:
            path = old_save(self)
        except Exception:
            path = session_path(self)
        return merge_custom_into_session(self, path)

    def schedule_autosave(self):
        try:
            pending = getattr(self, "_autosave_after_id", None)
            if pending:
                self.after_cancel(pending)
        except Exception:
            pass
        try:
            self._autosave_after_id = self.after(700, lambda _self=self: save_autosave_state(_self))
        except Exception:
            self._autosave_after_id = None

    def restore(self):
        try:
            if callable(init_custom):
                init_custom(self)
            if callable(add_tab):
                add_tab(self)
            if callable(refresh):
                refresh(self)
        except Exception:
            # Never block the accepted planner from opening because of the
            # optional custom-material editor.
            pass

    def pin_setup_button(self):
        """Keep the existing setup toggle in one fixed position and width.

        The accepted legacy toggle already owns the correct show/hide command.
        This final layout-only step calls that existing position normalizer once
        at startup and gives the button a fixed width so changing its text from
        Show setup to Hide setup cannot move it.
        """
        try:
            if callable(fix_setup_button):
                fix_setup_button(self)
            button = getattr(self, "setup_toggle_btn", None)
            if button is not None:
                button.configure(width=10)
        except Exception:
            pass

    def restore_and_pin(self):
        restore(self)
        pin_setup_button(self)

    def build(self):
        old_build(self)
        apply_post_build(self)

    def apply_post_build(self):
        load_custom(self)
        restore_and_pin(self)
        # Some accepted legacy layers finish rebuilding Setup on idle. Reassert
        # only the missing Custom DB tab and the same fixed toggle placement.
        _schedule_restore(self, restore_and_pin)

    if wrap_build:
        gui_cls._build = build
    gui_cls.save_autosave_state = save_autosave_state
    gui_cls.schedule_autosave = schedule_autosave
    gui_cls.restore_custom_db_tab = restore
    if return_post_build:
        return apply_post_build
    return gui_cls


def _schedule_restore(gui, restore_and_pin):
    """Reassert the accepted Custom DB tab after legacy idle rebuilds."""
    try:
        gui.after_idle(lambda _gui=gui: restore_and_pin(_gui))
        for delay in (120, 450):
            gui.after(delay, lambda _gui=gui: restore_and_pin(_gui))
    except Exception:
        pass
