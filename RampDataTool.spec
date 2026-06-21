# -*- mode: python ; coding: utf-8 -*-
#
# Reproducible build:  pyinstaller RampDataTool.spec
#
# On macOS this produces dist/RampDataTool.app (plus a dist/RampDataTool/ folder).
# On Windows/Linux it produces a dist/RampDataTool/ folder with the executable.
#
# Bundled here that the bare CLI would miss:
#   - CustomTkinter's theme/asset data files (otherwise CTk crashes on import)
#   - images/ (team logo)

import sys
from PyInstaller.utils.hooks import collect_data_files

datas  = collect_data_files("customtkinter")
datas += [("images", "images")]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RampDataTool",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # windowed app, no terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,       # builds for the host arch (arm64 on your M-series)
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RampDataTool",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="RampDataTool.app",
        icon=None,
        bundle_identifier="com.bulmerobotics.rampdatatool",
        info_plist={
            "NSHighResolutionCapable": True,   # crisp on Retina, no blurry scaling
            "LSApplicationCategoryType": "public.app-category.developer-tools",
        },
    )
