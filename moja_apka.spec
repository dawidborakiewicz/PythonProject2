# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules
a = Analysis(
    ['main.py'],
    pathex=[r'D:\Documents\pycharmprojects\PythonProject2'],
    binaries=[],
    datas=[
        # ('path\to\file.ext', 'dest_folder_inside_exe'),
        # przykładowo:
        # (r'D:\Documents\pycharmprojects\PythonProject2\config\*.json', 'config'),
        (r'D:\Documents\pycharmprojects\PythonProject2\sky\*.png', 'sky'), # wszystkie pliki .png w katalogu sky
        (r'D:\Documents\pycharmprojects\PythonProject2\*.npy', '.'),  # wszystkie pliki .npy w głównym katalogu
        (r'D:\Documents\pycharmprojects\PythonProject2\*.png','.') # wszystkie pliki .png w głównym katalogu
    ],
    # wszystkie dynamiczne i brakujące importy:
    hiddenimports=collect_submodules('OpenGL') +[
        'pyglm.glm',
        'OpenGL.arrays',
        'pyglm',
        'OpenGL',
        'OpenGL.GL',
        'OpenGL.GLU',
        'pyglm',
        'pkg_resources',     # przydatne, jeśli korzystasz z entry_points lub setuptools
        # dopisz tu inne moduły ładowane dynamicznie, np. z importlib
    ],
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
    name='moja_apka',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
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
    name='moja_apka',
)
