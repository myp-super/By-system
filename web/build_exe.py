"""
Build standalone .exe for 保研全程管理 Web App.
Output: dist/保研管理.exe
"""
import sys, os
from pathlib import Path
import shutil

WEB_DIR = Path(__file__).parent.resolve()
DIST_DIR = WEB_DIR / 'dist'

def clean():
    for d in [DIST_DIR, WEB_DIR / 'build']:
        if d.exists(): shutil.rmtree(d)
    for f in WEB_DIR.glob('*.spec'):
        f.unlink()
    print('[Clean] Done')

def build():
    try:
        from PyInstaller.__main__ import run as pyi_run
    except ImportError:
        print('ERROR: pip install pyinstaller')
        sys.exit(1)

    sep = ';' if sys.platform == 'win32' else ':'

    # Data files to bundle
    datas = [
        (str(WEB_DIR / 'templates'), 'templates'),
        (str(WEB_DIR / 'static'), 'static'),
        (str(WEB_DIR / 'data'), 'data'),
    ]

    # Build args
    args = [
        str(WEB_DIR / 'launcher.py'),
        '--name', '保研管理',
        '--onefile',
        '--console',
        '--clean',
        '--noconfirm',
    ]

    for src, dst in datas:
        args += ['--add-data', f'{src}{sep}{dst}']

    # Hidden imports
    for mod in ['sqlalchemy', 'sqlalchemy.ext.declarative', 'flask', 'flask_cors',
                'pandas', 'openpyxl', 'waitress', 'jinja2', 'jinja2.ext',
                'plyer', 'werkzeug', 'docx', 'urllib3', 'bs4', 'lxml',
                'pdfplumber', 'PyPDF2', 'zipfile', 'json', 'uuid']:
        args += ['--hidden-import', mod]

    # Collect all submodules
    args += ['--collect-all', 'sqlalchemy']
    args += ['--collect-all', 'flask']
    args += ['--collect-all', 'jinja2']

    print(f'Building 保研管理.exe...')
    print(f'  Entry: launcher.py')
    print(f'  Data: templates/ static/ data/')

    pyi_run(args)

    exe = DIST_DIR / ('保研管理.exe' if sys.platform == 'win32' else '保研管理')
    if exe.exists():
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f'\n[SUCCESS] {exe}')
        print(f'  Size: {size_mb:.1f} MB')
        print(f'\n  Double-click {exe.name} to start.')
        print(f'  Browser will open automatically to http://localhost:5000')
    else:
        print('\n[ERROR] Build failed — check output above')

if __name__ == '__main__':
    if '--clean' in sys.argv:
        clean()
    build()
