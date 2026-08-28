# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

project_dir = Path(os.getcwd())
gui_dir = project_dir / "lx" / "gui"
stuff_dir = project_dir / "lx" / "stuff"
mfql_dir = project_dir / "lx" / "mfql"

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"

hidden_lx = collect_submodules("lx")

# Confirmed unused by inspecting the shipped 1.5.0 bundle. The tkinter stack
# alone is ~10 MB and Pythonwin another 6.4 MB, none of it imported anywhere
# in this project.
excludes = [
    "tkinter",
    "_tkinter",
    "Tkinter",
    "Pythonwin",
    "setuptools",
    "pkg_resources",
    "wheel",
    "pytest",
    "IPython",
]
if not IS_WINDOWS:
    excludes += ["comtypes", "win32com", "pythoncom", "pywintypes"]

# lipidx_ico2.ico maxes out at 47x48 px. lipidx_tb.ico is a true 256x256 and
# is what the packaged executable should carry.
icon_file = str(stuff_dir / ("lipidx.icns" if IS_MACOS else "lipidx_tb.ico"))

a = Analysis(
    ["LipidXplorer.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(gui_dir / "lpdxImportSettings_benchmark.ini"), "lx/gui"),
        (str(gui_dir / "lpdxopts.ini"), "lx/gui"),
        (str(stuff_dir / "*.png"), "lx/stuff"),
        (str(stuff_dir / "*.ico"), "lx/stuff"),
        (str(mfql_dir / "parsetab.py"), "lx/mfql"),
    ],
    hiddenimports=[
        "lx",
        "lx.batch_processor",
        "lx.spectraImport",
        "lx.spectraContainer",
        "lx.mfql.runtimeExecution",
        "lx.mfql.mfqlParser",
        "lx.mfql.parsetab",
    ]
    + hidden_lx,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LipidXplorer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="LipidXplorer",
)

if IS_MACOS:
    # Without BUNDLE, macOS gets a bare Unix executable: no menu bar, no Dock
    # identity, and wx cannot behave like a native application.
    app = BUNDLE(
        coll,
        name="LipidXplorer.app",
        icon=icon_file,
        bundle_identifier="de.isas.lifs.lipidxplorer",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "CFBundleShortVersionString": "1.5.0",
            "CFBundleVersion": "1.5.0",
        },
    )
