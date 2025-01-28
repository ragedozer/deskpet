# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Make sure these paths match your actual file locations
added_files = [
    ('goose.json', '.'),
    ('goose.png', '.'),
    ('icon.ico', '.'),
    ('logo.png', '.')
]

a = Analysis(
    ['deskpet.py'],
    pathex=[],
    binaries=[],
    datas=added_files,  # Add the files here
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DeskPet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True temporarily for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    version='version_info.txt'
)
