"""
桌面应用启动器 —— 原生窗口，无需浏览器
双击 app.py 或运行 python app.py 即可启动
需要先安装: pip install pywebview
"""

import sys
import threading
import time
from pathlib import Path

import webview

sys.path.insert(0, str(Path(__file__).parent))
from web.server import app as flask_app

HOST = "127.0.0.1"
PORT = 15000
URL = f"http://{HOST}:{PORT}"


def start_server():
    """在后台线程启动 Flask 服务"""
    flask_app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    window = webview.create_window(
        title="网文动态大纲",
        url=URL,
        width=1300,
        height=850,
        min_size=(900, 600),
        resizable=True,
        text_select=True,
    )
    webview.start(debug=False)
    print("应用已退出。")


if __name__ == "__main__":
    main()
