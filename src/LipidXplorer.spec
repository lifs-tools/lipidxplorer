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

# only for python 3.8
# ('..\\venv\\Lib\\site-packages\\scipy.libs\\*.dll', '.'),

a = Analysis(['LipidXplorer.py'],
             pathex=[],
             datas=[
                 ('tools\\peakStrainer\\utils\\template.mzXML', 'tools\\peakStrainer\\utils'),
                 ('lx\\mfql\\mfqlParser.py', 'lx\\mfql'),
                 ('..\\venv\\Lib\\site-packages\\fisher_py\\dll', 'fisher_py\\dll'),
                 ('..\\venv\\Lib\\site-packages\\ms_deisotope\\_c', 'ms_deisotope\\_c'),
                 ('..\\venv\\Lib\\site-packages\\ms_peak_picker\\_c', 'ms_peak_picker\\_c'),
                 ('..\\venv\\Lib\\site-packages\\brainpy\\_c', 'brainpy\\_c'),
             ] if sys.platform == 'win32' else [],
             hiddenimports=['pkg_resources.py2_warn', 'dependency_injector.errors', 'scipy.spatial.transform._rotation_groups', 'six'],
             binaries=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=['tornado', 'pandoc', 'notebook', 'jedi', 'nbconvert', 'nbformat'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

# Remove duplicates
for b in a.binaries.copy():  # Traver the binaries.
    for d in a.datas:  #  Traverse the datas.
        if b[1].endswith(d[0]):  # If duplicate found.
            a.binaries.remove(b)  # Remove the duplicate.
            break

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
          debug=True,
          bootloader_ignore_signals=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          icon='lx/stuff/lipidx_tb.ico',
          console=True )

with ZipFile(DISTPATH+'.zip', 'w') as zipObj:
   # Iterate over all the files in DISTPATH
   for folderName, subfolders, filenames in os.walk(DISTPATH):
       for filename in filenames:
           #create complete filepath of file in directory
           filePath = os.path.join(folderName, filename)
           # Add file to zip
           zipObj.write(filePath)
