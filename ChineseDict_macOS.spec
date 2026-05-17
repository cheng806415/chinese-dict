# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['sip']
hiddenimports += collect_submodules('PyQt5.QtWidgets')
hiddenimports += collect_submodules('PyQt5.QtCore')
hiddenimports += collect_submodules('PyQt5.QtGui')

excludes = [
    'PyQt6',
    'PyQt5.QtQuick', 'PyQt5.QtQml', 'PyQt5.QtNetwork',
    'PyQt5.QtWebEngine', 'PyQt5.QtWebChannel', 'PyQt5.QtDesigner',
    'PyQt5.QtBluetooth', 'PyQt5.QtMultimedia', 'PyQt5.QtSql',
    'PyQt5.QtXml', 'PyQt5.QtSvg', 'PyQt5.QtTest', 'PyQt5.QtOpenGL',
    'PyQt5.QtSensors', 'PyQt5.QtSerialPort', 'PyQt5.QtPositioning',
    'PyQt5.QtLocation', 'PyQt5.QtNfc',
    'PyQt5.QtDBus', 'PyQt5.QtTextToSpeech',
    'PyQt5.QtHelp', 'PyQt5.QtPrintSupport',
    'PyQt5.QtWebSockets', 'PyQt5.QtXmlPatterns',
    'pygame', 'numpy', 'pandas', 'matplotlib', 'scipy', 'PIL',
    'tkinter', 'unittest', 'xmlrunner', 'pytest',
]

a = Analysis(
    [os.path.join('src', 'main.py')],
    pathex=[],
    binaries=[],
    datas=[(os.path.join('data', 'dictionary.db'), 'data')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=2,
)

qt_bin_excludes = []
for binary in a.binaries:
    name = binary[0].lower()
    skip = any(x in name for x in [
        'qt5quick', 'qt5qml', 'qt5network', 'qt5webengine', 'qt5webchannel',
        'qt5designer', 'qt5bluetooth', 'qt5multimedia', 'qt5sql', 'qt5xml',
        'qt5svg', 'qt5test', 'qt5opengl', 'qt5sensors', 'qt5serialport',
        'qt5positioning', 'qt5location', 'qt5nfc',
        'qt5dbus', 'qt5texttospeech',
        'qt5help', 'qt5printsupport',
        'qt5websockets', 'qt5xmlpatterns',
    ])
    if not skip:
        qt_bin_excludes.append(binary)

a.binaries = qt_bin_excludes

qt_data_excludes = []
for data in a.datas:
    name = data[0].lower()
    skip = any(x in name for x in [
        'qml', 'translations', 'qsci',
    ])
    if not skip:
        qt_data_excludes.append(data)

a.datas = qt_data_excludes

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChineseDict',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    name='ChineseDict',
)

app = BUNDLE(
    coll,
    name='ChineseDict.app',
    icon=None,
    bundle_identifier='com.chinesedict.app',
    info_plist={
        'CFBundleName': 'ChineseDict',
        'CFBundleDisplayName': 'ChineseDict',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13',
    },
)
