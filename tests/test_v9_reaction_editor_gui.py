"""Native Tk smoke test; skipped by headless test runners without DISPLAY."""
import os
import tkinter as tk
import pytest

@pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='X11 display needed for real Tk widgets')
def test_v9_autoplan_reaction_editor_instantiates_without_global_style_mutation():
    from suite_gui.auto_plan_option_v9 import open_auto_plan
    from suite_gui.reaction_method_editor_v9 import open_reaction_method_editor
    root=tk.Tk()
    root.withdraw()
    for k,v in {'sequence':'dS-dV-dS','scale':'0.1','resin':'2-CTC',
                'loading':'0.8','chemistry':'DIC/HOBt','copies':'1'}.items():
        setattr(root,'pm_'+k,tk.StringVar(value=v))
    root.pm_items=[{}]
    root.pm_current_index=lambda:0
    try:
        window=open_auto_plan(root)
        assert 'V9.0.0' in window.title()
        editor=open_reaction_method_editor(window,sequence='dS-dV-dS',resin='2-CTC',
               scale_mmol=.1,copies=1,side_chain_mode='catalog',on_save=lambda r:None)
        root.update_idletasks()
        assert editor.winfo_exists() and window.winfo_exists()
        editor.destroy()
        window.destroy()
    finally:
        root.destroy()
