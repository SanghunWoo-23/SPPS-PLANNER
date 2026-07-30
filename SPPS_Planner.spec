# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project = Path(SPECPATH)
datas = [
    (str(project / "apps"), "apps"),
    (str(project / "suite_gui"), "suite_gui"),
    (str(project / "peptiforg_core"), "peptiforg_core"),
    (str(project / "assets"), "assets"),
    (str(project / "docs"), "docs"),
    (str(project / "VERSION.txt"), "."),
]
hiddenimports = [
    "suite_gui.spps_tk_gui",
    "suite_gui.release",
    "suite_gui.release_composition",
    "suite_gui.release_contract",
    "suite_gui.modules.classic_workflow",
    "suite_gui.modules.workbench_workflow",
    "suite_gui.legacy_controller",
    "peptiforg_core.ui_helpers",
    "spps_planner",
    "spps_planner.engine",
    "spps_planner.parser",
    "spps_planner.export",
    "spps_planner.database",
    "tkinter",
    "tkinter.ttk",
    "tkinter.filedialog",
    "tkinter.messagebox",
]

a = Analysis(
    [str(project / "main_launcher.py")],
    pathex=[str(project), str(project / "apps" / "spps_planner_app")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["jedi", "IPython", "notebook", "jupyter", "matplotlib"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SPPS_Planner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(project / "assets" / "SPPS_Planner_Icon.ico"),
    version=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SPPS_Planner",
)
