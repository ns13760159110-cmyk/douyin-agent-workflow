#!/usr/bin/env python3.12
import json
import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse

HISTORY_FILE = "/home/aoray/抖音智能体工作流/脚本/history.json"
STATIC_DIR = "/home/aoray/抖音智能体工作流/脚本"

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/history":
            history = load_history()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(history, ensure_ascii=False).encode())
        elif self.path == "/api/history/clear":
            save_history([])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        elif self.path.startswith("/api/douyin/parse"):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("url", [""])[0]
            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"success":False,"error":"缺少url参数"}, ensure_ascii=False).encode())
            else:
                result = parse_douyin(url)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
        elif self.path.startswith("/api/douyin/comments"):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("url", [""])[0]
            cursor = int(params.get("cursor", ["0"])[0])
            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"success":False,"error":"缺少url参数"}, ensure_ascii=False).encode())
            else:
                result = get_douyin_comments(url, cursor)
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
        else:
            path = self.path.split("?")[0]
            if path == "/" or path == "":
                path = "/index.html"
            filepath = STATIC_DIR + path
            if os.path.exists(filepath) and os.path.isfile(filepath):
                ext = filepath.split(".")[-1]
                types = {"html":"text/html","js":"application/javascript","json":"application/json","css":"text/css"}
                ct = types.get(ext, "text/plain") + "; charset=utf-8"
                with open(filepath, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_cors()
                self.end_headers()
                self.wfile.write(content)
            else:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        if self.path == "/api/history":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                record = json.loads(body.decode("utf-8"))
                history = load_history()
                record["id"] = len(history) + 1
                record["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                history.insert(0, record)
                if len(history) > 100:
                    history = history[:100]
                save_history(history)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_cors()
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

def parse_douyin(url):
    try:
        result = subprocess.run(
            ["python3.12", os.path.join(os.path.dirname(__file__), "douyin_api.py"), url],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_douyin_comments(url, cursor=0):
    try:
        result = subprocess.run(
            ["python3.12", os.path.join(os.path.dirname(__file__), "douyin_api.py"), "comments", url, str(cursor)],
            capture_output=True, text=True, timeout=30
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = 8088
    print(f"服务启动在 http://0.0.0.0:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
