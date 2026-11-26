"""Simple Excel/CSV -> review -> local ML -> Auto Plan evidence workflow.

All file I/O is local. Does not write private observations to release directories.
"""
from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from suite_gui.ai_background_v9 import UiBackgroundRunner

from suite_gui.ai_excel_core_v9 import (
    ALIASES, DISPLAY, preview_file, normalize_preview,
    save_reviewed_dataset, load_reviewed_dataset, train_local_advisor,
    advise_from_local_data, verify_preview_source, combine_reviewed_tables,
    audit_reviewed_data, append_reviewed_dataset, restore_last_good_dataset,
    ml_readiness_report, create_blank_excel_template, create_process_excel_template,
    discover_import_sources, _sha256_file,
)


def _locations(gui):
    from spps_planner.user_paths import user_data_dir, user_models_dir
    data = Path(getattr(gui,'ai_excel_data_dir',None) or user_data_dir()/'ai_excel_v9')
    models = Path(getattr(gui,'ai_excel_models_dir',None) or user_models_dir()/'ai_excel_v9')
    return data, models


def open_excel_ai_dialog(gui, *, parent=None, current_context=None, on_apply=None, on_dataset_saved=None):
    """Call from either Auto Plan or ML Lab; never runs automatically on file selection."""
    host=parent or gui
    win=tk.Toplevel(host)
    win.title('SPPS Planner V9.0.0 | AI + Excel Assistant')
    win.geometry('1040x730'); win.minsize(830,620); win.transient(host)
    root=ttk.Frame(win,padding=12); root.pack(fill='both',expand=True)
    # Scroll the workbook/mapping body while reserving a fixed action footer.
    body_canvas=tk.Canvas(root,highlightthickness=0,borderwidth=0)
    body_scroll=ttk.Scrollbar(root,orient='vertical',command=body_canvas.yview)
    body_canvas.configure(yscrollcommand=body_scroll.set)
    body=ttk.Frame(body_canvas)
    body_window=body_canvas.create_window((0,0),window=body,anchor='nw')
    def _resize_body(_event=None):
        body_canvas.configure(scrollregion=body_canvas.bbox('all'))
    def _resize_canvas(event):
        body_canvas.itemconfigure(body_window,width=event.width)
    body.bind('<Configure>',_resize_body)
    body_canvas.bind('<Configure>',_resize_canvas)
    def _body_wheel(event):
        if getattr(event,'num',None)==4: steps=-1
        elif getattr(event,'num',None)==5: steps=1
        else: steps=-int(getattr(event,'delta',0)/120)
        if steps: body_canvas.yview_scroll(steps,'units')
    body_canvas.bind('<MouseWheel>',_body_wheel)
    body_canvas.bind('<Button-4>',_body_wheel)
    body_canvas.bind('<Button-5>',_body_wheel)
    ttk.Label(body,text='AI Data Assistant · Excel / CSV → Review → Learn',font=('Segoe UI',14,'bold')).pack(anchor='w')
    ttk.Label(body,text='Local-only. Import does not modify experimental records, current Plan, chemistry, or SOP. Review each mapped field before saving.',wraplength=760).pack(anchor='w',pady=(3,7))

    state={'preview':None,'normalized':None,'report':None,'accepted':False,'result':None,'reviewed_signature':None,
           'staged':[],'pending_paths':[],'current_staged':False,'scan_notices':[],'total_queue_count':0}
    source=tk.StringVar(value='No workbook selected')
    selected_sheet=tk.StringVar(value='')
    scan_all_sheets=tk.BooleanVar(value=True)
    chooser=ttk.Frame(body);chooser.pack(fill='x',pady=(3,5))
    ttk.Label(chooser,textvariable=source).pack(side='left',fill='x',expand=True)
    sheetbox=ttk.Combobox(chooser,textvariable=selected_sheet,values=[],state='readonly',width=20)
    sheetbox.pack(side='right',padx=(8,0))
    ttk.Checkbutton(body,text='Automatically queue data worksheets from each Excel file (review individually)',
                    variable=scan_all_sheets).pack(anchor='w',pady=(2,3))
    mapping=ttk.LabelFrame(body,text='Detected columns · adjust if needed',padding=8)
    # Manual mapping is available only after Advanced is expanded.
    # Its contents are kept intact for existing users.
    # Pack it from the Advanced toggle callback instead.

    variables={}
    for i,key in enumerate(ALIASES):
        row,col=divmod(i,2)
        ttk.Label(mapping,text=DISPLAY[key],width=25).grid(row=row,column=col*2,sticky='w',padx=(3,5),pady=3)
        variable=tk.StringVar(value='— Not mapped —')
        combo=ttk.Combobox(mapping,textvariable=variable,state='readonly',width=27,values=['— Not mapped —'])
        combo.grid(row=row,column=col*2+1,sticky='ew',padx=(0,15),pady=3)
        variables[key]=(variable,combo)
    mapping.columnconfigure(1,weight=1);mapping.columnconfigure(3,weight=1)
    def make_blank_template():
        target=filedialog.asksaveasfilename(parent=win,title='Save a blank experiment Excel template',
                       defaultextension='.xlsx',filetypes=[('Excel workbook','*.xlsx')],
                       initialfile='SPPS_Planner_V9_Experimental_Data_TEMPLATE.xlsx')
        if not target:return
        try:
            destination=create_blank_excel_template(target)
            messagebox.showinfo('Blank Excel template',
                                f'Empty workbook created at:\n{destination}\nEnter actual measurements, then import it for review.',
                                parent=win)
        except Exception as exc:
            messagebox.showerror('Blank template',str(exc),parent=win)
    ttk.Button(mapping,text='Create blank Excel template',command=make_blank_template).grid(
        row=(len(ALIASES)+1)//2,column=0,columnspan=2,sticky='w',pady=(7,2))
    def make_process_template():
        target=filedialog.asksaveasfilename(parent=win,title='Save process-level Excel template',
                   defaultextension='.xlsx',filetypes=[('Excel workbook','*.xlsx')],
                   initialfile='SPPS_Planner_V9_Process_Experiments_TEMPLATE.xlsx')
        if not target:return
        try:
            destination=create_process_excel_template(target)
            messagebox.showinfo('Process Excel template',f'Blank process workbook created:\n{destination}',parent=win)
        except Exception as exc: messagebox.showerror('Process template',str(exc),parent=win)
    ttk.Button(mapping,text='Create reaction-stage template',command=make_process_template).grid(
        row=(len(ALIASES)+1)//2,column=2,columnspan=2,sticky='e',pady=(7,2))

    advanced_open=tk.BooleanVar(value=False)
    def toggle_advanced():
        if advanced_open.get():
            mapping.pack(fill='x',pady=(4,4),before=info_label)
            advanced_tools.pack(fill='x',pady=(4,4),before=info_label)
        else:
            mapping.pack_forget()
            advanced_tools.pack_forget()
    advanced_toggle=ttk.Checkbutton(body,text='Advanced · Manual column mapping and learning',
                                    variable=advanced_open,command=toggle_advanced)
    advanced_toggle.pack(anchor='w',pady=(7,3))
    advanced_tools=ttk.Frame(body)
    # Keep manual import/review/target controls in separate rows so none can
    # disappear beyond the right edge at the supported 830px minimum width.
    advanced_import_row=ttk.Frame(advanced_tools)
    advanced_import_row.pack(fill='x',pady=(2,3))
    advanced_review_row=ttk.Frame(advanced_tools)
    advanced_review_row.pack(fill='x',pady=(2,3))
    advanced_target_row=ttk.Frame(advanced_tools)
    advanced_target_row.pack(fill='x',pady=(2,3))
    info=tk.StringVar(value='Choose an .xlsx, .csv or .tsv file. Korean/English headers supported.')
    info_label=ttk.Label(body,textvariable=info,wraplength=760)
    info_label.pack(anchor='w',pady=(4,4))
    preview_frame=ttk.LabelFrame(body,text='First 12 imported rows (preview only)')
    preview_frame.pack(fill='both',expand=True)
    tree=ttk.Treeview(preview_frame,show='headings',height=6)
    vbar=ttk.Scrollbar(preview_frame,orient='vertical',command=tree.yview)
    hbar=ttk.Scrollbar(preview_frame,orient='horizontal',command=tree.xview)
    tree.configure(xscrollcommand=hbar.set,yscrollcommand=vbar.set)
    tree.grid(row=0,column=0,sticky='nsew')
    vbar.grid(row=0,column=1,sticky='ns');hbar.grid(row=1,column=0,sticky='ew')
    preview_frame.columnconfigure(0,weight=1);preview_frame.rowconfigure(0,weight=1)
    percent_conversion=tk.BooleanVar(value=True)
    percent_check=ttk.Checkbutton(root,text='Convert Excel percentage-formatted cells (0.75 → 75%); uncheck if source is already 0–100.',variable=percent_conversion)
    percent_check.pack(anchor='w',pady=(5,0))
    consent=tk.BooleanVar(value=False)
    save_mode=tk.StringVar(value='append')
    mode_line=ttk.Frame(advanced_tools)
    mode_line.pack(fill='x',pady=(5,0))
    ttk.Label(mode_line,text='Save mode:').pack(side='left')
    ttk.Radiobutton(mode_line,text='Append to local reviewed dataset',variable=save_mode,value='append').pack(side='left',padx=(8,6))
    ttk.Radiobutton(mode_line,text='Replace reviewed dataset',variable=save_mode,value='replace').pack(side='left')
    consent_check=ttk.Checkbutton(advanced_tools,text='I reviewed the column mapping and confirm these are real experiment records (not planned, simulated or private-for-public sample data).',variable=consent)
    consent_check.pack(anchor='w',pady=(8,2))
    result=tk.Text(root,height=3,wrap='word',font=('Consolas',10))
    result.pack(fill='x',pady=(4,6));result.configure(state='disabled')
    target_var=tk.StringVar(value='actual_yield_percent')
    status=tk.StringVar(value='No data imported or trained.')
    status_label=ttk.Label(root,textvariable=status,wraplength=790)
    status_label.pack(anchor='w',pady=(0,5))
    buttons=ttk.Frame(root);buttons.pack(fill='x')
    secondary_buttons=ttk.Frame(root);secondary_buttons.pack(fill='x',pady=(5,0))
    action_buttons=[]
    cancel_training_button=None
    def busy_changed(busy):
        for control in action_buttons:
            if control.winfo_exists():
                unavailable = control.cget('text') == 'Compare current peptide' and not current_context
                control.configure(state='disabled' if busy or unavailable else 'normal')
        if cancel_training_button is not None:
            cancel_training_button.configure(state='normal' if busy and runner._process is not None else 'disabled')
        if busy:
            progress.start(35)
        else:
            progress.stop()
    runner=UiBackgroundRunner(win,busy_changed)
    progress=ttk.Progressbar(root,mode='indeterminate',length=120)
    progress.pack(fill='x',pady=(3,1))
    def on_error(label):
        return lambda exc: messagebox.showerror(label,str(exc),parent=win)
    win.protocol('WM_DELETE_WINDOW',runner.close)

    def set_result(value):
        result.configure(state='normal');result.delete('1.0','end');result.insert('1.0',str(value));result.configure(state='disabled')
    def set_tree(frame):
        for item in tree.get_children():tree.delete(item)
        cols=list(frame.columns)[:16]
        tree['columns']=cols
        for col in cols:
            tree.heading(col,text=str(col));tree.column(col,width=145,minwidth=70,stretch=False)
        for _,row in frame.head(12).iterrows():
            tree.insert('', 'end', values=[str(row.get(col,''))[:90] for col in cols])
    def reset_mapping(preview):
        for key,(var,combo) in variables.items():
            combo.configure(values=['— Not mapped —',*preview.columns]);var.set(preview.mapping.get(key,'— Not mapped —'))
    def do_preview(path, sheet=None):
        status.set(f'Reading {Path(path).name} in background. The window remains responsive.')
        def done(snapshot):
            state.update(preview=snapshot,normalized=None,report=None,accepted=False,result=None,reviewed_signature=None,current_staged=False)
            source.set(f'{Path(path).name} / {snapshot.sheet}');selected_sheet.set(snapshot.sheet)
            sheetbox.configure(values=snapshot.sheets)
            reset_mapping(snapshot);set_tree(snapshot.raw)
            consent.set(False)
            notes=state.get('scan_notices',[])
            info.set(snapshot.summary()+ ('\nWarnings: '+ '; '.join(snapshot.warnings) if snapshot.warnings else '')
                     + ('\nWorksheet scan: '+ '; '.join(notes[:4]) if notes else ''))
            status.set('Preview only — no data saved. Verify target is a measured percentage.')
            set_result('Detected headers automatically. Correct a field from the dropdown if needed.')
        return runner.submit(lambda:preview_file(path,sheet=sheet),done,on_error('Import Excel / CSV'))
    def choose():
        paths=filedialog.askopenfilenames(parent=win,title='Choose experimental outcome files (all data sheets supported)',
            filetypes=[('Excel / CSV', '*.xlsx *.xlsm *.csv *.tsv *.txt'),('Excel workbook','*.xlsx *.xlsm'),('CSV','*.csv'),('All files','*.*')])
        if paths:
            # Clear in-memory drafts only. No data is saved, sent or trained.
            state.update(staged=[],pending_paths=[],preview=None,normalized=None,
                         report=None,accepted=False,result=None,current_staged=False,
                         scan_notices=[],total_queue_count=0)
            scan_all=bool(scan_all_sheets.get())
            status.set('Scanning workbook headers in background; GUIDE and blank sheets are not imported automatically...')
            def queued(answer):
                worklist,notices=answer
                state['pending_paths']=list(worklist[1:])
                state['scan_notices']=list(notices)
                state['total_queue_count']=len(worklist)
                do_preview(*worklist[0])
            runner.submit(lambda:discover_import_sources(paths,all_data_sheets=scan_all),
                          queued,on_error('Select workbook sheets'))
    def change_sheet(_event=None):
        if runner.busy:return
        current=state['preview']
        if current and selected_sheet.get() and selected_sheet.get()!=current.sheet:
            do_preview(current.file_path,selected_sheet.get())
    sheetbox.bind('<<ComboboxSelected>>',change_sheet)
    def current_mapping():
        return {key:var.get() for key,(var,_) in variables.items() if var.get()!='— Not mapped —'}
    def review():
        try:
            preview=state['preview']
            if preview is None:raise ValueError('Choose an Excel/CSV file first.')
            chosen_mapping=current_mapping()
            convert=bool(percent_conversion.get())
            signature=(tuple(sorted(chosen_mapping.items())),convert)
            status.set('Checking and cleaning data in background...')
            def compute():
                return normalize_preview(preview,chosen_mapping,convert_excel_percent=convert)
            def done(answer):
                records,report=answer
                state.update(normalized=records,report=report,accepted=False,
                             reviewed_signature=signature,result=None)
                set_tree(records)
                info.set(f"Cleaned {len(records)}/{report['source_rows']} rows. Outcomes: {report['usable_targets']}.\n"+'; '.join(report['warnings']))
                status.set('Cleaned preview only. Check the outcomes and approve Save to local profile.')
                set_result('No training yet. Data are not imported into the actual run history automatically.')
                consent.set(False)
            runner.submit(compute,done,on_error('Review mapping'))
        except Exception as exc:messagebox.showerror('Review mapping',str(exc),parent=win)
    def current_reviewed():
        if state['current_staged']:
            raise ValueError('This file has already been staged.')
        if not consent.get():
            raise ValueError('Review the cleaned rows and check the approval box for this file.')
        preview=state['preview']
        if preview is None:
            raise ValueError('Choose a source file first.')
        if state['reviewed_signature']!=(tuple(sorted(current_mapping().items())),bool(percent_conversion.get())):
            raise ValueError('Mapping or percentage settings changed. Click Check & clean and approve again.')
        verify_preview_source(preview)
        records, report=state['normalized'],state['report']
        if records is None or report is None:
            raise ValueError('Click Check & clean before staging a reviewed file.')
        if not len(records):
            raise ValueError('No usable sequence rows.')
        return records,report,preview.file_sha256,preview
    def stage_current():
        try:
            item=current_reviewed()
            state['staged'].append(item)
            state['current_staged']=True
            consent.set(False)
            if state['pending_paths']:
                next_path,next_sheet=state['pending_paths'].pop(0)
                do_preview(next_path,next_sheet)
                status.set(f"{len(state['staged'])} approved worksheet(s) staged; {len(state['pending_paths'])} waiting.")
            else:
                status.set(f"{len(state['staged'])} approved file(s) staged. Use Save to persist; no chemistry or SOP has changed.")
                set_result('Ready to save. Data will be combined without silently removing possible replicates.')
        except Exception as exc:
            messagebox.showerror('Stage reviewed file',str(exc),parent=win)
    def skip_current_sheet():
        if runner.busy:
            return
        if not state['preview']:
            messagebox.showinfo('Skip worksheet','Choose source files first.',parent=win)
            return
        current=state['preview']
        state.update(preview=None,normalized=None,report=None,accepted=False,
                     reviewed_signature=None,current_staged=False)
        consent.set(False)
        if state['pending_paths']:
            next_path,next_sheet=state['pending_paths'].pop(0)
            do_preview(next_path,next_sheet)
        else:
            selected_sheet.set('')
            source.set('No pending worksheet')
            info.set('No remaining worksheet. Save only already approved worksheets, or choose more data.')
            status.set(f'{len(state["staged"])} approved worksheet(s) remain; skipped {Path(current.file_path).name} / {current.sheet}.')

    def capture_reviewed_items():
        items=list(state['staged'])
        if not state['current_staged'] and state['preview'] is not None:
            items.append(current_reviewed())
        if not items:
            raise ValueError('No approved records to combine.')
        return items
    def combine_previews(items):
        # Heavy merge/quality audit belongs to the worker, not Tk.
        for item in items:
            verify_preview_source(item[3])
        records,quality=combine_reviewed_tables(*(x[0] for x in items))
        digest=sha256('|'.join(x[2] for x in items).encode('utf-8')).hexdigest()
        return records,quality,digest
    def audit():
        try:
            items=capture_reviewed_items()
            mode=save_mode.get()
            data_dir,_=_locations(gui)
            status.set('Reviewing data quality in background...')
            def compute():
                records,quality,_=combine_previews(items)
                if mode=='append' and (data_dir/'ai_excel_reviewed_v9.json').exists():
                    previous,_=load_reviewed_dataset(data_dir)
                    records,quality=combine_reviewed_tables(previous,records)
                from suite_gui.experiment_feedback_v9 import summarize_stage_feedback
                return quality,ml_readiness_report(records),summarize_stage_feedback(records)
            def done(result_info):
                quality,readiness,feedback=result_info
                set_result(json_pretty({'quality_audit':quality,'training_readiness':readiness['targets'],
                                        'observed_stage_feedback':feedback}))
                status.set(f"Quality audit: {quality['total_rows']} rows; {quality['unique_parseable_sequence_groups']} unique sequences; {quality['duplicate_run_ids']} duplicate Run IDs. No changes saved.")
            runner.submit(compute,done,on_error('Data quality audit'))
        except Exception as exc:
            messagebox.showerror('Data quality audit',str(exc),parent=win)
    def save():
        try:
            if state['pending_paths']:
                raise ValueError('Review and stage the current file, then the remaining files, before saving.')
            items=capture_reviewed_items()
            mode=save_mode.get()
            if mode not in ('append','replace'):
                raise ValueError('Unknown save mode.')
            data_dir,_=_locations(gui)
            status.set('Combining approved files and verifying source integrity in background...')
            def prepare():
                return combine_previews(items)
            def prepared(answer):
                records,quality,digest=answer
                if not len(records):
                    messagebox.showerror('Save reviewed data','No valid sequence rows.',parent=win)
                    return
                report={'merge_mode':mode.upper(), 'source_count':len(items),
                    'sources':[{'sha256':x[2],'rows':len(x[0]),'file':Path(x[3].file_path).name,
                                'sheet':x[3].sheet,'mapping':x[1].get('mapping',{})} for x in items],
                    'quality_audit':quality}
                if not messagebox.askyesno('Confirm local import',
                       f"{len(items)} reviewed worksheet(s), {len(records)} new row(s).\n"
                       f"Mode: {mode.upper()} (existing data {'kept' if mode=='append' else 'replaced'}).\n"
                       f"Exact repeated rows: {quality['exact_duplicate_rows']}; conflicting Run IDs: {quality['conflicting_run_ids']}.\n"
                       'No cloud upload and no automatic SOP or Plan updates. Continue?',parent=win):
                    status.set('Import cancelled. Previously saved data unchanged.')
                    return
                status.set('Saving reviewed dataset atomically in background...')
                def write():
                    if mode=='append':
                        return append_reviewed_dataset(records,report,digest,data_dir)
                    return save_reviewed_dataset(records,report,digest,data_dir)
                def done(saved):
                    state.update(normalized=records,report=report,accepted=True,result=None,
                                 staged=[],pending_paths=[],current_staged=True)
                    status.set(f"Saved {saved['rows']} locally reviewed rows. Old models will be withheld until retrained.")
                    set_result('Saved local dataset at:\n'+saved['path']+'\nOnly reviewed actual observations may be used for training.')
                    if on_dataset_saved:
                        on_dataset_saved()
                runner.submit(write,done,on_error('Save reviewed data'))
            runner.submit(prepare,prepared,on_error('Save reviewed data'))
        except Exception as exc:
            messagebox.showerror('Save reviewed data',str(exc),parent=win)
    def train():
        try:
            data_dir,model_dir=_locations(gui)
            target=target_var.get()
            # Confirmation occurs on the Tk thread; all IO/sklearn work is off-thread.
            if not messagebox.askyesno('Train local AI',
                f'Train a local exploratory {"yield" if target=="actual_yield_percent" else "purity"} model from reviewed rows?\nThe model is advisory-only and never alters Plan/coupling/cleavage settings.',parent=win):return
            status.set('Training in isolated process. Cancel stops the ML process and leaves reviewed Excel records unchanged.')
            def done(output):
                state['result']=None
                set_result(json_pretty(output))
                status.set('Training finished. Examine held-out baseline, warning and model status.')
            data_dir,model_dir=_locations(gui)
            from suite_gui.process_ai_v9 import STAGE_TARGETS
            kind='stage' if target in STAGE_TARGETS else 'linear'
            runner.submit_training_process(kind,data_dir,model_dir,target,done,on_error('Training not available'))
        except Exception as exc:messagebox.showwarning('Training not available',str(exc),parent=win)
    def attach_checked(checked):
        if checked is not None and on_apply:
            on_apply(checked)
            status.set('AI review attached to open Auto Plan draft only; no conditions automatically applied.')
            messagebox.showinfo('AI evidence','Attached advisory evidence to the current Auto Plan review. It will appear in exported draft JSON.',parent=win)
    def advise(*,attach=False):
        try:
            if not current_context:
                raise ValueError('Open this assistant from Auto Plan to compare an active sequence.')
            # Copy context on the UI thread to avoid observing an in-flight form edit.
            context=dict(current_context)
            data_dir,model_dir=_locations(gui)
            target=target_var.get()
            status.set('Searching similar experiments and verifying the local model in background...')
            def done(checked):
                state['result']=checked
                set_result(json_pretty(checked))
                status.set('Read-only AI evidence; no synthesis parameters changed.')
                if attach:attach_checked(checked)
            from suite_gui.process_ai_v9 import STAGE_TARGETS,advise_stage
            if target in STAGE_TARGETS:
                context['reaction_step']=STAGE_TARGETS[target]
                operation=lambda:advise_stage(context,data_dir,model_dir,target)
            else:
                operation=lambda:advise_from_local_data(context,data_dir,model_dir,target=target)
            runner.submit(operation,done,on_error('AI evidence'))
        except Exception as exc:messagebox.showerror('AI evidence',str(exc),parent=win)
    def use_in_plan():
        if state['result'] is None:
            advise(attach=True)
        else:
            attach_checked(state['result'])
    def restore():
        try:
            data_dir,_=_locations(gui)
            if not messagebox.askyesno('Restore reviewed dataset',
                 'Restore the previous validated Excel/CSV dataset backup?\n'
                 'This replaces the current reviewed dataset and may invalidate local ML models.',parent=win):
                return
            status.set('Verifying and restoring previous dataset in background...')
            def done(info):
                state['result']=None
                status.set(f"Restored {info['restored_rows']} rows. Retrain local AI before using old predictions.")
                set_result(json_pretty(info))
            runner.submit(lambda:restore_last_good_dataset(data_dir),done,on_error('Restore reviewed dataset'))
        except Exception as exc:
            messagebox.showerror('Restore reviewed dataset',str(exc),parent=win)
    action_buttons.append(ttk.Button(advanced_review_row,text='Restore previous dataset',command=restore))
    action_buttons[-1].pack(side='right')
    action_buttons.append(ttk.Button(advanced_import_row,text='1. Choose Excel(s) / CSV(s)',command=choose))
    action_buttons[-1].pack(side='left',padx=(0,4))
    action_buttons.append(ttk.Button(advanced_import_row,text='2. Check & clean',command=review))
    action_buttons[-1].pack(side='left',padx=4)
    action_buttons.append(ttk.Button(advanced_import_row,text='3. Save combined data',command=save))
    action_buttons[-1].pack(side='left',padx=4)
    action_buttons.append(ttk.Button(advanced_import_row,text='4. Train local AI',command=train))
    action_buttons[-1].pack(side='left',padx=4)
    ttk.Label(advanced_target_row,text='ML target:').pack(side='left',padx=(10,3))
    ttk.Combobox(advanced_target_row,textvariable=target_var,state='readonly',width=23,
       values=['actual_yield_percent','actual_purity_percent','coupling_conversion_percent',
               'cyclization_yield_percent','crude_yield_percent',
               'purification_recovery_percent','cleavage_recovery_percent']).pack(side='left')
    def cancel_training_action():
        if runner.cancel_training():
            status.set('Training process cancelled. Existing saved dataset unchanged; do not use incomplete model files.')
            state['result']=None
    def auto_import_and_train():
        paths=filedialog.askopenfilenames(parent=win,title='Import complete experimental workbooks',
            filetypes=[('Excel and tables','*.xlsx *.xlsm *.csv *.tsv *.txt'),
                       ('All supported','*.xlsx *.xlsm *.csv *.tsv *.txt')])
        if not paths:return
        status.set('Analyzing all data worksheets, detected targets and quality in background...')
        def computed(assessment):
            if not assessment['ready']:
                set_result('Automatic import paused:\n'+'\n'.join(assessment['blockers']))
                status.set('Automatic mapping needs review; expand Advanced to correct source fields.')
                return
            sources=assessment['sources']
            quality=assessment['quality']
            targets=assessment['targets']
            warning_count=len(assessment['notices'])
            text=(f"Analyzed {len(sources)} worksheet(s), {quality['total_rows']} rows.\n"
                  f"Detected measured outcomes: {', '.join(sorted({k for s in sources for k in s['targets']}))}.\n"
                  f"Training candidates: {', '.join(targets) if targets else 'none (insufficient data)'}.\n"
                  f"Data warnings: {warning_count}; duplicates: {quality['exact_duplicate_rows']}.\n"
                  'Please confirm that these values are REAL measured experimental data, not planned or simulated results.\n'
                  'The app will save locally and learn eligible targets; no chemistry or Plan will be changed.\n'
                  'Continue?')
            if not messagebox.askyesno('Review automatic data import',text,parent=win):
                status.set('Automatic import cancelled; no files modified.')
                return
            data_dir,model_dir=_locations(gui)
            mode=save_mode.get()
            if mode not in ('replace','append'):mode='append'
            def store():
                # Re-check sources immediately before making any persistent changes.
                for origin in sources:
                    original=next((Path(p) for p in paths if Path(p).name==origin['file']),None)
                    if original is None or _sha256_file(original)!=origin['sha256']:
                        raise ValueError('Source file changed since analysis. Import cancelled.')
                from suite_gui.ai_excel_core_v9 import save_reviewed_dataset, append_reviewed_dataset
                report={'auto_detected':True,'merge_mode':mode.upper(),
                        'sources':sources,'quality_audit':quality,
                        'reviewed_by_user':True,'warnings':assessment['notices']}
                if mode=='append' and (data_dir/'ai_excel_reviewed_v9.json').exists():
                    previous,_=load_reviewed_dataset(data_dir)
                    merged, quality_check=combine_reviewed_tables(previous,assessment['records'])
                    if quality_check['training_blocked']:
                        raise ValueError('Existing data overlap or conflict with imported rows. No changes saved; inspect in Advanced.')
                if mode=='append':
                    info=append_reviewed_dataset(assessment['records'],report,assessment['source_digest'],data_dir)
                else:
                    info=save_reviewed_dataset(assessment['records'],report,assessment['source_digest'],data_dir)
                saved_records,_=load_reviewed_dataset(data_dir)
                return info, __import__('suite_gui.ai_auto_import_v9',fromlist=['plan_training_targets']).plan_training_targets(saved_records)
            def stored(value):
                info, eligible=value
                if on_dataset_saved:
                    on_dataset_saved()
                if not eligible:
                    status.set(f"Saved {info['rows']} observed rows. Not enough reliable labeled data to train.")
                    set_result('Saved reviewed experimental data locally. Training withheld until enough valid measurements are available.')
                    return
                outcomes=[]
                def next_task(index):
                    if index>=len(eligible):
                        status.set(f'Automatic learning complete: {len(outcomes)} target(s) evaluated. Review model metrics before use.')
                        set_result(json_pretty({'saved_rows':info['rows'],'training_results':outcomes}))
                        return
                    target=eligible[index]
                    from suite_gui.process_ai_v9 import STAGE_TARGETS
                    kind='stage' if target in STAGE_TARGETS else 'linear'
                    status.set(f'Learning {index+1}/{len(eligible)}: {target}. No synthesis plan will be changed.')
                    def succeeded(report):
                        outcomes.append({'target':target,'result':report})
                        next_task(index+1)
                    def failed(exc):
                        outcomes.append({'target':target,'error':str(exc)})
                        next_task(index+1)
                    runner.submit_training_process(kind,data_dir,model_dir,target,succeeded,failed)
                next_task(0)
            status.set('Saving approved measurement records locally...')
            runner.submit(store,stored,on_error('Automatic import save'))
        from suite_gui.ai_auto_import_v9 import analyze_workbooks
        runner.submit(lambda:analyze_workbooks(paths),computed,on_error('Automatic data analysis'))
    action_buttons.append(ttk.Button(buttons,text='Import File(s) → Auto Analyze & Learn',command=auto_import_and_train))
    action_buttons[-1].pack(side='left',padx=(0,8))
    cancel_training_button=ttk.Button(secondary_buttons,text='Cancel training',
                                     command=cancel_training_action,state='disabled')
    cancel_training_button.pack(side='right',padx=(5,0))
    action_buttons.append(ttk.Button(advanced_review_row,text='Stage reviewed file / Next',command=stage_current))
    action_buttons[-1].pack(side='left',padx=(0,6))
    action_buttons.append(ttk.Button(advanced_review_row,text='Skip worksheet',command=skip_current_sheet))
    action_buttons[-1].pack(side='left',padx=(0,6))
    action_buttons.append(ttk.Button(advanced_review_row,text='Audit data quality',command=audit))
    action_buttons[-1].pack(side='left',padx=(0,6))
    action_buttons.append(ttk.Button(secondary_buttons,text='Compare current peptide',command=advise,state='normal' if current_context else 'disabled'))
    action_buttons[-1].pack(side='left',padx=(0,6))
    if on_apply:
        action_buttons.append(ttk.Button(secondary_buttons,text='Attach evidence (review only)',command=use_in_plan))
        action_buttons[-1].pack(side='left',padx=(0,6))
    ttk.Button(secondary_buttons,text='Close',command=runner.close).pack(side='right')
    # Footer controls are laid out before the expanding scrollable body,
    # preventing Tk's pack manager from hiding actions on low-height screens.
    for widget, options in (
        (secondary_buttons, {'fill':'x','pady':(5,0)}),
        (buttons, {'fill':'x'}),
        (status_label, {'anchor':'w','pady':(0,5)}),
        (result, {'fill':'x','pady':(4,6)}),
        (percent_check, {'anchor':'w','pady':(5,0)}),
        (progress, {'fill':'x','pady':(3,1)}),
    ):
        widget.pack_forget()
        widget.pack(side='bottom', **options)
    body_scroll.pack(side='right',fill='y')
    body_canvas.pack(side='left',fill='both',expand=True)
    # Scroll when hovering over explanatory labels and frames, but leave
    # editable inputs and the table's own scrollbars under their native control.
    def _scroll_bindings(widget):
        for child in widget.winfo_children():
            if not isinstance(child,(ttk.Combobox,ttk.Entry,ttk.Treeview,ttk.Scrollbar)):
                for event in ('<MouseWheel>','<Button-4>','<Button-5>'):
                    child.bind(event,_body_wheel,add='+')
                _scroll_bindings(child)
    _scroll_bindings(body)
    return win


def json_pretty(data):
    import json
    return json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)
