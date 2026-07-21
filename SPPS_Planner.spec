# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

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
for package in ("pandas", "numpy", "openpyxl", "sklearn", "joblib"):
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    hiddenimports += package_hidden
    if package == "pandas":
        pandas_binaries = package_binaries
    elif package == "numpy":
        numpy_binaries = package_binaries
    elif package == "openpyxl":
        openpyxl_binaries = package_binaries
    elif package == "sklearn":
        sklearn_binaries = package_binaries
    else:
        joblib_binaries = package_binaries
binaries = pandas_binaries + numpy_binaries + openpyxl_binaries + sklearn_binaries + joblib_binaries

a = Analysis(
    [str(project / "main_launcher.py")],
    pathex=[str(project), str(project / "apps" / "spps_planner_app")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["jedi", "IPython", "notebook", "jupyter", "matplotlib", "scipy"],
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
