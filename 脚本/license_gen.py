#!/usr/bin/env python3.12
import requests
import random
import string
import json
import sys
import time
APP_ID = "cli_aa8c36d48a7b5bd1"
APP_SECRET = "cfucsDjzMw0k5RL1zH62ccUefWPSvjCm"
APP_TOKEN = "G6GVwerePiRBQ8k07QgcMJRXnzb"
TABLE_ID = "tblwCg1OlEvl4jS4"
def get_token():
    res = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET}
    )
    return res.json().get("tenant_access_token", "")
def gen_code(prefix="CMYK"):
    """生成激活码，格式：CMYK-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    parts = [''.join(random.choices(chars, k=4)) for _ in range(3)]
    return f"{prefix}-{'-'.join(parts)}"
def create_license(plan="标准版", days=30, max_use=999, channel="", remark="", count=1):
    """批量创建激活码"""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    expire_ts = int((time.time() + days * 86400) * 1000)
    codes = []
    for _ in range(count):
        code = gen_code()
        res = requests.post(
            f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records",
            headers=headers,
            json={
                "fields": {
                    "激活码": code,
                    "状态": "未激活",
                    "套餐": plan,
                    "到期时间": expire_ts,
                    "最大使用次数": max_use,
                    "已使用次数": 0,
                    "渠道": channel,
                    "备注": remark
                }
            }
        )
        result = res.json()
        if result.get("code") == 0:
            codes.append(code)
            print(f"✅ 生成成功：{code}")
        else:
            print(f"❌ 生成失败：{result}")
    return codes
def get_stats():
    """获取激活码统计"""
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records",
        headers=headers, params={"page_size": 500}
    )
    items = res.json().get("data", {}).get("items", [])
    total = len(items)
    active = sum(1 for i in items if i.get("fields", {}).get("状态") == "使用中")
    unused = sum(1 for i in items if i.get("fields", {}).get("状态") == "未激活")
    expired = sum(1 for i in items if i.get("fields", {}).get("状态") == "已过期")
    return {"total": total, "active": active, "unused": unused, "expired": expired}
def get_records():
    """获取所有激活码记录"""
    import datetime
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.get(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records",
        headers=headers, params={"page_size": 100}
    )
    items = res.json().get("data", {}).get("items", [])
    records = []
    for item in items:
        f = item.get("fields", {})
        expire_ts = f.get("到期时间", 0)
        expire_str = ""
        if expire_ts:
            try:
                ts = int(expire_ts) / 1000 if len(str(int(expire_ts))) > 10 else int(expire_ts)
                expire_str = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except:
                pass
        records.append({
            "激活码": f.get("激活码", ""),
            "状态": f.get("状态", ""),
            "套餐": f.get("套餐", ""),
            "到期时间": expire_str or f.get("到期时间"),
            "最大使用次数": f.get("最大使用次数", ""),
            "已使用次数": f.get("已使用次数", ""),
            "绑定设备": f.get("绑定设备", ""),
            "使用者": f.get("使用者", ""),
            "渠道": f.get("渠道", ""),
            "备注": f.get("备注", "")
        })
    return records
if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    plan = sys.argv[3] if len(sys.argv) > 3 else "标准版"
    channel = sys.argv[4] if len(sys.argv) > 4 else ""
    print(f"生成{count}个激活码，有效期{days}天，套餐：{plan}")
    codes = create_license(plan=plan, days=days, count=count, channel=channel)
    print(f"\n生成完成，共{len(codes)}个：")
    for c in codes:
        print(c)
