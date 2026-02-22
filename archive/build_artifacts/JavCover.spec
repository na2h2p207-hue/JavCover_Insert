# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['c:\\Users\\jerom\\Desktop\\mosaic\\label\\JavCover_WebView.py'],
    pathex=['c:\\Users\\jerom\\Desktop\\mosaic\\label\\rename'],
    binaries=[],
    datas=[
        ('c:\\Users\\jerom\\Desktop\\mosaic\\label\\archive\\icon.ico', '.'),
        ('c:\\Users\\jerom\\Desktop\\mosaic\\label\\gui', 'gui'),
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
    icon=['c:\\Users\\jerom\\Desktop\\mosaic\\label\\archive\\icon.ico'],
)
