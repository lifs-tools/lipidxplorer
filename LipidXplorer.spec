# -*- mode: python -*-
import os, sys, shutil

# copy assets to dist
assetsDir = "lx/stuff/"
if os.path.isdir("dist/lx/"):
    shutil.rmtree("dist/lx/")

shutil.copytree(assetsDir, "dist/lx/stuff/")

# copy mfql to dist
mfqlDir = "mfql/"
if os.path.isdir("dist/mfql/"):
    shutil.rmtree("dist/mfql/")

shutil.copytree(mfqlDir, "dist/mfql/")

block_cipher = None


a = Analysis(['LipidXplorer.py'],
             pathex=['C:\\Users\\nils.hoffmann\\PycharmProjects\\gitlab.isas.de\\lipidxplorer'],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries + [('msvcp100.dll', 'C:\\Windows\\System32\\msvcp100.dll', 'BINARY'),
                        ('msvcr100.dll', 'C:\\Windows\\System32\\msvcr100.dll', 'BINARY')]
          if sys.platform == 'win32' else a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='LipidXplorer',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          icon='lx/stuff/lipidx_tb.ico',
          console=False )
