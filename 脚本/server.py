#!/usr/bin/env python3.12
import json
import os
import subprocess
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse

from monitor_manager import add_video, remove_video, refresh_video, refresh_all, get_all
import sys
sys.path.insert(0, os.path.dirname(__file__))
import bgm_mixer
import auto_create

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
        elif self.path == "/api/monitor/list":
            data = get_all()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
        elif self.path == "/api/monitor/refresh_all":
            result = refresh_all()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
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
        elif self.path.startswith("/api/douyin/download"):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("url", [""])[0]
            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": "缺少url参数"}, ensure_ascii=False).encode())
            else:
                import hashlib, requests
                try:
                    # 解析视频获取无水印链接
                    parse_result = parse_douyin(url)
                    if not parse_result.get("success"):
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.send_cors()
                        self.end_headers()
                        self.wfile.write(json.dumps(parse_result, ensure_ascii=False).encode())
                        return
                    video_url = parse_result.get("video_url", "")
                    if not video_url:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json; charset=utf-8")
                        self.send_cors()
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": False, "error": "无法获取视频下载链接"}, ensure_ascii=False).encode())
                        return
                    # 下载视频
                    vid = hashlib.md5(video_url.encode()).hexdigest()[:8]
                    local_path = f"/tmp/douyin_{vid}.mp4"
                    r = requests.get(video_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.douyin.com/"}, timeout=60)
                    with open(local_path, "wb") as f:
                        f.write(r.content)
                    size = os.path.getsize(local_path)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True, "video_path": local_path, "size": size, "desc": parse_result.get("desc", ""), "author": parse_result.get("author", "")}, ensure_ascii=False).encode())
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False).encode())
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
        elif self.path == "/api/bgm/list":
            data = bgm_mixer.list_bgm()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
        else:
            path = self.path.split("?")[0]
            if path == "/" or path == "":
                path = "/index.html"
            # /tmp_video 路由
            if path.startswith("/tmp_video"):
                parsed = urllib.parse.urlparse(self.path)
                params = urllib.parse.parse_qs(parsed.query)
                video_path = params.get("path", [""])[0]
                if video_path and os.path.exists(video_path):
                    with open(video_path, "rb") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Length", str(len(content)))
                    self.send_cors()
                    self.end_headers()
                    self.wfile.write(content)
                else:
                    self.send_response(404)
                    self.end_headers()
                return
            # 优先检查 /tmp 下的文件（封面图片、音频等）
            if path.startswith("/tmp/") and os.path.exists(path) and os.path.isfile(path):
                ext = path.split(".")[-1]
                types = {"jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","mp3":"audio/mpeg","mp4":"video/mp4","srt":"text/plain"}
                ct = types.get(ext, "application/octet-stream")
                with open(path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_cors()
                self.end_headers()
                self.wfile.write(content)
                return
            filepath = STATIC_DIR + path
            if os.path.exists(filepath) and os.path.isfile(filepath):
                ext = filepath.split(".")[-1]
                types = {"html":"text/html","js":"application/javascript","json":"application/json","css":"text/css","jpg":"image/jpeg","jpeg":"image/jpeg","png":"image/png","mp3":"audio/mpeg","mp4":"video/mp4"}
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
        if self.path == "/api/monitor/add":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            result = add_video(body.get("url", ""), body.get("title", ""))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
        elif self.path == "/api/monitor/remove":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            result = remove_video(int(body.get("id", 0)))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
        elif self.path == "/api/monitor/refresh":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            result = refresh_video(int(body.get("id", 0)))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
        elif self.path == "/api/tts":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            text = body.get("text", "")
            voice = body.get("voice", "晓晓（女，温柔）")
            speed = body.get("speed", "+0%")
            if text:
                result = tts_generator.run(text, voice, output_path=f"/tmp/tts_{hash(text) & 0xFFFF}.mp3")
                self.send_response(200)
                self.send_header("Content-Type", "application/json;charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
            else:
                self.send_response(400)
                self.end_headers()
        elif self.path == "/api/auto_create":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            url = body.get("url", "")
            voice = body.get("voice", "晓晓（女，温柔）")
            bgm = body.get("bgm", "轻快活泼")
            bgm_vol = float(body.get("bgm_vol", 0.15))
            result = auto_create.run_pipeline(url, voice, bgm, bgm_vol)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
        elif self.path == "/api/bgm/mix":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            voice_path = body.get("voice_path", "")
            bgm_path = body.get("bgm_path", "")
            output_path = body.get("output_path", "/tmp/mixed_output.mp3")
            bgm_vol = float(body.get("bgm_vol", 0.1))
            result = bgm_mixer.mix_audio(voice_path, bgm_path, output_path, bgm_vol=bgm_vol)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
        elif self.path == "/api/cover":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            video_path = body.get("video_path", "")
            if video_path and os.path.exists(video_path):
                result = cover_extractor.extract_cover(video_path)
                self.send_response(200)
                self.send_header("Content-Type", "application/json;charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
            else:
                self.send_response(400)
                self.end_headers()
        elif self.path == "/api/subtitle":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            video_path = body.get("video_path", "")
            if video_path and os.path.exists(video_path):
                import subtitle_generator
                result = subtitle_generator.process(video_path)
                self.send_response(200)
                self.send_header("Content-Type", "application/json;charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode())
            else:
                self.send_response(400)
                self.end_headers()
        elif self.path == "/api/merge":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length).decode())
            video_path = body.get("video_path", "")
            audio_path = body.get("audio_path", "")
            output_path = f"/tmp/merged_{hash(video_path+audio_path) & 0xFFFF}.mp4"
            try:
                final = auto_create.combine_video(video_path, audio_path, output_path)
                size = os.path.getsize(final)
                self.send_response(200)
                self.send_header("Content-Type", "application/json;charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"success":True, "path":final, "video_url":"/tmp_video?path="+urllib.parse.quote(final), "size":size}, ensure_ascii=False).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json;charset=utf-8")
                self.send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"success":False, "error":str(e)}, ensure_ascii=False).encode())
        elif self.path == "/api/history":
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

# 自动刷新线程：每小时采集一次所有监控视频的数据
def _auto_refresh_loop():
    while True:
        time.sleep(3600)
        try:
            result = refresh_all()
            print(f"[监控] 自动刷新完成: {result}")
        except Exception as e:
            print(f"[监控] 自动刷新失败: {e}")

threading.Thread(target=_auto_refresh_loop, daemon=True).start()

# ===== 封面提取接口 =====
import cover_extractor

# ===== TTS 接口 =====
import tts_generator

# ===== 字幕生成接口 =====
def handle_subtitle(self, video_path):
    import subtitle_generator
    result = subtitle_generator.process(video_path)
    self.send_response(200)
    self.send_header("Content-Type","application/json;charset=utf-8")
    self.send_cors()
    self.end_headers()
    self.wfile.write(json.dumps(result,ensure_ascii=False).encode())

if __name__ == "__main__":
    port = 8088
    print(f"服务启动在 http://0.0.0.0:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
