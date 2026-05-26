#!/usr/bin/env python3.12
import requests
import json
import hashlib
import time
import os
# 飞书配置
APP_ID = "cli_aa8c36d48a7b5bd1"
APP_SECRET = "cfucsDjzMw0k5RL1zH62ccUefWPSvjCm"
APP_TOKEN = "G6GVwerePiRBQ8k07QgcMJRXnzb"
TABLE_ID = "tblwCg1OlEvl4jS4"
def get_token() -> str:
    res = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    return res.json().get("tenant_access_token", "")

def get_headers():
    return {"Authorization": f"Bearer {get_token()}", "Content-Type": "application/json"}

def verify_license(code: str, device_id: str = "") -> dict:
    try:
        # 查询激活码
        res = requests.get(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records",
            headers=get_headers(),
            params={"filter": f'CurrentValue.[激活码]="{code}"'}
        )
        data = res.json()
        items = data.get("data", {}).get("items", [])
        if not items:
            return {"valid": False, "error": "激活码不存在"}
        record = items[0]
        fields = record.get("fields", {})
        record_id = record.get("record_id", "")
        # 检查状态
        status = fields.get("状态", "")
        if status == "已禁用":
            return {"valid": False, "error": "激活码已禁用"}
        # 检查到期时间
        expire = fields.get("到期时间", "")
        if expire:
            try:
                expire_ts = int(expire) / 1000 if len(str(expire)) > 10 else int(expire)
                if expire_ts < time.time():
                    return {"valid": False, "error": "激活码已过期"}
            except:
                pass
        # 检查使用次数
        max_use = int(fields.get("最大使用次数", 0) or 0)
        used = int(fields.get("已使用次数", 0) or 0)
        if max_use and used >= max_use:
            return {"valid": False, "error": "激活码使用次数已达上限"}
        # 更新使用记录
        update_data = {
            "fields": {
                "已使用次数": used + 1,
                "最后使用时间": int(time.time() * 1000),
                "状态": "使用中"
            }
        }
        if device_id and not fields.get("绑定设备"):
            update_data["fields"]["绑定设备"] = device_id
        put_res = requests.put(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}",
            headers=get_headers(),
            json=update_data
        )
        if put_res.json().get("code") != 0:
            return {"valid": True, "plan": fields.get("套餐", "标准版"), "expire": expire, "message": "验证成功(更新失败)"}
        return {
            "valid": True,
            "plan": fields.get("套餐", "标准版"),
            "expire": expire,
            "message": "验证成功"
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}

def check_session(code: str) -> dict:
    """轻量验证，不更新使用次数"""
    try:
        res = requests.get(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records",
            headers=get_headers(),
            params={"filter": f'CurrentValue.[激活码]="{code}"'}
        )
        items = res.json().get("data", {}).get("items", [])
        if not items:
            return {"valid": False}
        fields = items[0].get("fields", {})
        status = fields.get("状态", "")
        if status == "已禁用":
            return {"valid": False}
        return {"valid": True, "plan": fields.get("套餐", "标准版")}
    except:
        return {"valid": False}

if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "test"
    print(json.dumps(verify_license(code), ensure_ascii=False, indent=2))
