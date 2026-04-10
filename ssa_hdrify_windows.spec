# -*- mode: python ; coding: utf-8 -*-
import os

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/asset/*', 'asset')],
    hiddenimports=['pysubs2', 'charset_normalizer', 'charset_normalizer.md__mypyc'],
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
    a.zipfiles,
    [],
    name='ssa hdrify',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=os.path.join(SPECPATH, 'hdr.ico'),
)
