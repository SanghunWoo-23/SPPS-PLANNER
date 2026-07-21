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

    The old function name is kept for compatibility with Pepforge/SPPS shared code,
    but this planner should prefer SPPS_Planner_Icon.* over Pepforge_Icon.*.
    """
    try:
        ico = _asset_path("SPPS_Planner_Icon.ico")
        if ico.exists() and os.name == "nt":
            try:
                window.iconbitmap(default=str(ico))
            except Exception:
                try:
                    window.iconbitmap(str(ico))
                except Exception:
                    pass
    except Exception:
        pass
    try:
        for fname in ("SPPS_Planner_Icon.png", "Pepforge_Icon.png"):
            png = _asset_path(fname)
            if png.exists():
                img = tk.PhotoImage(file=str(png))
                window.iconphoto(True, img)
                # keep a Python reference; otherwise Tk may discard the image
                setattr(window, "_pepforge_icon_img", img)
                setattr(window, "_spps_icon_status", "OK")
                return
        setattr(window, "_spps_icon_status", "MISSING")
    except Exception as e:
        try:
            setattr(window, "_spps_icon_status", f"ERROR: {e}")
        except Exception:
            pass

def open_path(path: str | Path) -> None:
    p = Path(path)
    if os.name == "nt":
        os.startfile(str(p))
    elif sys.platform == "darwin":
        os.system(f'open "{p}"')
    else:
        os.system(f'xdg-open "{p}"')
