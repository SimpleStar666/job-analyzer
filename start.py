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

# 导入依赖，必要时安装
try:
    import requests
    import flask
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "flask", "rich"])

print("Starting web server...")
print()

# 函数：打开浏览器
def open_browser():
    time.sleep(1.5)
    print("Opening browser automatically...")
    webbrowser.open("http://localhost:5000")

# 在后台线程打开浏览器
threading.Thread(target=open_browser, daemon=True).start()

print("Server is starting up!")
print("Your browser will open automatically shortly.")
print("If not, please visit: http://localhost:5000")
print()
print("Press Ctrl+C to stop the server")
print()

# 切换到正确目录并启动Flask
os.chdir(base_dir)
from web.app import app

if __name__ == "__main__":
    # 关闭debug模式，避免重启问题
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
