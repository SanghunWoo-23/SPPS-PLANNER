"""Small separate Tk editor for operator-reviewed head-to-tail reaction methods.

No modifications to global ttk.Treeview styles or existing Project Manager fields.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox

from spps_planner.reaction_planner_v9 import REACTION_METHODS, prepare_reaction_review, ReactionPlanError


def open_reaction_method_editor(parent, *, sequence, resin, scale_mmol, copies,
                                side_chain_mode, on_save, current=None):
    dialog=tk.Toplevel(parent)
    dialog.title('V9.0.0 | Head-to-tail Reaction Method (review only)')
    dialog.geometry('675x600')
    dialog.minsize(590,530)
    dialog.transient(parent)
    outer=ttk.Frame(dialog,padding=14)
    outer.pack(fill='both',expand=True)
    ttk.Label(outer,text='Head-to-tail cyclization — operator-defined method',
              font=('Segoe UI',12,'bold')).pack(anchor='w')
    ttk.Label(outer,text='Operator-reviewed draft only; entered quantities may appear in Plan and Materials, not an approved SOP.',
              wraplength=615).pack(anchor='w',pady=(4,10))
    # Only supported in solution after protected selective cleavage.
    ttk.Label(outer,text='Reaction: free N-terminal α-amine + free C-terminal COOH | Solution phase').pack(anchor='w',pady=(0,6))
    form=ttk.Frame(outer)
    form.pack(fill='x')
    ids=list(REACTION_METHODS)
    labels={k:v['label'] for k,v in REACTION_METHODS.items()}
    name_to_id={v:k for k,v in labels.items()}
    chosen=tk.StringVar(value=labels.get((current or {}).get('system_id'),labels.get('HBTU_NMM', labels[ids[0]])))
    concentration=tk.StringVar(value=str((current or {}).get('concentration_mm') or ''))
    solvent=tk.StringVar(value=str((current or {}).get('solvent') or ''))
    hours=tk.StringVar(value=str((current or {}).get('reaction_time_h') or ''))
    temperature=tk.StringVar(value='' if (current or {}).get('temperature_c') is None else str(current['temperature_c']))
    ttk.Label(form,text='Reagent system').grid(row=0,column=0,sticky='w',pady=5)
    sysbox=ttk.Combobox(form,values=[labels[k] for k in ids],textvariable=chosen,state='readonly',width=35)
    sysbox.grid(row=0,column=1,columnspan=3,sticky='ew',padx=(8,0),pady=5)
    ttk.Label(form,text='Concentration (mM)').grid(row=1,column=0,sticky='w',pady=5)
    ttk.Entry(form,textvariable=concentration,width=14).grid(row=1,column=1,sticky='w',padx=(8,15))
    ttk.Label(form,text='Solvent').grid(row=1,column=2,sticky='w',pady=5)
    ttk.Entry(form,textvariable=solvent,width=18).grid(row=1,column=3,sticky='ew',padx=(8,0))
    ttk.Label(form,text='Time (h)').grid(row=2,column=0,sticky='w',pady=5)
    ttk.Entry(form,textvariable=hours,width=14).grid(row=2,column=1,sticky='w',padx=(8,15))
    ttk.Label(form,text='Temperature (°C)').grid(row=2,column=2,sticky='w',pady=5)
    ttk.Entry(form,textvariable=temperature,width=18).grid(row=2,column=3,sticky='ew',padx=(8,0))
    form.columnconfigure(3,weight=1)
    ttk.Separator(outer).pack(fill='x',pady=9)
    ttk.Label(outer,text='Reagent equivalents — all values entered by operator, never auto-prescribed').pack(anchor='w',pady=(0,4))
    reagent_area=ttk.Frame(outer)
    reagent_area.pack(fill='x')
    eq_vars={}
    stored_eq={r['name']:str(r['equivalents']) for r in (current or {}).get('reagents',[])
               if isinstance(r,dict) and r.get('name') and r.get('equivalents') is not None}
    def draw_reagents(*_):
        # Do not throw away operator input when switching reaction systems.
        stored_eq.update({name:var.get() for name,var in eq_vars.items()})
        for child in reagent_area.winfo_children():
            child.destroy()
        eq_vars.clear()
        method=REACTION_METHODS[name_to_id[chosen.get()]]
        for idx,(name,role) in enumerate(method['reagents']):
            ttk.Label(reagent_area,text=f'{name}  ·  {role}').grid(row=idx,column=0,sticky='w',pady=4)
            var=tk.StringVar(value=stored_eq.get(name,''))
            eq_vars[name]=var
            ttk.Entry(reagent_area,textvariable=var,width=12).grid(row=idx,column=1,sticky='w',padx=(15,5),pady=4)
            ttk.Label(reagent_area,text='eq vs scale').grid(row=idx,column=2,sticky='w')
    chosen.trace_add('write',draw_reagents)
    draw_reagents()
    output=tk.Text(outer,height=8,wrap='word',font=('Consolas',9))
    output.pack(fill='both',expand=True,pady=(10,6))
    output.insert('1.0','Enter per-reagent equivalents, dilution, solvent, and time.\n\n'
                  'Preview first; quantities are mmol only, not verified bottle masses.\n'
                  'No on-resin head-to-tail method is inferred.')
    output.configure(state='disabled')
    state={'draft':None}
    def compute():
        method_id=name_to_id[chosen.get()]
        review=prepare_reaction_review(
            sequence,resin,method_id=method_id,scale_mmol=scale_mmol,copies=copies,
            concentration_mm=concentration.get(),solvent=solvent.get(),
            reaction_time_h=hours.get(),temperature_c=temperature.get(),
            equivalents={name:var.get() for name,var in eq_vars.items()},
            side_chain_mode=side_chain_mode)
        state['draft']=review
        lines=[f"STATUS: {review['method_status']} (NOT AN APPROVED SOP)",
               f"Protected linear MW: {review['protected_linear_mw']:.3f} g/mol",
               f"Protected cyclic MW: {review['protected_cyclic_mw']:.3f} g/mol",
               f"Solution per copy: {review['volume_per_copy_ml'] if review['volume_per_copy_ml'] is not None else 'not entered'} mL",
               f"Total solution: {review['volume_total_ml'] if review['volume_total_ml'] is not None else 'not entered'} mL",'']
        for r in review['reagents']:
            lines.append(f"{r['name']} ({r['role']}): {r['equivalents'] if r['equivalents'] is not None else 'not entered'} eq → "
                         f"{r['mmol_per_copy'] if r['mmol_per_copy'] is not None else 'N/A'} mmol / copy")
        lines.extend(['', 'ANALYTICAL MASS CANDIDATES (avg neutral MW, not m/z; NOT observed products):'])
        for candidate in review.get('possible_oligomers',[]):
            lines.append(f"{candidate['species']}: {candidate['average_neutral_mw_g_mol']:.3f} g/mol")
        evidence=review.get('literature_evidence',{})
        if evidence:
            lines.extend(['', 'LITERATURE CONTEXT — not a validated method:'])
            for flag in evidence.get('risk_flags',[]):
                lines.append(f"[{flag['severity'].upper()}] {flag['code']}: {flag['message']}")
            lines.append('References (IDs and links in exported JSON):')
            for paper in evidence.get('references',[]):
                lines.append(f"{paper['id']} ({paper['year']}): {paper['url']}")
        if review['method_status']!='OPERATOR_SUPPLIED_REVIEW_REQUIRED':
            lines.append('WARNING: incomplete reaction method; no executable protocol.')
        output.configure(state='normal')
        output.delete('1.0','end')
        output.insert('1.0','\n'.join(lines))
        output.configure(state='disabled')
        return review
    actions=ttk.Frame(outer)
    actions.pack(fill='x',pady=(6,0))
    def do_preview():
        try:compute()
        except (ReactionPlanError,ValueError) as exc:messagebox.showerror('Method validation',str(exc),parent=dialog)
    def do_save():
        try:
            review=compute()
            on_save(review)
            dialog.destroy()
        except (ReactionPlanError,ValueError) as exc:
            messagebox.showerror('Method validation',str(exc),parent=dialog)
    ttk.Button(actions,text='Preview quantities',command=do_preview).pack(side='left')
    ttk.Button(actions,text='Use as unapproved draft',command=do_save).pack(side='left',padx=8)
    ttk.Button(actions,text='Cancel',command=dialog.destroy).pack(side='right')
    return dialog
