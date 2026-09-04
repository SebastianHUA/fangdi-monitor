# -*- coding: utf-8 -*-
"""2026-08-20 LPR 查询结果微信批量推送"""
import json
import sys
import time

sys.path.insert(0, r"C:\Users\huaxi\.workbuddy\skills\lpr-query-notifier\scripts")
from wechat_sender import send_to_wechat

CONFIG = r"C:\Users\huaxi\.workbuddy\skills\arcwechat\config\wechat_recipients.json"

MESSAGE = """📊 【LPR利率查询】

✅ 查询成功！

📅 公布日期：2026年8月20日（周四）
🔄 调整情况：与上月持平，无变化

📌 最新LPR利率：
• 1年期LPR：3.0%
• 5年期以上LPR：3.5%

📝 数据来源：中国人民银行
🔗 官方公告：https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/3876551/2026082008353223017/index.html

📂 历史数据查询：
• LPR历史数据完整版：https://docs.qq.com/sheet/DTkVQTWp0UFJqaEdv
• LPR查询日期计划-2026年v2：https://docs.qq.com/doc/DTnJTbWd6bmRtVnh5

---
【来自梦小喵🐱】"""


def main():
    with open(CONFIG, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    targets = [r for r in cfg["recipients"] if r.get("enabled")]
    print(f"启用收件人 {len(targets)} 位\n", flush=True)

    ok, fail = [], []
    for i, r in enumerate(targets, 1):
        # search_key 优先，用于长名称群组的搜索匹配
        key = r.get("search_key") or r["name"]
        print(f"=== [{i}/{len(targets)}] {r['name']} (搜索词: {key}) ===", flush=True)
        try:
            if send_to_wechat(key, MESSAGE):
                ok.append(r["name"])
            else:
                fail.append(r["name"])
        except Exception as e:
            print(f"EXCEPTION: {e}", flush=True)
            fail.append(r["name"])
        time.sleep(1.5)

    print("\n" + "=" * 40, flush=True)
    print(f"成功 {len(ok)}: {ok}", flush=True)
    print(f"失败 {len(fail)}: {fail}", flush=True)
    return 0 if not fail else 1


if __name__ == "__main__":
    sys.exit(main())
