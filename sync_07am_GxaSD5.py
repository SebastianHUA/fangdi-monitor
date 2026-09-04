# -*- coding: utf-8 -*-
"""07:00 楼市回顾 -> 腾讯文档 GxaSD5 同步。

用法： python311 sync_07am_GxaSD5.py <YYYY-MM-DD> [毫秒戳]
      不传毫秒戳则自动按该日期 UTC 午夜计算。

⚠️ 2026-08-31 重写：
  - 调用通道由已失效的 mcporter（tdoc_helper）改为直连 MCP（tdoc_mcp）
  - 日期解析改用 get_field()，修复 field_values/fields 结构误判导致重复新增的 bug
  - DATE / TS 改为命令行传参，不再硬编码
"""
import datetime
import json
import sys
import time

sys.path.insert(0, r"C:\Users\huaxi\WorkBuddy\Claw")
from tdoc_mcp import call, ok, get_field  # noqa: E402

FILE_ID = "DTnNsSXVoc21TbkhF"
SHEET = "GxaSD5"

if len(sys.argv) < 2:
    print("usage: sync_07am_GxaSD5.py <YYYY-MM-DD> [ts_ms]")
    sys.exit(2)
DATE = sys.argv[1]
if len(sys.argv) >= 3:
    TS = sys.argv[2]
else:
    y, m, d = [int(x) for x in DATE.split("-")]
    TS = str(int(datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc).timestamp() * 1000))
print("DATE=%s TS=%s" % (DATE, TS))


def main():
    with open(r"C:\Users\huaxi\WorkBuddy\Claw\data\fangdi_data.json", encoding="utf-8") as f:
        data = json.load(f)
    rec = next((x for x in data if x.get("date") == DATE), None)
    if not rec:
        print("NO_RECORD")
        return 1
    review = rec.get("marketReview", "") or ""
    if not review:
        print("WARN: marketReview 为空，仍继续写入")

    for attempt in range(3):
        lst = call("smartsheet.list_records", {"file_id": FILE_ID, "sheet_id": SHEET})
        if not ok(lst):
            print("LIST_FAIL", str(lst)[:200])
            time.sleep(10 if attempt == 0 else 30)
            continue
        records = lst.get("records", [])
        rid = None
        for r in records:
            if get_field(r, "日期") == str(TS):
                rid = r.get("record_id")
                break
        rv = {"field": "楼市回顾内容", "text_value": {"items": [{"text": review, "type": "text"}]}}
        if rid:
            resp = call("smartsheet.update_records", {
                "file_id": FILE_ID, "sheet_id": SHEET,
                "records": [{"record_id": rid, "field_values": [rv]}],
            })
            mode = "UPDATE"
        else:
            dv = {"field": "日期", "string_value": str(TS)}
            resp = call("smartsheet.add_records", {
                "file_id": FILE_ID, "sheet_id": SHEET,
                "records": [{"field_values": [dv, rv]}],
            })
            mode = "ADD"
        if ok(resp):
            print("GXASD5_OK mode=%s rid=%s" % (mode, rid or "NEW"))
            return 0
        print("WRITE_FAIL(%s) attempt=%d -> %s" % (mode, attempt + 1, str(resp)[:300]))
        time.sleep(10 if attempt == 0 else 30)

    print("GXASD5_GAVEUP")
    return 1


if __name__ == "__main__":
    sys.exit(main())
