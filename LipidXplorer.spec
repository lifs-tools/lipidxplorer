# -*- mode: python -*-

block_cipher = None


a = Analysis(['LipidXplorer.py'],
             pathex=['D:\\tmp\\LipidXplorer-1.2.7'],
             binaries=[],
             datas=[('lx\\stuff\*','lx\\stuff')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='LipidXplorer',
          debug=False,
          strip=False,
          upx=False,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='LipidXplorer')
