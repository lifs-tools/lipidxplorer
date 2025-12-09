# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['LipidXplorer.py'],      # MUST match exe script
    pathex=['.'],
    binaries=[],

    # include full lx package
    datas=[('lx/**/*', 'lx')],

    hiddenimports=[
        'lx',
        'lx.batch_processor',
        'lx.spectraImport',
        'lx.spectraContainer',
        'lx.mfql.runtimeExecution',
        'lx.mfql.mfqlParser',
    ],

    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# >>> THE FIXED EXE BLOCK <<
exe = EXE(
    'LipidXplorer.py',      # Instead of (pyz, a.scripts,...)
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,

    name='LipidXplorer',
    debug=False,
    strip=False,
    upx=True,
    console=True,

    # >>> CRITICAL FOR MULTIPROCESSING <<
    multiprocessing=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='LipidXplorer'
)
