# -*- mode: python -*-
import os, sys, shutil
from zipfile import ZipFile
import subprocess
import six

label = subprocess.check_output(["git", "describe", "--always"]).strip().decode()
with open("CHANGELOG", "a") as myfile:
    myfile.write("git hash of this build: "+label)

# copy assets to dist
assetsDir = "src/lx/stuff/"
if os.path.isdir(DISTPATH+"/src/lx/"):
    shutil.rmtree(DISTPATH+"/src/lx/")

shutil.copytree(assetsDir, DISTPATH+"/src/lx/stuff/")

shutil.copy("README.md", DISTPATH+"/")
shutil.copy("CHANGELOG", DISTPATH+"/")
shutil.copy("COPYRIGHT.txt", DISTPATH+"/")
shutil.copy("LICENSES-third-party.txt", DISTPATH+"/")
shutil.copy("settings/lpdxImportSettings_benchmark.ini", DISTPATH+"/")
shutil.copy("settings/lpdxImportSettings_tutorial.ini", DISTPATH+"/")
shutil.copy("settings/lpdxopts.ini", DISTPATH+"/")
shutil.copy("ReleaseNotes.docx", DISTPATH+"/")

block_cipher = None


a = Analysis(['LipidXplorer.py'],
             pathex=[],
             datas=[
                 ('..\\venv\\Lib\\site-packages\\ms_deisotope\\data_source\\_vendor\\ThermoRawFileReader_3_0_41\\Libraries\\*.dll', 'ms_deisotope\\data_source\\_vendor\\ThermoRawFileReader_3_0_41\\Libraries'),
                 ('tools\\peakStrainer\\utils\\template.mzXML', 'tools\\peakStrainer\\utils'),
                 ('lx\\mfql\\mfqlParser.py', 'lx\\mfql'),
                 ('..\\venv\\Lib\\site-packages\\scipy.libs\*.dll', '.'),
                 ('..\\venv\\Lib\\site-packages\\ms_deisotope', 'ms_deisotope'),
                 ('..\\venv\\Lib\\site-packages\\ms_peak_picker', 'ms_peak_picker'),
                 ('..\\venv\\Lib\\site-packages\\brainpy', 'brainpy'),
             ] if sys.platform == 'win32' else [],
             hiddenimports=['pkg_resources.py2_warn', 'dependency_injector.errors', 'scipy.spatial.transform._rotation_groups', 'six'],
             binaries=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['tornado', 'pandoc', 'notebook', 'jedi', 'nbconvert', 'nbformat', 'ms_deisotope', 'ms_peak_picker', 'brainpy'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries + [('msvcp100.dll', 'msvcp100.dll', 'BINARY'),
                        ('msvcr100.dll', 'msvcr100.dll', 'BINARY')]
          if sys.platform == 'win32' else a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='LipidXplorer',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          icon='lx/stuff/lipidx_tb.ico',
          console=False )

with ZipFile(DISTPATH+'.zip', 'w') as zipObj:
   # Iterate over all the files in DISTPATH
   for folderName, subfolders, filenames in os.walk(DISTPATH):
       for filename in filenames:
           #create complete filepath of file in directory
           filePath = os.path.join(folderName, filename)
           # Add file to zip
           zipObj.write(filePath)
