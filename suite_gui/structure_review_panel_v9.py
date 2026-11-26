"""Operator-only molecular topology review UI; never applies laboratory conditions."""
from __future__ import annotations
import json
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from spps_planner.extended_structure_v9 import graph_crosscheck

OPTIONS = {
    'Linear / protected linear': 'linear',
    'Head-to-tail amide': 'head_to_tail',
    'Lys epsilon-amide branch': 'lysine_branch',
    'Main-chain head-to-tail + Lys branch': 'lysine_branch_head_to_tail',
    'Cys–Cys disulfide': 'disulfide',
    'Lys-to-Asp/Glu side-chain lactam': 'sidechain_lactam',
}


def open_structure_review(parent, *, sequence: str, resin: str,
                          side_chain_mode: str = 'explicit',
                          suggested_topology: str = 'linear', on_attach=None):
    win=tk.Toplevel(parent)
    win.title('V9.0.0 | Independent molecular graph review')
    win.geometry('745x560')
    win.minsize(560,420)
    win.transient(parent)
    frame=ttk.Frame(win,padding=12);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Molecular graph cross-check — independent of legacy SPPS engine',
              font=('Segoe UI',12,'bold'),wraplength=680).pack(anchor='w')
    ttk.Label(frame,text='Review-only. Supported groups: Ser/Thr/Tyr(tBu), Asp/Glu(OtBu), Lys(Boc); L/D standard amino acids. '
              'Cys(Acm/StBu/Trt). Main-chain head-to-tail + one Lys branch. Explicit sites are residue positions counting from the N terminus (1-based).',
              wraplength=680).pack(anchor='w',pady=(4,10))
    row=ttk.Frame(frame);row.pack(fill='x')
    ttk.Label(row,text='Topology').pack(side='left')
    chosen=tk.StringVar(value=next((x for x,y in OPTIONS.items() if y==suggested_topology),next(iter(OPTIONS))))
    ttk.Combobox(row,textvariable=chosen,values=list(OPTIONS),state='readonly',width=37).pack(side='left',padx=8)
    ttk.Label(row,text='Site A').pack(side='left')
    a=tk.StringVar();ttk.Entry(row,textvariable=a,width=5).pack(side='left',padx=4)
    ttk.Label(row,text='B').pack(side='left')
    b=tk.StringVar();ttk.Entry(row,textvariable=b,width=5).pack(side='left',padx=4)
    output=ScrolledText(frame,height=17,wrap='word',font=('Consolas',10))
    output.pack(fill='both',expand=True,pady=9)
    output.insert('1.0','Select topology and choose Compute. Disulfide/lactam require explicit sites.\n'
                          'No 3D shape, reactivity, product identity, or experimental completion is asserted.')
    output.configure(state='disabled')
    last={'result':None}
    state=ttk.Label(frame,text='No graph has been reviewed.',wraplength=680)
    state.pack(anchor='w')
    buttons=ttk.Frame(frame);buttons.pack(fill='x',pady=(7,0))
    def compute():
        path=OPTIONS[chosen.get()]
        sites=None
        if path in ('disulfide','sidechain_lactam'):
            try:
                if not (a.get().strip().isdigit() and b.get().strip().isdigit()):
                    raise ValueError('Both reaction site positions must be positive integer indices.')
                sites=(int(a.get().strip()),int(b.get().strip()))
            except ValueError as exc:
                last['result']={'status':'WITHHELD_INVALID_SITES','reason':str(exc)}
        if last['result'] is None or last['result'].get('status')!='WITHHELD_INVALID_SITES':
            last['result']=graph_crosscheck(sequence,resin,topology=path,
                                side_chain_mode=side_chain_mode,sites=sites)
        record={'sequence':sequence,'resin':resin,'side_chain_mode':side_chain_mode,
                'topology':path,'sites':sites,'graph':last['result'],
                'status':'UNAPPROVED_REVIEW_ONLY'}
        last['record']=record
        output.configure(state='normal');output.delete('1.0','end')
        output.insert('1.0',json.dumps(record,indent=2,ensure_ascii=False,allow_nan=False))
        output.configure(state='disabled')
        state.configure(text=f"Cross-check: {last['result']['status']}. No reaction conditions were generated.")
    def refresh(*_):
        last.clear();last['result']=None
        state.configure(text='Topology / reaction sites changed — recompute before attaching.')
    chosen.trace_add('write',refresh)
    a.trace_add('write',refresh)
    b.trace_add('write',refresh)
    def attach():
        if not last.get('record') or not last.get('result') or last['result'].get('status') != 'CROSSCHECK_PASS':
            # All computed failures remain visible in the preview but must never
            # become an approved plan's MW evidence.
            state.configure(text='A successful, current molecular graph review is required before attaching.')
            return
        if on_attach:
            on_attach(dict(last['record']))
        win.destroy()
    ttk.Button(buttons,text='Compute molecular graph',command=compute).pack(side='left')
    ttk.Button(buttons,text='Custom atom-mapped JSON...',
        command=lambda: open_atomic_topology_editor(win,sequence=sequence,resin=resin,on_attach=on_attach)).pack(side='left',padx=6)
    ttk.Button(buttons,text='Attach review to Auto Plan',command=attach).pack(side='left',padx=8)
    ttk.Button(buttons,text='Close',command=win.destroy).pack(side='right')
    return win


