from __future__ import annotations
import os, sys
from pathlib import Path
import tkinter as tk

ROOT = Path(__file__).resolve().parents[1]

def _asset_path(name: str) -> Path:
    # PyInstaller one-file/frozen support
    base = Path(getattr(sys, "_MEIPASS", ROOT))
    p = base / "assets" / name
    if p.exists():
        return p
    return ROOT / "assets" / name

def set_pepforge_icon(window: tk.Tk | tk.Toplevel) -> None:
    """Apply the SPPS Planner icon to standalone Tk windows.

    The legacy function name is retained for source compatibility.
    SPPS Planner uses its own release icon assets.
    """
    applied = False
    ico = _asset_path("SPPS_Planner_Icon.ico")
    if os.name == "nt" and ico.exists():
        try:
            window.iconbitmap(default=str(ico))
            applied = True
        except tk.TclError:
            try:
                window.iconbitmap(str(ico))
                applied = True
            except tk.TclError:
                applied = False

    if not applied:
        for fname in ("SPPS_Planner_Icon.png",):
            png = _asset_path(fname)
            if not png.exists():
                continue
            try:
                img = tk.PhotoImage(file=str(png))
                window.iconphoto(True, img)
                # Keep a Python reference; otherwise Tk may discard the image.
                setattr(window, "_pepforge_icon_img", img)
                applied = True
                break
            except tk.TclError:
                continue

    setattr(window, "_spps_icon_status", "OK" if applied else "MISSING")

def open_path(path: str | Path) -> None:
    p = Path(path)
    if os.name == "nt":
        os.startfile(str(p))
    elif sys.platform == "darwin":
        os.system(f'open "{p}"')
    else:
        os.system(f'xdg-open "{p}"')
