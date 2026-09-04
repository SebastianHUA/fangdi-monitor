# -*- coding: utf-8 -*-
"""07:00 完整数据 -> 腾讯文档 bwHrDx 同步（一手房 + 二手房）。

用法： python311 sync_07am_bwHrDx.py <YYYY-MM-DD>

⚠️ 2026-08-31 重写：
  - 调用通道由已失效的 mcporter（tdoc_helper）改为直连 MCP（tdoc_mcp）
  - 日期解析改用 get_field()，修复「按 r['fields'] 解析导致全部日期判 MISSING，
    进而重复 add_records」的历史 bug
  - DATE 改为命令行传参，不再硬编码
"""
import json
import sys
import time

sys.path.insert(0, r"C:\Users\huaxi\WorkBuddy\Claw")
from tdoc_mcp import call, ok, get_field  # noqa: E402

FILE_ID = "DTnNsSXVoc21TbkhF"
SHEET = "bwHrDx"

if len(sys.argv) < 2:
    print("usage: sync_07am_bwHrDx.py <YYYY-MM-DD>")
    sys.exit(2)
DATE = sys.argv[1]


def main():
    with open(r"C:\Users\huaxi\WorkBuddy\Claw\data\fangdi_data.json", encoding="utf-8") as f:
        data = json.load(f)
    rec = next((x for x in data if x.get("date") == DATE), None)
    if not rec:
        print("NO_RECORD")
        return 1

    nh = rec.get("newHouse", {})
    sh = rec.get("secondHand", {})
    if not sh:
        print("NO_SECONDHAND: 二手房数据缺失，只更新一手房字段")

    nh_u = nh.get("todaySignUnits") or 0
    nh_a = nh.get("todaySignArea") or 0
    sh_c = sh.get("yesterdaySaleCount") or 0
    sh_a = sh.get("yesterdaySaleArea") or 0
    nh_avg = round(nh_a / nh_u, 2) if nh_u else 0
    sh_avg = round(sh_a / sh_c, 2) if sh_c else 0
    print("本地: 一手 %s套/%s㎡/套均%s/可售%s | 二手 %s套/%s㎡/套均%s/挂牌%s"
          % (nh_u, nh_a, nh_avg, nh.get("availableUnits"), sh_c, sh_a, sh_avg,
             sh.get("listingCount")))

    field_values = [
        {"field": "一手房成交套数", "number_value": nh_u},
        {"field": "一手房成交面积（㎡）", "number_value": nh_a},
        {"field": "一手房套均面积（㎡/套）", "number_value": nh_avg},
        {"field": "一手房可售套数", "number_value": nh.get("availableUnits") or 0},
    ]
    if sh:
        field_values += [
            {"field": "二手房成交套数", "number_value": sh_c},
            {"field": "二手房成交面积（㎡）", "number_value": sh_a},
            {"field": "二手房套均面积（㎡/套）", "number_value": sh_avg},
            {"field": "二手房挂牌套数", "number_value": sh.get("listingCount") or 0},
        ]

    for attempt in range(3):
        lst = call("smartsheet.list_records", {"file_id": FILE_ID, "sheet_id": SHEET})
        if not ok(lst):
            print("LIST_FAIL", str(lst)[:200])
            time.sleep(10 if attempt == 0 else 30)
            continue
        records = lst.get("records", [])
        rid = None
        for r in records:
            if get_field(r, "日期") == DATE:
                rid = r.get("record_id")
                break
        if rid:
            resp = call("smartsheet.update_records", {
                "file_id": FILE_ID, "sheet_id": SHEET,
                "records": [{"record_id": rid, "field_values": field_values}],
            })
            mode = "UPDATE"
        else:
            dv = {"field": "日期", "text_value": {"items": [{"text": DATE, "type": "text"}]}}
            resp = call("smartsheet.add_records", {
                "file_id": FILE_ID, "sheet_id": SHEET,
                "records": [{"field_values": [dv] + field_values}],
            })
            mode = "ADD"
        if ok(resp):
            print("BWHRDX_OK mode=%s rid=%s" % (mode, rid or "NEW"))
            return 0
        print("WRITE_FAIL(%s) attempt=%d -> %s" % (mode, attempt + 1, str(resp)[:300]))
        time.sleep(10 if attempt == 0 else 30)

    print("BWHRDX_GAVEUP")
    return 1


if __name__ == "__main__":
    sys.exit(main())
