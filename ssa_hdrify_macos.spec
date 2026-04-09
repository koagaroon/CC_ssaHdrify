# -*- mode: python ; coding: utf-8 -*-
import os

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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[os.path.join(SPECPATH, 'hdr.icns')],
)
app = BUNDLE(
    exe,
    name='ssa hdrify.app',
    icon=os.path.join(SPECPATH, 'hdr.icns'),
    bundle_identifier='com.gky99.ssa-hdrify',
    version=app_version
)
