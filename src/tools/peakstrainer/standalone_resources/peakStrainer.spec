# -*- mode: python -*-
# used by pyinstaller to create .exe
# C:\apps\Anaconda2) C:\apps\eclipseRCP\workspace\PeakStrainer>
# pyinstaller peakStrainer.spec
block_cipher = None


a = Analysis(['peakStrainerApp.py'],
             pathex=['C:\\apps\\eclipseRCP\\workspace\\PeakStrainer'],
             binaries=[],
             datas=[('utils\\template.mzXML','utils')],
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
          name='peakStrainer',
          debug=False,
          strip=False,
          upx=False,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='peakStrainer')
