"""
Production server entry point — keeps running 24/7.
Usage: python run.py

Place a shortcut to this file in Windows Startup folder for auto-start on boot:
  Win+R → shell:startup → 创建快捷方式指向此文件
"""
import sys, os
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    try:
        from waitress import serve
        print("=" * 50)
        print("  保研全程管理 — 生产模式 (waitress)")
        print(f"  http://localhost:{port}")
        print("  按 Ctrl+C 停止")
        print("=" * 50)
        serve(app, host='0.0.0.0', port=port, threads=4)
    except ImportError:
        print("waitress not installed, using Flask dev server")
        app.run(host='0.0.0.0', port=port, debug=False)
