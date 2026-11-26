"""Optional sequence-first Auto Plan confirmation UI.

The existing Project Manager Generate remains the calculation authority.
No empirical cleavage recommendation is manufactured by this preview.
"""
from __future__ import annotations
import math
import tkinter as tk
from tkinter import ttk, messagebox
from spps_planner.parser import parse_sequence
from spps_planner.mass_balance_v9 import calculate_mass_states, estimate_mass_yield, MassBalanceError, checked_integer
from spps_planner.reaction_planner_v9 import validate_stored_reaction_review, ReactionPlanError
from suite_gui.sequence_risk_map_v8 import build_sequence_risk_map
from datetime import datetime, timezone
import json
from tkinter import filedialog


def preview_inputs(sequence, scale, resin, loading, chemistry, copies):
    if not str(sequence or "").strip():
        raise ValueError("Enter a peptide sequence first.")
    parsed = parse_sequence(str(sequence).strip())
    tokens = list(parsed.core_tokens) + list(parsed.branch_tokens)
    if not tokens:
        raise ValueError("The sequence has no recognized amino-acid residues.")
    try:
        amount, load = float(scale), float(loading)
        count = checked_integer(copies, 'copies')
    except (TypeError, ValueError) as exc:
        raise ValueError("Scale, loading, and copies must be numeric.") from exc
    if isinstance(scale, bool) or isinstance(loading, bool) or not all(math.isfinite(v) and v > 0 for v in (amount, load)):
        raise ValueError("Scale, loading, and copies must be positive finite values.")
    if not str(resin).strip():
        raise ValueError("Select a resin before generating.")
    cys = sum(str(token).upper() == "C" for token in tokens)
    tfa_eq = 100 * cys if cys else (30 if len(tokens) <= 7 else 80 if len(tokens) <= 15 else 100)
    return {
        "sequence": str(sequence).strip(), "residues": len(tokens),
        "scale": amount, "resin": str(resin).strip(), "loading": load,
        "copies": count, "chemistry": str(chemistry).strip(),
        "resin_g": amount / load, "tfa_eq": tfa_eq,
        "cys_count": cys, "nterm": parsed.nterm, "cterm": parsed.cterm_text,
    }


def build_review_draft(sequence, scale, resin, loading, chemistry, copies, *, product_path="linear_deprotected", side_chain_mode="catalog", reaction_review=None):
    """Deterministic, review-only V9 draft; never changes the active project.

    Experimental conditions and cleavage recipes are intentionally not inferred.
    """
    fields = preview_inputs(sequence, scale, resin, loading, chemistry, copies)
    if reaction_review is not None:
        if not product_path.startswith('head_to_tail') or not isinstance(reaction_review,dict):
            raise ValueError('Reaction review requires a Head-to-tail product pathway.')
        try:
            reaction_review = validate_stored_reaction_review(
                reaction_review, sequence=fields['sequence'], resin=fields['resin'],
                scale_mmol=fields['scale'], copies=fields['copies'],
                side_chain_mode=side_chain_mode)
        except ReactionPlanError as exc:
            raise ValueError(f'Reaction method is stale or invalid: {exc}') from exc
    risks = build_sequence_risk_map(fields["sequence"])
    try:
        mass = calculate_mass_states(fields['sequence'], fields['resin'],side_chain_mode=side_chain_mode)
        mass_status = {'status':'CALCULATED_THEORETICAL','values':mass}
    except (MassBalanceError, ValueError) as exc:
        mass_status = {'status':'MASS_NOT_AVAILABLE','reason':str(exc)}
    from suite_gui.auto_plan_evolution_v9 import build_process_review
    from spps_planner.structure_crosscheck_v9 import independent_mass_check
    from spps_planner.extended_structure_v9 import graph_crosscheck
    process_review = build_process_review(product_path, mass_status, reaction_review)
    structure_review = independent_mass_check(fields['sequence'], expected=mass_status.get('values'))
    # Independent graph verification of explicitly supported chemistry. For a
    # *deprotected* endpoint, do not accidentally validate a protected precursor.
    mass_values=mass_status.get('values',{})
    graph_mode=('lysine_branch' if mass_values.get('topology')=='lysine_branch'
                else 'head_to_tail' if product_path.startswith('head_to_tail') else 'linear')
    endpoint_groups=('none' if product_path in ('linear_deprotected','head_to_tail_deprotected')
                     else side_chain_mode)
    graph_review=graph_crosscheck(fields['sequence'], fields['resin'],topology=graph_mode,
                                  side_chain_mode=endpoint_groups)
    from spps_planner.research_assistant_v9 import build_research_brief
    research_review = build_research_brief(fields['sequence'],product_path,fields['resin'],reaction_review)
    return {
        "process_review":process_review,
        "research_assistant":research_review,
        "structure_crosscheck":structure_review,
        "extended_structure_review":graph_review,
        "format": "SPPS Planner V9.0.0 operator review draft",
        "schema": 1,
        "status": "DRAFT_NOT_APPROVED",
        "source": "Current Project Manager inputs",
        "product_path": product_path,
        "side_chain_mode": side_chain_mode,
        "mass": mass_status,
        "yield": {"status":"NO_ESTIMATE_UNTIL_OPERATOR_FACTORS"},
        "reaction_review": reaction_review if product_path.startswith("head_to_tail") and reaction_review else {"status":"NO_CYCLIZATION_METHOD_SELECTED"},
        "inputs": fields,
        "risk": {
            "findings": risks["findings"],
            "parser_warnings": risks["parser_warnings"],
            "meaning": risks["score_meaning"],
        },
        "cleavage": {
            "tfa_basis_eq": fields["tfa_eq"],
            "cocktail": None,
            "time_minutes": None,
            "evidence": "Unverified rule-based planning basis; operator review required",
        },
        "operator_notes": "",
        "generation": "Existing chemistry engine only after confirmation",
    }


