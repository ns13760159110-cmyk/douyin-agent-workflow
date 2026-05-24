#!/usr/bin/env python3.12
"""抖音链接解析 API 封装 —— 供 server.py 调用"""
import sys, os, json, requests
from urllib.parse import quote

# 确保能从 douyin_parse 子目录导入，且 cookie 路径正确
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "douyin_parse"))
os.chdir(os.path.join(SCRIPT_DIR, "douyin_parse"))  # cookie.txt 在 CWD 查找

from douyin_video_parser import DouyinVideoParser, ABogus


def parse(url: str) -> dict:
    """
    解析抖音分享链接，返回视频信息。
    支持: v.douyin.com/xxx, www.douyin.com/video/xxx, 纯视频ID
    """
    try:
        parser = DouyinVideoParser()
        result = parser.parse_video(url)
        if not result:
            return {"success": False, "error": "解析失败，视频可能已删除或链接无效"}

        return {
            "success": True,
            "aweme_id": result.get("aweme_id", ""),
            "desc": result.get("desc", ""),
            "author": result.get("author_nickname", ""),
            "author_sec_uid": result.get("author_sec_uid", ""),
            "cover_url": result.get("cover_url", ""),
            "create_time": result.get("create_time", 0),
            "content_type": result.get("content_type", "video"),
            "video_url": result.get("nwm_url", ""),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_comments(url: str, cursor: int = 0, count: int = 20) -> dict:
    """获取视频评论"""
    try:
        parser = DouyinVideoParser()
        video_id = parser.get_video_id(url)
        if not video_id:
            return {"success": False, "error": "无法获取视频ID"}

        # 直接调用评论 API（DouyinVideoParser 没有 get_comments 方法）
        params = {
            "device_platform": "webapp", "aid": "6383", "channel": "channel_pc_web",
            "aweme_id": video_id, "cursor": str(cursor), "count": str(count),
            "pc_client_type": "1", "version_code": "290100", "version_name": "29.1.0",
            "cookie_enabled": "true", "browser_language": "zh-CN",
            "browser_platform": "Win32", "browser_name": "Chrome",
            "browser_version": "130.0.0.0", "browser_online": "true",
            "engine_name": "Blink", "engine_version": "130.0.0.0",
            "os_name": "Windows", "os_version": "10", "platform": "PC", "msToken": ""
        }

        a_bogus = ABogus().get_value(params)
        params["a_bogus"] = quote(a_bogus, safe="")

        headers = {
            "User-Agent": parser.user_agent,
            "Cookie": parser.cookie,
            "Referer": f"https://www.douyin.com/video/{video_id}",
        }

        resp = requests.get(
            "https://www.douyin.com/aweme/v1/web/comment/list/",
            params=params, headers=headers, timeout=15
        )
        data = resp.json()
        comments_raw = data.get("comments") or []

        return {
            "success": True,
            "video_id": video_id,
            "total": data.get("total_count", 0),
            "has_more": data.get("has_more", 0) == 1,
            "cursor": data.get("cursor", 0),
            "comments": [
                {
                    "nickname": c.get("user", {}).get("nickname", ""),
                    "text": c.get("text", ""),
                    "likes": c.get("digg_count", 0),
                    "reply": ((c.get("reply_comment") or {}).get("text", "") if isinstance(c.get("reply_comment"), dict) else "")
                }
                for c in comments_raw
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "用法: douyin_api.py <url> 或 douyin_api.py comments <url> [cursor]"}, ensure_ascii=False))
        sys.exit(1)

    if sys.argv[1] == "comments":
        if len(sys.argv) < 3:
            print(json.dumps({"success": False, "error": "缺少url参数"}, ensure_ascii=False))
            sys.exit(1)
        url = sys.argv[2]
        cursor = int(sys.argv[3]) if len(sys.argv) > 3 else 0
        result = get_comments(url, cursor=cursor)
    else:
        url = sys.argv[1]
        result = parse(url)

    print(json.dumps(result, ensure_ascii=False, indent=2))