def open_atomic_topology_editor(parent, *, sequence: str, resin: str, on_attach=None):
    """Expert opt-in editor for explicit atom-mapped, operator-reviewed graphs.

    Never runs a synthesis method, reads external URLs or auto-converts a sequence.
    JSON must be inspected by the operator; a matching structure is not inferred.
    """
    from tkinter import filedialog, messagebox
    from spps_planner.atomic_topology_v9 import calculate_atomic_topology, load_atomic_topology_json
    from spps_planner.strict_json_v9 import loads_scientific_json
    from spps_planner.monomer_catalog_v9 import import_monomer_catalog, resolve_catalog_tokens
    from pathlib import Path
    window=tk.Toplevel(parent)
    window.title('V9.0.0 | Custom atom-mapped topology (expert review)')
    window.geometry('830x660')
    window.minsize(610,470)
    frame=ttk.Frame(window,padding=10);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Atomic structure JSON — explicitly mapped residues and reaction sites',
              font=('Segoe UI',11,'bold')).pack(anchor='w')
    ttk.Label(frame,text='Operator must confirm the SMILES match the requested peptide, stereo, protections and selected topology. '
                'Results are theoretical ONLY. Unsupported or ambiguous chemistry is withheld.',
              wraplength=770).pack(anchor='w',pady=(5,8))
    example={'monomers':[
        {'name':'L-Ala','smiles':'[NH2:1][C@@H](C)[C:2](=O)[OH:3]'},
        {'name':'Aib','smiles':'[NH2:1]C(C)(C)[C:2](=O)[OH:3]'},
        {'name':'L-Nle','smiles':'[NH2:1][C@@H](CCCC)[C:2](=O)[OH:3]'}],
        'head_to_tail':True}
    editor=ScrolledText(frame,height=13,wrap='none',font=('Consolas',10))
    editor.pack(fill='both',expand=True)
    editor.insert('1.0',json.dumps(example,indent=2,ensure_ascii=False))
    results=ScrolledText(frame,height=11,wrap='word',font=('Consolas',9))
    results.pack(fill='both',expand=True,pady=(7,4))
    results.insert('1.0','Compute for a preview. Do not infer successful cyclization or a validated product.')
    results.config(state='disabled')
    ack=tk.BooleanVar(value=False)
    ttk.Checkbutton(frame,text='I verified that the mapped atoms, molecular structure, termini and protections match my intended product.',
                    variable=ack).pack(anchor='w')
    state={'payload':None,'record':None,'text':None,'catalog':{}}
    status=ttk.Label(frame,text='No validated structure attached.',wraplength=760)
    status.pack(anchor='w',pady=(3,0))
    buttons=ttk.Frame(frame);buttons.pack(fill='x',pady=4)
    def invalidate(_=None):
        state.update(payload=None,record=None,text=None)
        ack.set(False)
    editor.bind('<<Modified>>',lambda _: (invalidate(),editor.edit_modified(False)) if editor.edit_modified() else None)
    def load_file():
        file=filedialog.askopenfilename(parent=window,title='Open explicit topology JSON',filetypes=[('JSON','*.json')])
        if not file:return
        try:
            data=load_atomic_topology_json(file)
            editor.delete('1.0','end');editor.insert('1.0',json.dumps(data,indent=2,ensure_ascii=False))
            invalidate();status.config(text=f'Loaded local file {Path(file).name}; inspect and compute again.')
        except (OSError,ValueError,TypeError) as exc:
            messagebox.showerror('Invalid topology file',str(exc),parent=window)
    def import_catalog():
        file=filedialog.askopenfilename(parent=window,title='Load local amino acid building block catalog',
           filetypes=[('Catalogs','*.xlsx *.csv *.tsv *.json')])
        if not file:return
        try:
            result=import_monomer_catalog(file)
            state['catalog']={row['token']:row for row in result['accepted']}
            invalidate()
            status.config(text=f"Monomers: {result['accepted_count']} valid, {result['rejected_count']} rejected. "
                        'Edit JSON to use {"token":"Aib"}; inspect original stereochemistry and provenance.')
        except (OSError,ValueError,TypeError) as exc:
            messagebox.showerror('Invalid monomer catalog',str(exc),parent=window)
    def compute():
        raw=editor.get('1.0','end-1c')
        try:
            if len(raw.encode('utf-8'))>200_000:raise ValueError('JSON exceeds 200 kB limit.')
            payload=resolve_catalog_tokens(loads_scientific_json(raw),state['catalog'])
            outcome=calculate_atomic_topology(payload)
        except (ValueError,TypeError) as exc:
            payload=None;outcome={'status':'WITHHELD_INVALID_INPUT','reason':str(exc)}
        invalidate()
        results.config(state='normal');results.delete('1.0','end')
        results.insert('1.0',json.dumps(outcome,indent=2,ensure_ascii=False))
        results.config(state='disabled')
        if outcome.get('status')=='ATOM_MAPPED_GRAPH_PASS':
            state.update(payload=payload,text=raw,record={'status':'UNAPPROVED_REVIEW_ONLY',
                'sequence':sequence,'resin':resin,'topology':'atom_mapped_custom',
                'schema':payload,'graph':outcome})
            status.config(text='Graph generated. Review composition and check operator confirmation before attaching.')
        else:
            status.config(text=f"Withheld: {outcome.get('reason',outcome.get('status'))}")
    def attach():
        if not state['record'] or not ack.get() or state['text']!=editor.get('1.0','end-1c'):
            status.config(text='Compute current JSON and confirm its correspondence with the requested product first.')
            return
        if on_attach:on_attach(dict(state['record']))
        window.destroy()
    ttk.Button(buttons,text='Load JSON...',command=load_file).pack(side='left')
    ttk.Button(buttons,text='Import AA Catalog...',command=import_catalog).pack(side='left',padx=4)
    ttk.Button(buttons,text='Compute atomic graph',command=compute).pack(side='left',padx=7)
    ttk.Button(buttons,text='Attach review to Auto Plan',command=attach).pack(side='left',padx=7)
    ttk.Button(buttons,text='Close',command=window.destroy).pack(side='right')
    return window
