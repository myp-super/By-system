# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\Lenovo\\Desktop\\app\\web\\templates', 'templates'), ('C:\\Users\\Lenovo\\Desktop\\app\\web\\static', 'static'), ('C:\\Users\\Lenovo\\Desktop\\app\\web\\data', 'data')]
binaries = []
hiddenimports = ['sqlalchemy', 'sqlalchemy.ext.declarative', 'flask', 'flask_cors', 'pandas', 'openpyxl', 'waitress', 'jinja2', 'jinja2.ext', 'plyer', 'werkzeug', 'docx', 'urllib3', 'bs4', 'lxml', 'pdfplumber', 'PyPDF2', 'zipfile', 'json', 'uuid']
tmp_ret = collect_all('sqlalchemy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('flask')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('jinja2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\Lenovo\\Desktop\\app\\web\\launcher.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='保研管理',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
