# -*- mode: python ; coding: utf-8 -*-
# NOTE: Update paths below to match your local project directory before building.
import os
PROJ_DIR = os.path.dirname(os.path.dirname(SPECPATH))  # resolves to project root

a = Analysis(
    [os.path.join(PROJ_DIR, 'JavCover_WebView.py')],
    pathex=[os.path.join(PROJ_DIR, 'rename')],
    binaries=[],
    datas=[
        (os.path.join(SPECPATH, '..', 'icon.ico'), '.'),
        (os.path.join(PROJ_DIR, 'gui'), 'gui'),
    ],
    hiddenimports=['rename_movies', 'manual_fix', 'cloudscraper', 'mutagen', 'PIL', 'webview', 'clr_loader', 'pythonnet'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='JavCover',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(SPECPATH, '..', 'icon.ico')],
)
