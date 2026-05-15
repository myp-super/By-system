"""
Standalone launcher for packaged .exe
Starts the web server and opens the browser automatically.
"""
import sys, os, threading, webbrowser
from pathlib import Path

# Ensure working directory is correct (PyInstaller sets sys._MEIPASS for bundled data)
if getattr(sys, 'frozen', False):
    os.chdir(Path(sys._MEIPASS))

from app import app

def open_browser():
    webbrowser.open('http://localhost:5000')

def main():
    port = int(os.environ.get('PORT', 5000))

    print("=" * 50)
    print("  保研全程管理 v5 Enterprise")
    print(f"  Server: http://localhost:{port}")
    print("  Press Ctrl+C to stop")
    print("=" * 50)

    # Open browser after a short delay
    threading.Timer(1.5, open_browser).start()

    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=port, threads=4)
    except ImportError:
        app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
