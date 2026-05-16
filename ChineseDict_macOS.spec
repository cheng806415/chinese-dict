# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('PyQt6.QtWidgets')
hiddenimports += collect_submodules('PyQt6.QtCore')
hiddenimports += collect_submodules('PyQt6.QtGui')

excludes = [
    'PyQt6.QtQuick', 'PyQt6.QtQml', 'PyQt6.QtNetwork',
    'PyQt6.QtWebEngine', 'PyQt6.QtWebChannel', 'PyQt6.QtDesigner',
    'PyQt6.QtBluetooth', 'PyQt6.QtMultimedia', 'PyQt6.QtSql',
    'PyQt6.QtXml', 'PyQt6.QtSvg', 'PyQt6.QtTest', 'PyQt6.QtOpenGL',
    'PyQt6.QtSensors', 'PyQt6.QtSerialPort', 'PyQt6.QtPositioning',
    'PyQt6.QtLocation', 'PyQt6.QtNfc', 'PyQt6.QtPdf',
    'PyQt6.QtPdfWidgets', 'PyQt6.QtRemoteObjects',
    'PyQt6.QtDBus', 'PyQt6.QtTextToSpeech', 'PyQt6.QtDataVisualization',
    'PyQt6.QtCharts', 'PyQt6.Qt3D', 'PyQt6.QtQuick3D',
    'PyQt6.QtQuickWidgets', 'PyQt6.QtHelp', 'PyQt6.QtOpenGLWidgets',
    'PyQt6.QtPrintSupport', 'PyQt6.QtSpellChecker', 'PyQt6.QtScxml',
    'PyQt6.QtUiTools', 'PyQt6.QtWebSockets', 'PyQt6.QtXmlPatterns',
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

qt6_bin_excludes = []
for binary in a.binaries:
    name = binary[0].lower()
    skip = any(x in name for x in [
        'qt6quick', 'qt6qml', 'qt6network', 'qt6webengine', 'qt6webchannel',
        'qt6designer', 'qt6bluetooth', 'qt6multimedia', 'qt6sql', 'qt6xml',
        'qt6svg', 'qt6test', 'qt6opengl', 'qt6sensors', 'qt6serialport',
        'qt6positioning', 'qt6location', 'qt6nfc', 'qt6pdf', 'qt6remoteobjects',
        'qt6dbus', 'qt6texttospeech', 'qt6datavisualization',
        'qt6charts', 'qt63d', 'qt6quick3d', 'qt6quickwidgets', 'qt6help',
        'qt6printsupport', 'qt6spellchecker', 'qt6scxml', 'qt6uitools',
        'qt6websockets', 'qt6xmlpatterns', 'qt6shader',
    ])
    if not skip:
        qt6_bin_excludes.append(binary)

a.binaries = qt6_bin_excludes

qt6_data_excludes = []
for data in a.datas:
    name = data[0].lower()
    skip = any(x in name for x in [
        'qml', 'translations', 'qsci',
    ])
    if not skip:
        qt6_data_excludes.append(data)

a.datas = qt6_data_excludes

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
        'LSMinimumSystemVersion': '11.0',
    },
)
