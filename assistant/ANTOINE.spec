# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['antoine_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('antoine.py', '.'),
    ],
    hiddenimports=[
        'speech_recognition', 'pygame', 'edge_tts',
        'groq', 'anthropic', 'google.genai',
        'pyaudio', 'pyttsx3', 'psutil', 'PIL', 'dotenv',
        'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtCore', 'PyQt6.QtGui',
        'pycaw', 'pycaw.pycaw', 'comtypes', 'comtypes.client',
        'tkinter',
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
    name='ANTOINE',
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
    icon=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ANTOINE',
)
