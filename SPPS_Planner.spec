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
    (str(project / "VERSION"), "."),
    (str(project / "VERSION.txt"), "."),
]
# Ensure native RDKit chemistry modules and local PDF reader are packaged.
rdkit_datas, rdkit_binaries, rdkit_hiddenimports = collect_all('rdkit')
pypdf_datas, pypdf_binaries, pypdf_hiddenimports = collect_all('pypdf')
datas.extend(rdkit_datas + pypdf_datas)
hiddenimports = [
    "suite_gui.spps_tk_gui",
    "suite_gui.release",
    "suite_gui.controller",
    "suite_gui.classic_base",
    "suite_gui.ui_system",
    "suite_gui.work_item_window",
    "suite_gui.batch_workflow",
    "suite_gui.data_system",
    "suite_gui.data_workflow",
    "suite_gui.data_workbook",
    "suite_gui.execution_workflow",
    "suite_gui.experimental_data",
    "suite_gui.experimental_workflow",
    "suite_gui.v6_features",
    "suite_gui.ml_advisor_v4",
    "suite_gui.modules.experimental_data_panel",
    "suite_gui.ml_dataset",
    "suite_gui.ml_workflow",
    "suite_gui.auto_plan_option_v9",
    "suite_gui.ai_excel_core_v9",
    "suite_gui.ai_excel_dialog_v9",
    "suite_gui.ai_background_v9",
    "suite_gui.persistence_workflow",
    "suite_gui.project_workflow",
    "suite_gui.risk_assessment",
    "suite_gui.risk_engine",
    "suite_gui.risk_workflow",
    "suite_gui.runtime_selftest",
    "suite_gui.local_paper_panel_v9",
    "spps_planner.atomic_topology_v9",
    "spps_planner.monomer_catalog_v9",
    "spps_planner.local_fulltext_v9",
    "suite_gui.synthesis_workflow",
    "suite_gui.ui_build",
    "suite_gui.release_contract",
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
hiddenimports.extend(rdkit_hiddenimports + pypdf_hiddenimports)

a = Analysis(
    [str(project / "main_launcher.py")],
    pathex=[str(project), str(project / "apps" / "spps_planner_app")],
    binaries=rdkit_binaries + pypdf_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["jedi", "IPython", "notebook", "jupyter", "matplotlib", "pytest", "torch", "tensorflow", "tensorboard"],
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
    version=str(project / "installer" / "version_info.txt"),
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
