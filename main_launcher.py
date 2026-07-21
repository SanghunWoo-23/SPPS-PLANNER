from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

APP_NAME = "SPPS Planner"
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
RUNTIME_LOG_DIR = ROOT / "outputs" / "runtime_logs"


def _ensure_runtime_environment() -> None:
    os.chdir(ROOT)
    for p in [ROOT, ROOT / "suite_gui", ROOT / "peptiforg_core", ROOT / "apps" / "spps_planner_app"]:
        sp = str(p)
        if sp not in sys.path:
            sys.path.insert(0, sp)
    try:
        RUNTIME_LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def main() -> None:
    _ensure_runtime_environment()
    try:
        from suite_gui.spps_tk_gui import main as spps_main
        spps_main()
    except Exception as exc:
        log_path = RUNTIME_LOG_DIR / "spps_planner_runtime_error.log"
        try:
            log_path.write_text(traceback.format_exc(), encoding="utf-8")
        except Exception:
            pass
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "SPPS Planner launch failed",
                f"SPPS Planner failed to open.\n\nError: {exc}\n\nLog:\n{log_path}",
            )
            root.destroy()
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
