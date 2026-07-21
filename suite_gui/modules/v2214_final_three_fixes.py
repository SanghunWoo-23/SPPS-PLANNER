"""V2.2.14 focused fixes: sequence chemicals, CTC(합성용), compact checklist."""
from __future__ import annotations
import re
from tkinter import ttk

APP_VERSION='V2.2.15'
VERSION_LABEL='SPPS Planner GitHub V2.2.15'

AC_AA = [
'Ac-Ala-OH','Ac-Arg(Pbf)-OH','Ac-Asn(Trt)-OH','Ac-Asp(OtBu)-OH','Ac-Cys(Trt)-OH',
'Ac-Gln(Trt)-OH','Ac-Glu(OtBu)-OH','Ac-Gly-OH','Ac-His(Trt)-OH','Ac-Ile-OH',
'Ac-Leu-OH','Ac-Lys(Boc)-OH','Ac-Met-OH','Ac-Phe-OH','Ac-Pro-OH','Ac-Ser(tBu)-OH',
'Ac-Thr(tBu)-OH','Ac-Trp(Boc)-OH','Ac-Tyr(tBu)-OH','Ac-Val-OH']

ACTIVE_RESINS = [
'Rink Amide AM','Rink Amide MBHA','Rink Amide ChemMatrix','Rink Amide Tentagel',
'2-CTC','CTC(합성기)','Wang','HMPB','Sieber Amide','PAL resin','Tentagel','Manual']


def _walk(root):
    try: children=root.winfo_children()
    except Exception: return
    for c in children:
        yield c
        yield from _walk(c)


def _patch_parser():
    from spps_planner import parser
    for name in AC_AA:
        if name not in parser.NTERM_MODIFIERS:
            parser.NTERM_MODIFIERS.append(name)
        parser.NTERM_MODIFIER_ALIASES[parser._norm_key(name)] = name
    # longest known names can contain more than four dash-separated pieces.
    def consume(parts):
        if not parts: return '', parts
        for n in range(min(8,len(parts)),0,-1):
            cand='-'.join(parts[:n])
            mod=parser._normalise_nterm_modifier(cand)
            if mod: return mod, parts[n:]
        return '',parts
    parser._consume_leading_nterm_modifier=consume
    try:
        from spps_planner import engine
        engine.parse_sequence = parser.parse_sequence
    except Exception:
        pass


def _restore_resin_widgets(gui):
    try:
        gui.RESIN_VALUES=list(ACTIVE_RESINS)
        type(gui).RESIN_VALUES=list(ACTIVE_RESINS)
    except Exception: pass
    for w in _walk(gui):
        if isinstance(w,ttk.Combobox):
            try:
                vals=[str(v) for v in w.cget('values')]
                if any(('CTC' in v or 'Rink Amide' in v) for v in vals):
                    current=str(w.get() or '')
                    w.configure(values=ACTIVE_RESINS)
                    if current in ACTIVE_RESINS: w.set(current)
            except Exception: pass


def _compact_checklist(gui):
    tree=getattr(gui,'progress_tree',None)
    if tree is None: return
    widths={'line':42,'done':48,'checked_at':88,'operation':145,'unit':105,'next_step':145,'note':220}
    try:
        tree.configure(height=16)
        for col in tree['columns']:
            tree.column(col,width=widths.get(col,90),minwidth=30,stretch=(col=='note'),anchor='w')
    except Exception: pass
    # Keep only a compact single-line control band above the table.
    try:
        parent=tree.master
        parent.rowconfigure(1,weight=1,minsize=240)
        for child in parent.winfo_children():
            info=child.grid_info()
            if int(info.get('row',-1))==0:
                try: child.configure(padding=(3,2))
                except Exception: pass
    except Exception: pass


def install(gui_cls, ns, *_a, **_k):
    _patch_parser()
    try:
        import suite_gui.modules.v2213_operator_final_restore as v2213
        def only_explicit_fmoc_row(row):
            unit = re.sub(r'[^a-z0-9]+', '', str(row.get('Unit name','')).lower())
            return unit in {'fmocremoval','deprotectiononly'}
        v2213._is_fmoc_removal = only_explicit_fmoc_row
    except Exception:
        pass
    old=gui_cls._build
    def build(self):
        old(self)
        _restore_resin_widgets(self)
        _compact_checklist(self)
        try:self.title(VERSION_LABEL)
        except Exception:pass
    gui_cls._build=build
    gui_cls.TITLE=VERSION_LABEL
    return gui_cls
