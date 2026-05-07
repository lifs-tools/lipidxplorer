# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

project_dir = Path(os.getcwd())
gui_dir = project_dir / "lx" / "gui"
stuff_dir = project_dir / "lx" / "stuff"
mfql_dir = project_dir / "lx" / "mfql"

hidden_lx = collect_submodules("lx")

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
    ] + hidden_lx,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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