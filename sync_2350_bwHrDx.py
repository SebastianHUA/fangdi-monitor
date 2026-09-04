# -*- coding: utf-8 -*-
"""23:50 一手房数据 -> 腾讯文档 bwHrDx 同步（只更新一手房字段，不动二手房）。

用法： python311 sync_2350_bwHrDx.py <YYYY-MM-DD>
"""
import json
import sys
import time

sys.path.insert(0, r"C:\Users\huaxi\WorkBuddy\Claw")
from tdoc_mcp import call, ok  # noqa: E402

FILE_ID = "DTnNsSXVoc21TbkhF"
SHEET = "bwHrDx"

if len(sys.argv) < 2:
    print("usage: sync_2350_bwHrDx.py <YYYY-MM-DD>")
    sys.exit(2)
DATE = sys.argv[1]


def main():
    # ---- 读本地记录 ----
    with open(r"C:\Users\huaxi\WorkBuddy\Claw\data\fangdi_data.json", encoding="utf-8") as f:
        data = json.load(f)
    rec = next((x for x in data if x.get("date") == DATE), None)
    if not rec:
        print("NO_LOCAL_RECORD")
        return 1
    nh = rec.get("newHouse", {})
    units = nh.get("todaySignUnits")
    area = nh.get("todaySignArea")
    avail = nh.get("availableUnits")
    if not units:
        print("BAD_UNITS", units)
        return 1
    avg = round(area / units, 2) if units else 0
    print("本地数据: 套数=%s 面积=%s 套均=%s 可售=%s" % (units, area, avg, avail))

    # ---- 列字段，确认标题（防 field not found） ----
    fields_resp = call("smartsheet.list_fields", {"file_id": FILE_ID, "sheet_id": SHEET})
    titles = []
    if ok(fields_resp):
        for f in (fields_resp.get("fields") or fields_resp.get("result") or []):
            t = f.get("title") or f.get("field_title") or f.get("name")
            if t:
                titles.append(t)
    print("表字段(%d): %s" % (len(titles), titles))

    # ---- list_records 找当天 record_id ----
    lst = None
    for attempt in range(3):
        lst = call("smartsheet.list_records", {"file_id": FILE_ID, "sheet_id": SHEET})
        if ok(lst):
            break
        print("LIST_FAIL", str(lst)[:200])
        time.sleep(10 if attempt == 0 else 30)
    if not ok(lst):
        print("BWHRDX_LIST_GAVEUP")
        return 1

    records = lst.get("records", [])
    print("返回记录数:", len(records))

    def field_text(r, name):
        """从 record 里取字段文本，兼容 field_values / fields 两种结构。"""
        fvs = r.get("field_values")
        if isinstance(fvs, list):
            for fv in fvs:
                if fv.get("field") == name:
                    tv = fv.get("text_value")
                    if isinstance(tv, dict):
                        items = tv.get("items") or []
                        if items:
                            return items[0].get("text", "")
                    if "number_value" in fv:
                        return str(fv["number_value"])
                    if "string_value" in fv:
                        return str(fv["string_value"])
            return None
        flds = r.get("fields") or {}
        v = flds.get(name)
        if isinstance(v, dict):
            tv = v.get("text_value")
            if isinstance(tv, dict):
                items = tv.get("items") or []
                if items:
                    return items[0].get("text", "")
            if "number_value" in v:
                return str(v["number_value"])
            if "string_value" in v:
                return str(v["string_value"])
            return None
        return str(v) if v is not None else None

    rid = None
    for r in records:
        if field_text(r, "日期") == DATE:
            rid = r.get("record_id")
            break
    print("当天 record_id:", rid or "(无，需新增)")

    # ---- 构造一手房字段（带单位后缀的标题，按需校验） ----
    def pick(*cands):
        for c in cands:
            if c in titles:
                return c
        return cands[0]

    f_units = pick("一手房成交套数")
    f_area = pick("一手房成交面积（㎡）", "一手房成交面积")
    f_avg = pick("一手房套均面积（㎡/套）", "一手房套均面积")
    f_avail = pick("一手房可售套数")

    field_values = [
        {"field": f_units, "number_value": units},
        {"field": f_area, "number_value": area},
        {"field": f_avg, "number_value": avg},
        {"field": f_avail, "number_value": avail},
    ]
    print("将写入字段:", [fv["field"] for fv in field_values])

    # ---- 写入（update 或 add），失败重试 ----
    for attempt in range(3):
        if rid:
            resp = call(
                "smartsheet.update_records",
                {
                    "file_id": FILE_ID,
                    "sheet_id": SHEET,
                    "records": [{"record_id": rid, "field_values": field_values}],
                },
            )
            mode = "UPDATE"
        else:
            dv = {"field": "日期", "text_value": {"items": [{"text": DATE, "type": "text"}]}}
            resp = call(
                "smartsheet.add_records",
                {
                    "file_id": FILE_ID,
                    "sheet_id": SHEET,
                    "records": [{"field_values": [dv] + field_values}],
                },
            )
            mode = "ADD"
        if ok(resp):
            print("BWHRDX_OK mode=%s rid=%s" % (mode, rid or "NEW"))
            print("响应:", json.dumps(resp, ensure_ascii=False)[:400])
            return 0
        print("WRITE_FAIL(%s) attempt=%d -> %s" % (mode, attempt + 1, str(resp)[:300]))
        time.sleep(10 if attempt == 0 else 30)

    print("BWHRDX_GAVEUP")
    return 1


if __name__ == "__main__":
    sys.exit(main())
