# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for VGTECH Road Damage Detector (Linux/Jetson)

import sys
from pathlib import Path

block_cipher = None

# Collect data files
datas = [
    ('VERSION', '.'),
    ('.env.example', '.'),
    ('models/*.tflite', 'models'),
]

# Hidden imports for TFLite and Qt
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'numpy',
    'cv2',
    'tflite_runtime',
    'tensorflow.lite',
    'supabase',
    'dotenv',
    'sqlite3',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='road-damage-detector',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='road-damage-detector-linux',
)
