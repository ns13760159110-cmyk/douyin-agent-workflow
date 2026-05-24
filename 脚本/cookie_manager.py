#!/usr/bin/env python3.12
"""Cookie 管理器 — 检查有效期、更新 cookie"""
import re, time, os, json

COOKIE_FILE = os.path.join(os.path.dirname(__file__), "douyin_parse/douyin_cookie.txt")

def get_cookie_info():
    try:
        with open(COOKIE_FILE, "r") as f:
            cookie = f.read().strip()
        # sid_guard 格式: sid_guard=xxx%7C创建时间戳%7C有效期秒数%7C...
        m = re.search(r'sid_guard=[^;]*%7C(\d+)%7C(\d+)', cookie)
        if m:
            created = int(m.group(1))
            duration = int(m.group(2))
            expire_ts = created + duration
        else:
            expire_ts = 0

        now = int(time.time())
        days_left = max(0, (expire_ts - now) // 86400) if expire_ts else -1

        return {
            "valid": len(cookie) > 100,
            "days_left": days_left,
            "expire_date": time.strftime("%Y-%m-%d", time.localtime(expire_ts)) if expire_ts else "未知",
            "warning": 0 < days_left < 7,
            "expired": days_left == 0 and expire_ts > 0,
        }
    except Exception as e:
        return {"valid": False, "days_left": 0, "error": str(e)}


def update_cookie(new_cookie: str) -> dict:
    try:
        new_cookie = new_cookie.strip()
        if len(new_cookie) < 100:
            return {"success": False, "error": "Cookie内容太短，请检查"}
        with open(COOKIE_FILE, "w") as f:
            f.write(new_cookie)
        return {"success": True, "message": "Cookie更新成功"}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print(json.dumps(get_cookie_info(), ensure_ascii=False, indent=2))
