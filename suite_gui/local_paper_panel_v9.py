"""Responsive Tk opt-in local paper search, no network or hidden file uploads."""
from __future__ import annotations
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter.scrolledtext import ScrolledText


def open_local_paper_panel(parent):
    from spps_planner.local_fulltext_v9 import index_local_documents,search_local_fulltext
    from spps_planner.grounded_literature_ai_v9 import (
        prepare_literature_packet, request_grounded_literature_review)
    win=tk.Toplevel(parent)
    win.title('V9.0.0 | Local literature evidence (PDF/TXT/MD)')
    win.geometry('760x530');win.minsize(560,410)
    f=ttk.Frame(win,padding=12);f.pack(fill='both',expand=True)
    ttk.Label(f,text='Local, operator-supplied full-text search — page-cited excerpts only',
             font=('Segoe UI',11,'bold')).pack(anchor='w')
    ttk.Label(f,text='Files stay on this machine. Scanned PDFs without text are not OCRed. '
             'Retrieved fragments cannot be treated as validated synthesis conditions.',
             wraplength=700).pack(anchor='w',pady=4)
    row=ttk.Frame(f);row.pack(fill='x',pady=(5,0))
    query=tk.StringVar(value='cyclization')
    ttk.Entry(row,textvariable=query,width=35).pack(side='left')
    q=queue.Queue();state={'index':None,'busy':False,'closed':False,'last_packet':None,'search_term':None}
    output=ScrolledText(f,wrap='word',font=('Consolas',10));output.pack(fill='both',expand=True,pady=8)
    output.insert('1.0','Select local full-text documents before searching.\n')
    status=ttk.Label(f,text='No local documents indexed.');status.pack(anchor='w')
    buttons=ttk.Frame(f);buttons.pack(fill='x')
    def render(value):
        output.delete('1.0','end')
        import json
        output.insert('1.0',json.dumps(value,ensure_ascii=False,indent=2))
    def submit(worker):
        if state['busy'] or state['closed']:return
        state['busy']=True;open_button.config(state='disabled');search_button.config(state='disabled');ai_button.config(state='disabled')
        def run():
            try:q.put(('ok',worker()))
            except Exception as exc:q.put(('error',f'{type(exc).__name__}: {exc}'[:300]))
        threading.Thread(target=run,daemon=True).start()
    def choose():
        filenames=filedialog.askopenfilenames(parent=win,title='Select local documents',
            filetypes=[('Supported documents','*.pdf *.txt *.md')])
        if filenames:
            state['last_packet']=None
            submit(lambda:('indexed',index_local_documents(list(filenames))))
    def search():
        if state['index'] is None:
            status.config(text='Index local documents first.')
            return
        index=state['index'];needle=query.get()
        state['last_packet']=None
        state['search_term']=needle
        submit(lambda:('search',search_local_fulltext(index,needle)))
    def ai_preview():
        # Two-step, opt-in workflow: show the exact bytes of paper excerpts
        # before the user may initiate an external provider request.
        if state['busy'] or state['closed'] or state['last_packet'] is None:
            status.config(text='Search local texts and inspect the snippets first.')
            return
        packet=state['last_packet']
        preview=tk.Toplevel(win)
        preview.title('Explicit consent | Excerpts leaving this computer')
        preview.geometry('670x460');preview.minsize(500,330);preview.transient(win)
        body=ttk.Frame(preview,padding=12);body.pack(fill='both',expand=True)
        ttk.Label(body,text='Only the passages below and your search question will be sent via HTTPS.',
                  wraplength=620).pack(anchor='w')
        ttk.Label(body,text='No private project, entire PDF, local filename, database or experiment history is sent. '
                  'External API use may incur charges; OpenAI API key and selected model are required.',
                  wraplength=620).pack(anchor='w',pady=(2,6))
        content=ScrolledText(body,wrap='word',height=15)
        content.pack(fill='both',expand=True)
        import json
        content.insert('1.0',json.dumps(packet,ensure_ascii=False,indent=2))
        content.config(state='disabled')
        actions=ttk.Frame(body);actions.pack(fill='x',pady=(8,0))
        def authorize():
            # Refuse requests if a new search replaced the preview while open.
            if state['closed'] or state['busy'] or packet is not state['last_packet']:
                preview.destroy()
                return
            preview.destroy()
            submit(lambda:('ai',request_grounded_literature_review(packet,explicit_consent=True)))
        ttk.Button(actions,text='Cancel — keep everything local',command=preview.destroy).pack(side='right')
        ttk.Button(actions,text='I consent: analyze selected excerpts',command=authorize).pack(side='right',padx=8)

    open_button=ttk.Button(row,text='Load local documents' ,command=choose);open_button.pack(side='left',padx=8)
    search_button=ttk.Button(row,text='Search cited text',command=search);search_button.pack(side='left')
    ai_button=ttk.Button(buttons,text='AI review selected excerpts...',command=ai_preview,state='disabled')
    ai_button.pack(side='left')
    ttk.Button(buttons,text='Close',command=win.destroy).pack(side='right')
    def poll():
        if state['closed'] or not win.winfo_exists():return
        try:
            kind,value=q.get_nowait()
        except queue.Empty:
            win.after(80,poll);return
        state['busy']=False;open_button.config(state='normal');search_button.config(state='normal')
        ai_button.config(state='normal' if state['last_packet'] is not None else 'disabled')
        if kind=='error':status.config(text='Local index/search failed (no data changed).');render({'error':value})
        else:
            action,content=value
            if action=='indexed':
                state['index']=content
                status.config(text=f"Indexed {content['document_count']} local document(s), {len(content['fragments'])} chunks")
                render({'status':content['status'],'warnings':content['warnings'],'fragments':len(content['fragments'])})
            elif action=='search':
                status.config(text=f"Search result: {content['status']}")
                render(content)
                try:
                    if state['search_term'] == query.get():
                        state['last_packet']=prepare_literature_packet(state['index'],state['search_term'])
                    else:
                        state['last_packet']=None
                except ValueError:
                    state['last_packet']=None
                ai_button.config(state='normal' if state['last_packet'] else 'disabled')
            else:
                status.config(text='Source-quotation-checked AI draft; experimenter review required.')
                render(content)
        win.after(80,poll)
    query.trace_add('write',lambda *_: (state.update(last_packet=None), ai_button.config(state='disabled')))
    def closed(e):
        if e.widget is win:state['closed']=True
    win.bind('<Destroy>',closed,add='+')
    win.after(80,poll)
    return win
