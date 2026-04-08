# -*- mode: python ; coding: utf-8 -*-
import os

app_version = os.environ.get("APP_VERSION", "0.0.1")

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/asset/*', 'asset')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='ssa hdrify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=os.path.join(SPECPATH, 'hdr.ico'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ssa_hdrify',
)
