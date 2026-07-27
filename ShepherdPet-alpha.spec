# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['ShepherdPetAlpha\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\86132\\Documents\\Codex\\2026-07-21\\hatch-pet-c-users-86132-codex\\outputs\\alpha-shepherd\\ShepherdPetAlpha\\assets', 'assets')],
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
    [],
    name='ShepherdPet-alpha',
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
    icon=['C:\\Users\\86132\\Documents\\Codex\\2026-07-21\\hatch-pet-c-users-86132-codex\\outputs\\alpha-shepherd\\ShepherdPetAlpha\\assets\\app.ico'],
)
