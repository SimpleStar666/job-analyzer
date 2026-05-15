import os
import sys
import webbrowser
import threading
import time

print("=" * 50)
print("    JobAnalyzer - Starting...")
print("=" * 50)
print()

# 添加当前目录和web目录到路径
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, "web"))

try:
    import requests
    import flask
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "flask", "rich"])

print("Starting web server...")
print()

def open_browser():
    time.sleep(2)
    print("Opening browser...")
    webbrowser.open("http://localhost:5000")

# 启动浏览器
threading.Thread(target=open_browser, daemon=True).start()

print("Server starting...")
print("Your browser should open automatically.")
print("If not, visit: http://localhost:5000")
print()
print("Press Ctrl+C to stop")
print()

# 直接导入并运行Flask应用
os.chdir(base_dir)
from web.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
