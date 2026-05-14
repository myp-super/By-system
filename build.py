"""
Build script — packages the app into a standalone .exe with PyInstaller.

Usage:
    python build.py           # Build
    python build.py --clean   # Clean + rebuild

Output:
    dist/保研管理.exe  (Windows)
    dist/保研管理      (macOS)
"""
import sys
import shutil
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.resolve()
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
APP_NAME = "保研管理"


def clean():
    """Remove previous build artifacts."""
    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            shutil.rmtree(d)
    for spec in PROJECT_ROOT.glob("*.spec"):
        spec.unlink()
    print("[✓] Build artifacts cleaned.")


def build():
    """Run PyInstaller to create a standalone executable."""
    try:
        from PyInstaller.__main__ import run as pyi_run
    except ImportError:
        print("ERROR: PyInstaller not installed. Run: pip install pyinstaller")
        sys.exit(1)

    main_script = PROJECT_ROOT / "main.py"
    if not main_script.exists():
        print(f"ERROR: {main_script} not found")
        sys.exit(1)

    print(f"[→] Building {APP_NAME} into single executable...")
    print(f"    Script : {main_script}")
    print(f"    Output : {DIST_DIR / APP_NAME}.exe" if sys.platform == "win32"
          else f"    Output : {DIST_DIR / APP_NAME}")

    # Build args with proper path separators
    sep = ";" if sys.platform == "win32" else ":"
    ui_dir = str(PROJECT_ROOT / "ui")

    args = [
        str(main_script),
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--clean",
        "--add-data", f"{ui_dir}{sep}ui",
        "--hidden-import", "sqlalchemy.ext.declarative",
        "--hidden-import", "plyer.platforms.win.notification",
        "--hidden-import", "openpyxl",
        "--hidden-import", "pandas",
        "--hidden-import", "docx",
        "--collect-all", "plyer",
        "--noconfirm",
    ]

    if sys.platform == "win32":
        args.append("--icon=NONE")
    elif sys.platform == "darwin":
        args.append("--icon=NONE")

    pyi_run(args)

    print(f"\n[✓] Build complete!")
    dest = DIST_DIR / (APP_NAME + (".exe" if sys.platform == "win32" else ""))
    if dest.exists():
        print(f"    → {dest}")
    else:
        print(f"    (Check {DIST_DIR} for output)")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    build()
