"""Actual Tk UI contract; no monkey patching of production functions."""
import tkinter as tk
import pytest


def find_button(widget,text):
    for child in widget.winfo_children():
        if isinstance(child,(tk.Button,)) or child.winfo_class()=='TButton':
            if child.cget('text')==text:return child
        nested=find_button(child,text)
        if nested:return nested
    return None


def make_root():
    try:
        root=tk.Tk()
        root.withdraw()
        return root
    except tk.TclError:
        pytest.skip('No Tk display available')


def test_withheld_graph_cannot_attach_review():
    from suite_gui.structure_review_panel_v9 import open_structure_review
    root=make_root(); attached=[]
    try:
        review=open_structure_review(root,sequence='X',resin='2-CTC',on_attach=attached.append)
        find_button(review,'Compute molecular graph').invoke()
        find_button(review,'Attach review to Auto Plan').invoke()
        assert not attached
        assert review.winfo_exists()
    finally:
        root.destroy()


def test_good_graph_can_attach_review():
    from suite_gui.structure_review_panel_v9 import open_structure_review
    root=make_root(); attached=[]
    try:
        review=open_structure_review(root,sequence='AS',resin='2-CTC',on_attach=attached.append)
        find_button(review,'Compute molecular graph').invoke()
        find_button(review,'Attach review to Auto Plan').invoke()
        assert len(attached)==1,attached
        assert attached[0]['graph']['status']=='CROSSCHECK_PASS'
    finally:
        root.destroy()


def test_local_document_ai_button_disabled_without_evidence():
    from suite_gui.local_paper_panel_v9 import open_local_paper_panel
    root=make_root()
    try:
        review=open_local_paper_panel(root)
        button=find_button(review,'AI review selected excerpts...')
        assert button is not None
        assert str(button.cget('state'))=='disabled'
        review.destroy()
    finally:
        root.destroy()
