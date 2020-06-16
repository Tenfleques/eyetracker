# -*- mode: python ; coding: utf-8 -*-
from kivy_deps import sdl2, glew
block_cipher = None


a = Analysis(['main.py'],
             pathex=['C:\\Users\\tendai\\source\\repos\\eyetracker\\gis-eyetracker'],
             binaries=[],
             datas=[],
             hiddenimports=['kivy.core.spelling_enchant', 'kivy.graphics',
                                         'kivy.graphics.compiler','pkg_resources.py2_warn', 'kivy.graphics.vertex',
                                         'win32file','win32timezone'],
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
          [],
          exclude_binaries=True,
          name='gis-eye-tracker-mipt',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False, icon='assets\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               *[Tree(p) for p in (sdl2.dep_bins)],
               strip=False,
               upx=True,
               upx_exclude=[],
               name='gis-eye-tracker-mipt')

