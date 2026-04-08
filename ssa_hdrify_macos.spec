# -*- mode: python ; coding: utf-8 -*-
import os
import platform

OS_TYPE = platform.system()

app_version = os.environ.get("APP_VERSION", "0.0.1")

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/asset/*', "asset")],
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(SPECPATH, 'hdr.icns')],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ssa_hdrify',
)
app = BUNDLE(
    coll,
    name='ssa hdrify.app',
    icon=os.path.join(SPECPATH, 'hdr.icns'),
    bundle_identifier='com.gky99.ssa-hdrify',
    version=app_version
)
