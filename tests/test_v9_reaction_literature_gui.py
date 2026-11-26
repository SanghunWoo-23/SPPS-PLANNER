"""Display-backed GUI regression: risk and references visible to operator."""
import os
import tkinter as tk
from tkinter import ttk
import pytest

@pytest.mark.skipif(not os.environ.get('DISPLAY'), reason='requires active Tk display')
def test_reaction_editor_displays_hcn_flag_and_primary_literature_url():
    from suite_gui.reaction_method_editor_v9 import open_reaction_method_editor
    root=tk.Tk();root.withdraw()
    try:
        d=open_reaction_method_editor(root,sequence='dS-dV-dS',resin='2-CTC',
              scale_mmol=.1,copies=1,side_chain_mode='catalog',on_save=lambda _:None)
        def walk(parent):
            for w in parent.winfo_children():
                yield w
                yield from walk(w)
        combobox=next(w for w in walk(d) if isinstance(w,ttk.Combobox))
        combobox.set('DIC / Oxyma Pure')
        for w in walk(d):
            if not isinstance(w,ttk.Entry) or isinstance(w,ttk.Combobox):continue
            if w.master is combobox.master:
                grid=w.grid_info(); key=(int(grid['row']),int(grid['column']))
                value={(1,1):'1',(1,3):'DMF',(2,1):'12',(2,3):'20'}[key]
            else:
                value='3'
            w.delete(0,'end');w.insert(0,value)
        button=next(w for w in walk(d) if isinstance(w,ttk.Button) and w.cget('text')=='Preview quantities')
        button.invoke()
        output=next(w for w in walk(d) if isinstance(w,tk.Text))
        rendered=output.get('1.0','end')
        assert '[HIGH] DIC_OXYMA_HCN' in rendered
        assert 'cyclic_dimer_two_links' in rendered
        assert 'https://doi.org/10.1021/acs.oprd.0c00227' in rendered
        d.destroy()
    finally:
        root.destroy()
