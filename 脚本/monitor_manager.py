#!/usr/bin/env python3.12
"""视频数据监控管理器 — 定期采集统计、历史追踪"""
import json, os, sys, time
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "douyin_parse"))
os.chdir(os.path.join(SCRIPT_DIR, "douyin_parse"))

from douyin_video_parser import DouyinVideoParser

MONITOR_FILE = os.path.join(SCRIPT_DIR, "monitor.json")


def load_monitor():
    try:
        with open(MONITOR_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def save_monitor(data):
    with open(MONITOR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_stats(url: str) -> dict:
    """获取单条视频的统计数据"""
    parser = DouyinVideoParser()
    video_id = parser.get_video_id(url)
    if not video_id:
        return {}
    detail = parser.get_aweme_detail(video_id)
    if not detail:
        return {}
    s = (detail.get("aweme_detail") or {}).get("statistics") or {}
    return {
        "likes": s.get("digg_count", 0),
        "comments": s.get("comment_count", 0),
        "shares": s.get("share_count", 0),
        "collects": s.get("collect_count", 0),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ts": int(time.time())
    }


def add_video(url: str, title: str = "") -> dict:
    monitor = load_monitor()
    for v in monitor:
        if v["url"] == url:
            return {"success": False, "error": "该视频已在监控列表"}
    monitor.append({
        "id": len(monitor) + 1,
        "url": url,
        "title": title,
        "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "history": []
    })
    save_monitor(monitor)
    return {"success": True, "message": "添加成功"}


def remove_video(video_id: int) -> dict:
    monitor = load_monitor()
    monitor = [v for v in monitor if v["id"] != video_id]
    save_monitor(monitor)
    return {"success": True}


def refresh_video(video_id: int) -> dict:
    monitor = load_monitor()
    for v in monitor:
        if v["id"] == video_id:
            stats = fetch_stats(v["url"])
            v["history"].append(stats)
            if len(v["history"]) > 30:
                v["history"] = v["history"][-30:]
            v["latest"] = stats
            save_monitor(monitor)
            return {"success": True, "stats": stats}
    return {"success": False, "error": "视频不存在"}


def refresh_all() -> dict:
    monitor = load_monitor()
    results = []
    for v in monitor:
        try:
            stats = fetch_stats(v["url"])
            v["history"].append(stats)
            if len(v["history"]) > 30:
                v["history"] = v["history"][-30:]
            v["latest"] = stats
            results.append({"id": v["id"], "title": v["title"], "success": True})
        except Exception as e:
            results.append({"id": v["id"], "title": v["title"], "success": False, "error": str(e)})
    save_monitor(monitor)
    return {"success": True, "results": results}


def get_all() -> list:
    return load_monitor()


if __name__ == "__main__":
    print(json.dumps(get_all(), ensure_ascii=False, indent=2))
