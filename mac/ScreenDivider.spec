# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['screen_divider_mac.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    name='ScreenDivider',
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
)
app = BUNDLE(
    exe,
    name='ScreenDivider.app',
    icon='temp_icon.png',
    bundle_identifier='com.screendivider.app',
    info_plist={
        'CFBundleDisplayName': 'ScreenDivider',
        'CFBundleIdentifier': 'com.screendivider.app',
        'CFBundleName': 'ScreenDivider',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
        'LSMinimumSystemVersion': '10.13.0',
        'NSHighResolutionCapable': True,
        'NSSupportsAutomaticGraphicsSwitching': True,
        'NSAppleEventsUsageDescription': 'This app needs to control other applications to provide screen splitting functionality.',
        'NSScreenCaptureDescription': 'This app needs screen recording permission to capture and display screen content for the split screen feature.',
        'NSSystemAdministrationUsageDescription': 'This app needs system administration access to manage screen capture and window positioning.',
        'NSDesktopFolderUsageDescription': 'This app may need to access desktop content for screen capture functionality.',
        'NSDocumentsFolderUsageDescription': 'This app may need to save configuration files.',
        'com.apple.security.automation.apple-events': True,
    },
)