def draft_to_json(draft, notes=""):
    """Serializable review draft; no experimental approval implied by export."""
    document = dict(draft)
    document["operator_notes"] = str(notes)
    return json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)


def open_auto_plan(gui, *, preferred_product_path=None, preferred_side_chain_mode=None):
    try:
        data = build_review_draft(gui.pm_sequence.get(), gui.pm_scale.get(),
                              gui.pm_resin.get(), gui.pm_loading.get(),
                              gui.pm_chemistry.get(), gui.pm_copies.get())
    except (ValueError, KeyError, AttributeError) as exc:
        messagebox.showerror("Auto Plan — check inputs", str(exc), parent=gui)
        return
    inputs = data["inputs"]
    idx = gui.pm_current_index() if hasattr(gui, 'pm_current_index') else None
    item = gui.pm_items[idx] if idx is not None and hasattr(gui,'pm_items') and 0 <= idx < len(gui.pm_items) else {}
    saved_options = item.get('v9_mass_options',{}) if isinstance(item,dict) else {}
    if not isinstance(saved_options,dict):
        saved_options={}
    win = tk.Toplevel(gui)
    win.title("Auto Plan | SPPS Planner V9.0.0")
    win.geometry("790x750")
    win.minsize(650, 620)
    win.transient(gui)
    # V9: keep all review and Generate controls reachable at modest window sizes.
    # Canvas scrollbar is scoped to this dialog (no global MouseWheel bindings).
    viewport = ttk.Frame(win)
    viewport.pack(fill='both',expand=True)
    canvas = tk.Canvas(viewport,highlightthickness=0,borderwidth=0)
    scrollbar = ttk.Scrollbar(viewport,orient='vertical',command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right',fill='y')
    canvas.pack(side='left',fill='both',expand=True)
    body = ttk.Frame(canvas, padding=16)
    content_id = canvas.create_window((0,0),window=body,anchor='nw')
    body.bind('<Configure>',lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e: canvas.itemconfigure(content_id,width=e.width))
    def _wheel(event):
        # Avoid intercepting Text's own scroll and Combobox popup interactions.
        if isinstance(event.widget, (tk.Text, ttk.Combobox)):
            return None
        delta = getattr(event, 'delta', 0)
        if delta:
            canvas.yview_scroll(-int(delta / abs(delta)), 'units')
        elif getattr(event, 'num', 0) in (4, 5):
            canvas.yview_scroll(-1 if event.num == 4 else 1, 'units')
        return 'break'
    def _bind_wheel(widget):
        # Toplevel-local bindings: multiple windows do not affect each other.
        if not isinstance(widget, (tk.Text, ttk.Combobox)):
            widget.bind('<MouseWheel>', _wheel, add='+')
            widget.bind('<Button-4>', _wheel, add='+')
            widget.bind('<Button-5>', _wheel, add='+')
        for child in widget.winfo_children():
            _bind_wheel(child)
    ttk.Label(body, text="Auto Plan — review before generation", font=("Segoe UI", 15, "bold")).pack(anchor="w")
    ttk.Label(body, text="Optional: existing Generate and Step 1 / Step 2 remain unchanged.", wraplength=660).pack(anchor="w", pady=(4, 12))
    text = tk.Text(body, height=13, wrap="word", font=("Consolas", 10), relief="flat", borderwidth=6)
    text.pack(fill="both", expand=True)
    details = [
        "CURRENT PROJECT INPUTS (not changed by opening this window)",
        f"Sequence       {inputs['sequence']}",
        f"Residues       {inputs['residues']}",
        f"N-terminal     {inputs['nterm'] or 'none'}",
        f"C-terminal     {inputs['cterm'] or 'from resin / sequence notation'}",
        f"Scale          {inputs['scale']:g} mmol  ×  {inputs['copies']} copies",
        f"Resin          {inputs['resin']}",
        f"Loading        {inputs['loading']:g} mmol/g",
        f"Resin mass     {inputs['resin_g']:g} g per copy (theoretical)",
        f"Chemistry      {inputs['chemistry']}",
        "",
        "CLEAVAGE PLANNING — RULE-BASED, NOT VERIFIED RECIPE",
        f"TFA basis      {inputs['tfa_eq']} eq (Cys count: {inputs['cys_count']})",
        "Cocktail       NOT auto-selected; use verified operator conditions",
        "Time           NOT inferable from sequence alone",
        "TIS / NH4I     NEVER automatically added",
        "",
        "GENERATE WILL UPDATE",
        "Plan · Materials · Checklist · Total Materials · Cleavage / Workup",
        "using the existing engine and active Project Manager settings.",
        "Inspect the resulting tables and evidence before laboratory use.",
    ]
    text.insert("1.0", "\n".join(details))
    findings = data["risk"]["findings"]
    details.extend(["", f"SEQUENCE RISK — {len(findings)} rule-based findings (not failure probability)"])
    for finding in findings[:15]:
        details.append(f"[{finding['severity']}] {finding['rule_id']}: {finding['title']} (positions {finding['positions']})")
    if len(findings) > 15:
        details.append(f"... {len(findings) - 15} more findings; consult Sequence Risk Map")
    if data["risk"]["parser_warnings"]:
        details.extend(["PARSER WARNINGS:", *map(str, data["risk"]["parser_warnings"])])
    text.delete("1.0", "end")
    text.insert("1.0", "\n".join(details))
    text.configure(state="disabled")
    # Show validated stage intent and independent graph check, not a recommended SOP.
    process = data.get('process_review', {})
    summary = ttk.LabelFrame(body,text='V9 Auto Plan · Reaction stages and RDKit cross-check',padding=8)
    summary.pack(fill='x',pady=5)
    labels = [f"{step['label']}: {step['theoretical_mw_g_mol'] if step['theoretical_mw_g_mol'] is not None else 'MW not calculated'} g/mol"
              for step in process.get('stages',[])]
    labels.extend('BLOCKED: '+item for item in process.get('blockers',[]))
    cross=data.get('structure_crosscheck',{})
    labels.append('RDKit independent mass review: '+str(cross.get('status','NOT_AVAILABLE')))
    ext=data.get('extended_structure_review',{})
    labels.append('Extended molecular graph: '+str(ext.get('status','NOT_AVAILABLE')))
    process_label=ttk.Label(summary,text='\n'.join(labels),wraplength=640,justify='left')
    process_label.pack(anchor='w')
    paper_list=data.get('research_assistant',{}).get('references',[])
    if paper_list:
        ttk.Label(summary,text='Literature context (review only): '+', '.join(p['id'] for p in paper_list[:5]),
                  wraplength=640).pack(anchor='w',pady=(6,0))

    # Offline AI / Excel evidence. Nothing can silently change chemistry or Plan.
    ai_review_state = {'result': None}
    ai_box=ttk.LabelFrame(body,text='V9 AI Assistant · Excel / CSV (optional)',padding=(8,6))
    ai_box.pack(fill='x',pady=(4,6))
    def _receive_ai_evidence(result):
        ai_review_state['result']=dict(result)
    def _open_ai_import():
        from suite_gui.ai_excel_dialog_v9 import open_excel_ai_dialog
        context={'sequence':inputs['sequence'],'resin':inputs['resin'],
            'chemistry':inputs['chemistry'],'scale_mmol':inputs['scale'],
            'loading_mmol_g':inputs['loading'],
            'product_path':final_options[chosen.get()]}
        active_mass=calculate_mass_states(inputs['sequence'],inputs['resin'],
                         side_chain_mode=protection_modes[group_label.get()])
        context['protection_profile']=';'.join(
            f"{r['position']}:{r['residue']}({r['protecting_group']})"
            for r in active_mass['residues'] if r.get('protecting_group'))
        method=reaction_state.get('draft') or {}
        context.update(reaction_step=('cyclization' if final_options[chosen.get()].startswith('head_to_tail') else 'crude'),
                       reaction_method=method.get('system_label',''),
                       reaction_time_h=method.get('reaction_time_h'),
                       reaction_concentration_mm=method.get('concentration_mm'))
        return open_excel_ai_dialog(gui,parent=win,current_context=context,on_apply=_receive_ai_evidence)
    ttk.Button(ai_box,text='AI · Import Excel / CSV...',command=_open_ai_import).pack(side='left')
    # Local-only literature retrieval; citations are curated, not generated SOPs.
    reference_line=ttk.Frame(summary);reference_line.pack(fill='x',pady=(4,0))
    reference_query=tk.StringVar(value='cyclization')
    ttk.Entry(reference_line,textvariable=reference_query,width=25).pack(side='left')
    reference_results=ttk.Label(summary,text='Search the bundled 8-paper evidence registry.',wraplength=650,justify='left')
    reference_results.pack(anchor='w')
    def search_evidence():
        from spps_planner.research_assistant_v9 import search_local_evidence
        refs=search_local_evidence(reference_query.get(),max_results=3)
        reference_results.configure(text=('\n'.join(f"{r['id']}: {r['url']}" for r in refs)
                if refs else 'No curated source matches. Insufficient evidence: no reaction recommendation.'))
    ttk.Button(reference_line,text='Search bundled sources',command=search_evidence).pack(side='left',padx=5)
    # Explicit opt-in only: this sends ONLY the text typed in the bibliography
    # field to Crossref; never sends the peptide or private experiment records.
    from suite_gui.ai_background_v9 import UiBackgroundRunner
    bibliographic_job=UiBackgroundRunner(win,lambda busy: online_button.configure(
        state='disabled' if busy else 'normal'))
    def _online_bibliography():
        query=reference_query.get().strip()
        if not messagebox.askyesno('Online bibliography (Crossref)',
            'Send ONLY these manually typed search keywords to the public Crossref API?\n\n'
            f'{query[:160]}\n\nNo sequence/project/experimental data is included automatically.',parent=win):
            return
        from spps_planner.online_bibliography_v9 import search_crossref_metadata
        def success(value):
            refs=value.get('references',[])
            reference_results.configure(text=('\n'.join(
                f"{r['year'] or 'n.d.'}: {r['title']}  {r['url']}" for r in refs)
                  if refs else 'No bibliographic matches. No synthesis advice inferred.')[:2500])
        def failure(error):
            reference_results.configure(text='Online lookup unavailable: '+str(error)[:180])
        bibliographic_job.submit(lambda:search_crossref_metadata(query),success,failure)
    online_button=ttk.Button(reference_line,text='Search Crossref online (opt-in)',command=_online_bibliography)
    online_button.pack(side='left',padx=4)
    ttk.Button(reference_line,text='Local PDF / Paper Evidence...',
               command=lambda: __import__('suite_gui.local_paper_panel_v9',fromlist=['open_local_paper_panel']).open_local_paper_panel(win)).pack(side='left',padx=4)
    def _online_window_closed(event):
        if event.widget is win:
            bibliographic_job.closed=True
    win.bind('<Destroy>',_online_window_closed,add='+')

    choices = ttk.LabelFrame(body, text="V9 Protected Product / Cyclization MW", padding=(8,6))
    choices.pack(fill="x", pady=(6,5))
    selection = ttk.Frame(choices); selection.pack(fill="x")
    ttk.Label(selection, text="Final product:").pack(side="left")
    final_options = {
        'Linear — fully deprotected':'linear_deprotected',
        'Linear — side-chain protected (selective cleavage)':'linear_protected',
        'Head-to-tail — cyclic, still protected':'head_to_tail_protected',
        'Head-to-tail — cyclic, globally deprotected':'head_to_tail_deprotected',
    }
    restored_product=preferred_product_path or saved_options.get('product_path','linear_deprotected')
    chosen = tk.StringVar(value=next((title for title,value in final_options.items() if value==restored_product), 'Linear — fully deprotected'))
    selector = ttk.Combobox(selection, textvariable=chosen, state='readonly',width=48,
                            values=list(final_options))
    selector.pack(side='left',padx=(6,5),fill='x',expand=True)
    row_group=ttk.Frame(choices);row_group.pack(fill='x',pady=(5,0))
    ttk.Label(row_group,text='Side-chain groups:').pack(side='left')
    protection_modes={
        'Catalog precursor (assumed retained)':'catalog',
        'Only explicitly annotated groups':'explicit',
        'None (deprotected chain)':'none',
    }
    stored_group=preferred_side_chain_mode or saved_options.get('side_chain_mode','catalog')
    group_label=tk.StringVar(value=next((title for title,value in protection_modes.items() if value==stored_group), 'Catalog precursor (assumed retained)'))
    group_select=ttk.Combobox(row_group,textvariable=group_label,values=list(protection_modes),
                              state='readonly',width=36)
    group_select.pack(side='left',padx=(6,4))
    reaction_state={'draft':None}
    crosslink_state={'review':None}
    saved_reaction=saved_options.get('reaction_review')
    if isinstance(saved_reaction,dict) and restored_product.startswith('head_to_tail'):
        try:
            reaction_state['draft'] = validate_stored_reaction_review(
                saved_reaction, sequence=inputs['sequence'], resin=inputs['resin'],
                scale_mmol=inputs['scale'], copies=inputs['copies'],
                side_chain_mode=stored_group)
        except (ValueError, TypeError, MassBalanceError, ReactionPlanError):
            pass
    method_row=ttk.Frame(choices)
    method_row.pack(fill='x',pady=(5,0))
    method_state_label=ttk.Label(method_row,text=(
        f"Restored unapproved method: {reaction_state['draft'].get('system_label','')}" if reaction_state['draft']
        else 'No head-to-tail method selected (mass-only review)'),wraplength=430)
    method_state_label.pack(side='right',fill='x',expand=True)
    def save_method(draft):
        reaction_state['draft']=draft
        method_state_label.configure(text=f"{draft['system_label']}: {draft['method_status']} — unapproved draft")
    def edit_method():
        if not final_options[chosen.get()].startswith('head_to_tail'):
            messagebox.showwarning('Reaction Method',
                'Choose a Head-to-tail product before editing its cyclization method.',parent=win)
            return
        from suite_gui.reaction_method_editor_v9 import open_reaction_method_editor
        open_reaction_method_editor(win,sequence=inputs['sequence'],resin=inputs['resin'],
            scale_mmol=inputs['scale'],copies=inputs['copies'],
            side_chain_mode=protection_modes[group_label.get()],
            on_save=save_method,current=(reaction_state['draft'] or {
                'system_id': (item.get('v9_mass_options') or {}).get('coupling_system_id','HBTU_NMM')}) )
    ttk.Button(method_row,text='Head-to-tail Method...',command=edit_method).pack(side='left')
    graph_row=ttk.Frame(choices);graph_row.pack(fill='x',pady=(5,0))
    graph_status=ttk.Label(graph_row,text='No independent cross-link review attached.',wraplength=450)
    graph_status.pack(side='right',fill='x',expand=True)
    def open_graph_review():
        from suite_gui.structure_review_panel_v9 import open_structure_review
        path=final_options[chosen.get()]
        suggestion='head_to_tail' if path.startswith('head_to_tail') else 'linear'
        def attached(record):
            crosslink_state['review']=record
            graph_status.configure(text='Graph review: '+record['graph'].get('status','UNKNOWN') +
                                   ' ('+record['topology']+'). No recipe applied.')
        open_structure_review(win,sequence=inputs['sequence'],resin=inputs['resin'],
            side_chain_mode=protection_modes[group_label.get()],
            suggested_topology=suggestion,on_attach=attached)
    ttk.Button(graph_row,text='Independent molecular graph / Cross-link...',
               command=open_graph_review).pack(side='left')
    mass_label=ttk.Label(choices,text='',wraplength=700)
    mass_label.pack(fill='x',pady=(4,0))

    yield_box=ttk.LabelFrame(body,text='Yield scenario — optional, NOT a measured prediction',padding=(8,5))
    yield_box.pack(fill='x',pady=(2,5))
    scenario_row=ttk.Frame(yield_box);scenario_row.pack(fill='x')
    ttk.Label(scenario_row,text='Coupling/step %').pack(side='left')
    stored_yield=item.get('v9_yield_scenario') if isinstance(item,dict) else None
    try:
        expected_context={
            'sequence':inputs['sequence'],'resin':inputs['resin'],
            'scale_mmol':inputs['scale'],'copies':inputs['copies'],
        }
        if (not isinstance(stored_yield,dict)
            or stored_yield.get('context')!=expected_context
            or stored_yield.get('product_path')!=final_options[chosen.get()]):
            stored_yield=None
    except (ValueError,TypeError,KeyError):
        stored_yield=None
    existing_factors=stored_yield.get('inputs',{}) if stored_yield else {}
    step_pct=tk.StringVar(value=existing_factors.get('coupling_conversion_percent',''))
    ttk.Entry(scenario_row,textvariable=step_pct,width=7).pack(side='left',padx=(3,9))
    ttk.Label(scenario_row,text='Cyclization %').pack(side='left')
    cycl_pct=tk.StringVar(value=existing_factors.get('cyclization_recovery_percent',''))
    ttk.Entry(scenario_row,textvariable=cycl_pct,width=7).pack(side='left',padx=(3,9))
    ttk.Label(scenario_row,text='Isolation %').pack(side='left')
    iso_pct=tk.StringVar(value=existing_factors.get('isolation_recovery_percent',''))
    ttk.Entry(scenario_row,textvariable=iso_pct,width=7).pack(side='left',padx=(3,9))
    yield_info=ttk.Label(yield_box,text='Leave fields blank to report theoretical mass only.',wraplength=710)
    yield_info.pack(anchor='w',pady=(3,0))

    def preview_mass(*_):
        try:
            current=calculate_mass_states(inputs['sequence'],inputs['resin'],
                       side_chain_mode=protection_modes[group_label.get()])
            path=final_options[chosen.get()]
            from suite_gui.auto_plan_evolution_v9 import build_process_review
            review=build_process_review(path,{'status':'CALCULATED_THEORETICAL','values':current},reaction_state['draft'])
            lines=[f"{r['label']}: {r['theoretical_mw_g_mol'] if r['theoretical_mw_g_mol'] is not None else 'not calculated'} g/mol"
                   for r in review['stages']]
            lines += ['BLOCKED: '+x for x in review['blockers']]
            process_label.configure(text='\n'.join(lines))
            key={'linear_deprotected':'linear_deprotected_mw',
                 'linear_protected':'selective_cleavage_mw',
                 'head_to_tail_protected':'head_to_tail_protected_mw',
                 'head_to_tail_deprotected':'head_to_tail_deprotected_mw'}[path]
            mw=current[key]
            if mw is None:
                mass_label.configure(text='BLOCKED: head-to-tail requires free N-terminal amine and free C-terminal COOH. Check resin and end caps.')
            else:
                mass_label.configure(text=f'Product MW {mw:,.3f} g/mol | Protected linear {current["linear_protected_mw"]:,.3f} | '
                           f'Fully deprotected linear {current["linear_deprotected_mw"]:,.3f} | '
                           f'Head-to-tail theoretical loss {current["water_loss_mw"]:.3f} Da. '
                           f'Assumptions/warnings: {len(current["warnings"])} (see exported JSON).')
        except Exception as exc:
            mass_label.configure(text='Mass cannot be calculated without exact chemistry: '+str(exc))
    def invalidate_reaction(*_):
        reaction_state['draft']=None
        crosslink_state['review']=None
        graph_status.configure(text='Graph review cleared: product/protection changed.')
        method_state_label.configure(text='Method cleared due to product/protection change; re-review if needed.')
        # AI evidence was obtained for the previously selected product topology.
        if ai_review_state['result'] is not None:
            ai_review_state['result']=None
            ai_status.configure(text='AI evidence cleared after product/protection change. Recheck the active pathway.')
        preview_mass()
    chosen.trace_add('write',invalidate_reaction)
    group_label.trace_add('write',invalidate_reaction)
    preview_mass()

    def _scenario_snapshot():
        state=calculate_mass_states(inputs['sequence'],inputs['resin'],side_chain_mode=protection_modes[group_label.get()])
        path=final_options[chosen.get()]
        key={'linear_deprotected':'linear_deprotected_mw','linear_protected':'selective_cleavage_mw',
             'head_to_tail_protected':'head_to_tail_protected_mw','head_to_tail_deprotected':'head_to_tail_deprotected_mw'}[path]
        mw=state[key]
        if mw is None:
            raise ValueError('Product pathway blocked: free N-terminal amine and free C-terminal COOH required')
        raw={'coupling_conversion_percent':step_pct.get().strip(),
             'cyclization_recovery_percent':cycl_pct.get().strip(),
             'isolation_recovery_percent':iso_pct.get().strip(),
             'coupling_step_assumption':max(0,state['residue_count']-1)}
        needed=('coupling_conversion_percent','isolation_recovery_percent')
        if any(not raw[k] for k in needed):
            if any(raw[k] for k in ('coupling_conversion_percent','cyclization_recovery_percent','isolation_recovery_percent')):
                raise ValueError('Provide both coupling conversion % and isolation recovery %; cyclic additionally needs cyclization %.')
            result=estimate_mass_yield(mw,inputs['scale'],copies=inputs['copies'])
        else:
            is_cycl=path.startswith('head_to_tail')
            if is_cycl and not raw['cyclization_recovery_percent']:
                raise ValueError('Cyclic case requires cyclization recovery %')
            result=estimate_mass_yield(mw,inputs['scale'],copies=inputs['copies'],
                coupling_steps=raw['coupling_step_assumption'],
                per_step_conversion=float(raw['coupling_conversion_percent'])/100.,
                cyclization_recovery=float(raw['cyclization_recovery_percent'])/100. if is_cycl else None,
                isolation_recovery=float(raw['isolation_recovery_percent'])/100.)
        return {'status':result['status'],'inputs':raw,'product_path':path,
                'context':{'sequence':inputs['sequence'], 'resin':inputs['resin'],
                           'scale_mmol':inputs['scale'], 'copies':inputs['copies']},
                'mw_g_mol':mw,'output':result,
                'disclaimer':'Operator-defined illustrative arithmetic, not empirical yield prediction or validated recovery.'}

    def run_yield_scenario():
        try:
            snapshot=_scenario_snapshot()
            result=snapshot['output']
            if result['scenario_g'] is None:
                yield_info.configure(text=f'Theoretical mass (100%): {result["theoretical_g"]:,.4f} g. Enter conversion and recovery factors for an operator scenario.')
            else:
                yield_info.configure(text=f'Theoretical: {result["theoretical_g"]:,.4f} g | OPERATOR SCENARIO: {result["scenario_g"]:,.4f} g ({result["scenario_percent"]:.2f}%); NOT a validated prediction')
        except Exception as exc:
            yield_info.configure(text='Scenario error: '+str(exc))

    ttk.Button(scenario_row,text='Calculate',command=run_yield_scenario).pack(side='left')

    ttk.Label(body, text="Review notes (exported with draft; not an approved SOP):").pack(anchor="w")
    review_notes = tk.Text(body, height=3, wrap="word")
    review_notes.pack(fill="x", pady=(0, 6))
    status = ttk.Label(body, text="Review the above assumptions before applying.", foreground="#815500")
    status.pack(anchor="w", pady=(8, 6))
    buttons = ttk.Frame(body)
    buttons.pack(fill="x")

    def generate():
        try:
            latest = build_review_draft(gui.pm_sequence.get(), gui.pm_scale.get(), gui.pm_resin.get(),
                                    gui.pm_loading.get(), gui.pm_chemistry.get(), gui.pm_copies.get())
            if latest != data:
                messagebox.showwarning("Auto Plan", "Project values changed since preview. Reopen Auto Plan to review the new inputs.", parent=win)
                return
            idx_before = gui.pm_current_index()
            item_before = gui.pm_items[idx_before] if idx_before is not None else None
            old_options = item_before.get('v9_mass_options') if item_before is not None else None
            scenario_snapshot=_scenario_snapshot()
            chosen_path=final_options[chosen.get()]
            group_mode=protection_modes[group_label.get()]
            verified_review=None
            if chosen_path.startswith('head_to_tail') and reaction_state['draft'] is not None:
                verified_review=validate_stored_reaction_review(
                    reaction_state['draft'],sequence=inputs['sequence'],resin=inputs['resin'],
                    scale_mmol=inputs['scale'],copies=inputs['copies'],side_chain_mode=group_mode)
            old_yield=item_before.get('v9_yield_scenario') if item_before is not None else None
            old_graph=item_before.get('v9_graph_review') if item_before is not None else None
            old_ai=item_before.get('v9_ai_evidence') if item_before is not None else None
            if item_before is not None:
                item_before['v9_yield_scenario']=scenario_snapshot
                item_before['v9_graph_review']=crosslink_state['review'] or {'status':'NOT_REVIEWED'}
                item_before['v9_ai_evidence']=(ai_review_state['result'] or {'status':'NO_AI_EVIDENCE_ATTACHED'})
                item_before['v9_mass_options'] = {
                    'coupling_system_id': (verified_review or {}).get('system_id') or (old_options or {}).get('coupling_system_id','HBTU_NMM'),
                    'coupling_system_label': (verified_review or {}).get('system_label') or (old_options or {}).get('coupling_system_label','HBTU / NMM'),
                    'product_path': chosen_path,
                    'side_chain_mode': group_mode,
                    'reaction_review': verified_review,
                }
            try:
                gui.pm_generate_selected()
            except Exception:
                if item_before is not None:
                    if old_options is None:item_before.pop('v9_mass_options',None)
                    else:item_before['v9_mass_options']=old_options
                    if old_graph is None:item_before.pop('v9_graph_review',None)
                    else:item_before['v9_graph_review']=old_graph
                    if old_yield is None:item_before.pop('v9_yield_scenario',None)
                    else:item_before['v9_yield_scenario']=old_yield
                    if old_ai is None:item_before.pop('v9_ai_evidence',None)
                    else:item_before['v9_ai_evidence']=old_ai
                raise
            idx = gui.pm_current_index()
            item = gui.pm_items[idx] if idx is not None else None
            if not item or item.get("status") != "Calculated":
                if item_before is not None:
                    if old_options is None: item_before.pop('v9_mass_options',None)
                    else: item_before['v9_mass_options']=old_options
                    if old_graph is None: item_before.pop('v9_graph_review',None)
                    else: item_before['v9_graph_review']=old_graph
                    if old_yield is None: item_before.pop('v9_yield_scenario',None)
                    else: item_before['v9_yield_scenario']=old_yield
                    if old_ai is None: item_before.pop('v9_ai_evidence',None)
                    else: item_before['v9_ai_evidence']=old_ai
                status.configure(text="Generation did not complete; inspect the Project Manager error.")
                return
            if hasattr(gui, "pm_refresh_cyclic_settings"):
                gui.pm_refresh_cyclic_settings()
            status.configure(text="Plan generated. Review Plan, Materials, Checklist and Cleavage tabs.", foreground="#176b3a")
            messagebox.showinfo("Auto Plan", "Existing engine generated the selected project outputs.\nReview the tables and confirm cleavage conditions before use.", parent=win)
        except Exception as exc:
            status.configure(text="Generation failed; no successful result was confirmed.")
            messagebox.showerror("Auto Plan", str(exc), parent=win)

    def export_draft():
        try:
            latest = build_review_draft(gui.pm_sequence.get(), gui.pm_scale.get(), gui.pm_resin.get(),
                                        gui.pm_loading.get(), gui.pm_chemistry.get(), gui.pm_copies.get())
            if latest != data:
                messagebox.showwarning("Auto Plan", "Project values changed; reopen preview before export.", parent=win)
                return
            destination = filedialog.asksaveasfilename(parent=win, title="Export unapproved review draft",
                 defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if not destination:
                return
            export_data = build_review_draft(inputs['sequence'],inputs['scale'],inputs['resin'],
                  inputs['loading'], inputs['chemistry'], inputs['copies'],
                  product_path=final_options[chosen.get()],
                  side_chain_mode=protection_modes[group_label.get()],
                  reaction_review=reaction_state['draft'])
            export_data['yield']=_scenario_snapshot()
            export_data['crosslink_review']=crosslink_state['review'] or {'status':'NOT_REVIEWED'}
            export_data['ai_evidence'] = (ai_review_state['result'] or {'status':'NO_AI_EVIDENCE_ATTACHED'})
            payload = draft_to_json(export_data, review_notes.get("1.0", "end-1c"))
            # No reliance on private persistence implementation: use same-directory temp + replace.
            from pathlib import Path
            import os, tempfile
            target = Path(destination)
            fd, temp = tempfile.mkstemp(dir=str(target.parent), prefix=".v9draft_", suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temp, target)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
            status.configure(text="Unapproved draft exported (not an experimental SOP).", foreground="#176b3a")
        except Exception as exc:
            messagebox.showerror("Export draft", str(exc), parent=win)

    ttk.Button(buttons, text="Generate Full Plan", command=generate).pack(side="left")
    ttk.Button(buttons, text="Export Draft JSON", command=export_draft).pack(side="left", padx=(8, 0))
    ttk.Button(buttons, text="Close", command=win.destroy).pack(side="right")
    _bind_wheel(viewport)
    return win
