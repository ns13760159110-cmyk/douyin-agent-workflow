#!/usr/bin/env python3.12
"""
抖音视频信息抓取脚本 v2
用法: python3.12 抖音抓取.py <视频URL> [cookie字符串]
"""
import sys
import json
import re
import time
import urllib.parse
from playwright.sync_api import sync_playwright, TimeoutError


def extract_video_id(url: str) -> str:
    m = re.search(r'video/(\d+)', url)
    if m:
        return m.group(1)
    return ""


def scrape_douyin(url: str, cookie_str: str = "") -> dict:
    video_id = extract_video_id(url)
    result = {
        "success": False,
        "url": url,
        "video_id": video_id,
        "title": "",
        "desc": "",
        "author": "",
        "author_id": "",
        "likes": "",
        "comments": "",
        "shares": "",
        "collects": "",
        "duration": "",
        "create_time": "",
        "music_title": "",
        "music_author": "",
        "hashtags": [],
        "cover_url": "",
        "video_url": "",
        "error": None,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Linux; Android 12; SM-G9910) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            viewport={"width": 412, "height": 915},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        # 注入 Cookie
        if cookie_str:
            cookies = []
            for item in cookie_str.split("; "):
                if "=" in item:
                    k, v = item.split("=", 1)
                    cookies.append({
                        "name": k.strip(),
                        "value": v.strip(),
                        "domain": ".douyin.com",
                        "path": "/",
                    })
            context.add_cookies(cookies)

        page = context.new_page()

        try:
            # 先访问首页获得 cookie
            page.goto("https://www.douyin.com", wait_until="domcontentloaded", timeout=20000)
            time.sleep(2)

            # 再访问视频页
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            content = page.content()

            # 方法1: 从 RENDER_DATA 提取
            render_match = re.search(
                r'<script[^>]*id="RENDER_DATA"[^>]*>(.*?)</script>',
                content, re.DOTALL
            )
            if render_match:
                try:
                    decoded = urllib.parse.unquote(render_match.group(1).strip())
                    # Douyin RENDER_DATA 是 URL-encoded JSON
                    data = json.loads(decoded)
                    self_data = None

                    # 遍历找到视频数据
                    def walk(obj, depth=0):
                        nonlocal self_data
                        if depth > 20 or self_data:
                            return
                        if isinstance(obj, dict):
                            if "aweme" in obj and "detail" in obj:
                                self_data = obj["aweme"]["detail"]
                                return
                            for v in obj.values():
                                walk(v, depth+1)
                        elif isinstance(obj, list):
                            for item in obj:
                                walk(item, depth+1)

                    walk(data)

                    if self_data:
                        result["desc"] = self_data.get("desc", "")
                        result["create_time"] = str(self_data.get("createTime", ""))
                        result["duration"] = str(self_data.get("duration", ""))
                        result["cover_url"] = (
                            self_data.get("video", {}).get("cover", {}).get("urlList", [""])[0]
                        )

                        author_info = self_data.get("author", {})
                        result["author"] = author_info.get("nickname", "")
                        result["author_id"] = author_info.get("uid", "")

                        stats = self_data.get("statistics", {})
                        result["likes"] = str(stats.get("diggCount", ""))
                        result["comments"] = str(stats.get("commentCount", ""))
                        result["shares"] = str(stats.get("shareCount", ""))
                        result["collects"] = str(stats.get("collectCount", ""))

                        music = self_data.get("music", {})
                        result["music_title"] = music.get("title", "")
                        result["music_author"] = music.get("author", "")

                        text_extra = self_data.get("textExtra", [])
                        result["hashtags"] = [
                            t.get("hashtagName", "") for t in text_extra
                            if t.get("hashtagName")
                        ]

                        play_addr = self_data.get("video", {}).get("playAddr", {})
                        result["video_url"] = (
                            play_addr.get("urlList", [""])[0] if play_addr else ""
                        )

                        result["success"] = True
                        result["title"] = f"{result['author']}: {result['desc'][:50]}"

                except Exception as e:
                    result["error"] = f"RENDER_DATA: {str(e)}"

            # 方法2: 从 __NEXT_DATA__ 提取
            if not result["success"]:
                next_match = re.search(
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    content, re.DOTALL
                )
                if next_match:
                    try:
                        nd = json.loads(next_match.group(1).strip())
                        props = nd.get("props", {}).get("pageProps", {})
                        video_data = props.get("videoData", {}) or props.get("videoInfo", {})
                        if video_data:
                            result["desc"] = video_data.get("desc", "")
                            result["author"] = video_data.get("author", {}).get("nickname", "")
                            result["likes"] = str(video_data.get("diggCount", ""))
                            result["success"] = bool(result["desc"])
                    except:
                        pass

            # 方法3: meta标签
            if not result["desc"]:
                meta = page.query_selector('meta[property="og:description"]')
                if meta:
                    result["desc"] = meta.get_attribute("content") or ""

            result["title"] = page.title()

        except PlaywrightTimeout:
            result["error"] = "超时"
        except Exception as e:
            result["error"] = str(e)
        finally:
            browser.close()

    return result


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.douyin.com/video/7384615836208023818"
    cookie = sys.argv[2] if len(sys.argv) > 2 else ""
    data = scrape_douyin(url, cookie)
    print(json.dumps(data, ensure_ascii=False, indent=2))
