#!/usr/bin/env python3.12
"""抖音链接解析 API 封装 —— 供 server.py 调用"""
import sys, os, json

# 确保能从 douyin_parse 子目录导入，且 cookie 路径正确
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(SCRIPT_DIR, "douyin_parse"))
os.chdir(os.path.join(SCRIPT_DIR, "douyin_parse"))  # cookie.txt 在 CWD 查找

from douyin_video_parser import DouyinVideoParser


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
            "desc": result.get("desc", ""),          # 视频文案
            "author": result.get("author_nickname", ""),
            "author_sec_uid": result.get("author_sec_uid", ""),
            "cover_url": result.get("cover_url", ""),
            "create_time": result.get("create_time", 0),
            "content_type": result.get("content_type", "video"),
            "video_url": result.get("nwm_url", ""),  # 无水印链接
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "请提供抖音链接"}, ensure_ascii=False))
        sys.exit(1)

    url = sys.argv[1]
    result = parse(url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
