"""
Build script for packaging the application with PyInstaller.
Run this script to generate a standalone executable.

Usage:
    python build.py          # Build for current platform
    python build.py --clean  # Clean build (remove build/dist first)

Output:
    dist/保研管理.exe   (Windows)
    dist/保研管理       (macOS/Linux)
"""
import sys
import shutil
from pathlib import Path

# Fix Unicode output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_FILE = PROJECT_ROOT / "保研管理.spec"
APP_NAME = "保研管理"


def clean():
    """Remove previous build artifacts."""
    for d in (DIST_DIR, BUILD_DIR):
        if d.exists():
            shutil.rmtree(d)
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()
    print("[✓] Cleaned build artifacts.")


def build():
    """Run PyInstaller to create standalone executable."""
    try:
        import PyInstaller.__main__ as pyi
    except ImportError:
        print("请先安装 PyInstaller: pip install pyinstaller")
        sys.exit(1)

    # Determine entry point
    main_script = PROJECT_ROOT / "main.py"
    if not main_script.exists():
        print(f"错误: 找不到入口文件 {main_script}")
        sys.exit(1)

    # Common PyInstaller arguments
    args = [
        str(main_script),
        "--name", APP_NAME,
        "--onefile",                # Single executable
        "--windowed",               # No console window (GUI app)
        "--clean",
        "--add-data", f"{PROJECT_ROOT / 'ui'}{';' if sys.platform == 'win32' else ':'}ui",
        "--hidden-import", "sqlalchemy.ext.declarative",
        "--hidden-import", "plyer.platforms.win.notification",
        "--hidden-import", "openpyxl",
        "--hidden-import", "pandas",
        "--collect-all", "plyer",
    ]

    # Platform-specific settings
    if sys.platform == "win32":
        args.append("--icon=NONE")  # Replace with .ico path if you have one
    elif sys.platform == "darwin":
        args.append("--icon=NONE")  # Replace with .icns path if you have one

    print(f"[→] Building {APP_NAME} as single executable...")
    print(f"    Entry: {main_script}")
    print(f"    Output: {DIST_DIR / APP_NAME}")

    pyi.run(args)

    print(f"\n[✓] Build complete!")
    print(f"    Executable: {DIST_DIR / APP_NAME}.exe" if sys.platform == "win32"
          else f"    Executable: {DIST_DIR / APP_NAME}")
    print(f"    Data: {DIST_DIR}")


if __name__ == "__main__":
    if "--clean" in sys.argv:
        clean()
    build()
