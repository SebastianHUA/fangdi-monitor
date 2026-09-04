# -*- coding: utf-8 -*-
"""认购公示 → 腾讯文档智能表 0g5JQL 同步脚本。

表结构（10 字段）:
  数据日期          string_value 毫秒戳（上海午夜）
  认购开始日期      string_value 毫秒戳（上海午夜）
  认购结束日期      string_value 毫秒戳（上海午夜）
  项目名称/所在区/开发企业/认购比   text_value
  套数（套）/上市面积（㎡）/备案均价（元/㎡）  number_value

用法:
    # 1) 自动模式：把本地 subscription_data.json 里所有缺失的楼盘补进表里
    python sync_subscription_0g5JQL.py

    # 2) 只处理某一天新增的楼盘
    python sync_subscription_0g5JQL.py --date 2026-09-01

    # 3) 只补录指定项目名（可多次传）
    python sync_subscription_0g5JQL.py --name 溯阳云筑

    # 4) 检查模式（不写入，只报告差异）
    python sync_subscription_0g5JQL.py --dry-run

    # 5) 精确批次补录（历史遗留补录专用，走 JSON 计划文件，避免命令行中文编码问题）
    python sync_subscription_0g5JQL.py --plan backfill_plan.json

plan 文件格式（每条指定 项目名 + 认购开始日期 + 该批次的数据日期）：
    [
      {"项目名称": "润耀华庭", "认购开始时间": "2026-08-20", "数据日期": "2026-08-19"},
      ...
    ]
同一楼盘不同批次用「项目名 + 认购开始日期」唯一定位，不会互相干扰。

去重键：项目名称 + 认购开始日期（预售许可证号不在表内，故用此组合）。
"""
import sys
import json
import io
import os
import time
import datetime
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tdoc_mcp import call, ok  # noqa: E402

FILE = 'DTnNsSXVoc21TbkhF'
SHEET = '0g5JQL'
SH = datetime.timezone(datetime.timedelta(hours=8))

# ⚠️ 表字段名 ≠ 本地 JSON 字段名，必须显式映射，否则静默丢字段
#    （本地 subscription_data.json 用「套数/上市面积/备案均价/入围比」无单位后缀）
FIELD_MAP = {
    '项目名称': '项目名称',
    '所在区': '所在区',
    '开发企业': '开发企业',
    '认购比': '入围比',              # 表里叫「认购比」，本地叫「入围比」
    '套数（套）': '套数',
    '上市面积（㎡）': '上市面积',
    '备案均价（元/㎡）': '备案均价',
}
TEXT_FIELDS = ['项目名称', '所在区', '开发企业', '认购比']
NUM_FIELDS = ['套数（套）', '上市面积（㎡）', '备案均价（元/㎡）']
DATE_FIELDS = ['数据日期', '认购开始日期', '认购结束日期']


def sh_ms(date_str):
    """'YYYY-MM-DD' → 上海当天 00:00 的毫秒戳字符串。"""
    y, m, d = map(int, date_str.split('-'))
    dt = datetime.datetime(y, m, d, 0, 0, 0, tzinfo=SH)
    return str(int(dt.timestamp() * 1000))


def ms_to_date(ms):
    if ms is None:
        return None
    try:
        ts = int(str(ms))
    except (TypeError, ValueError):
        return None
    return datetime.datetime.fromtimestamp(ts / 1000, SH).strftime('%Y-%m-%d')


def gv(rec, field):
    """容错读取一个字段值（number / text / string 三种形态）。"""
    for fv in rec.get('field_values', []):
        if fv.get('field') == field:
            if fv.get('number_value') is not None:
                return fv['number_value']
            items = (fv.get('text_value') or {}).get('items') or []
            if items:
                return items[0].get('text')
            sv = fv.get('string_value')
            if sv is not None:
                return sv
    return None


def load_table():
    r = call('smartsheet.list_records', {'file_id': FILE, 'sheet_id': SHEET, 'page_size': 200})
    if not ok(r):
        raise RuntimeError('list_records 失败: ' + json.dumps(r, ensure_ascii=False)[:400])
    return r.get('records', [])


def build_field_values(item, data_date):
    """把一个楼盘 dict 转成 field_values 列表（10 字段全传，避免历史遗漏问题）。"""
    fvs = []
    fvs.append({'field': '数据日期', 'string_value': sh_ms(data_date)})
    fvs.append({'field': '认购开始日期', 'string_value': sh_ms(item['认购开始时间'])})
    fvs.append({'field': '认购结束日期', 'string_value': sh_ms(item['认购结束时间'])})
    for f in TEXT_FIELDS:
        v = item.get(FIELD_MAP[f])
        if v is None or str(v).strip() == '':
            continue
        fvs.append({'field': f, 'text_value': {'items': [{'text': str(v), 'type': 'text'}]}})
    for f in NUM_FIELDS:
        v = item.get(FIELD_MAP[f])
        if v is None:
            continue
        fvs.append({'field': f, 'number_value': v})
    return fvs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', help='只处理该数据日期(YYYY-MM-DD)的楼盘')
    ap.add_argument('--name', action='append', help='只处理指定项目名称，可多次传')
    ap.add_argument('--plan', help='JSON 计划文件：按批次精确补录，每条自带数据日期')
    ap.add_argument('--dry-run', action='store_true', help='只报告不写入')
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    data = json.load(io.open(os.path.join(here, 'data', 'subscription_data.json'), encoding='utf-8'))
    data_date = args.date or data.get('date')
    items = data.get('recentSubscriptions', [])

    print('本地数据: date=%s 共%d条 (数据日期字段用 %s)' % (data.get('date'), len(items), data_date))

    # --plan 模式：每批次自带数据日期，逐条独立处理
    plan = None
    if args.plan:
        plan = json.load(io.open(args.plan, encoding='utf-8'))
        print('计划文件: %d 条' % len(plan))

    if args.name:
        items = [x for x in items if x.get('项目名称') in args.name]
        print('按名称过滤后: %d 条' % len(items))

    recs = load_table()
    print('表内现有记录: %d 条' % len(recs))

    # ⚠️ 表内历史记录存在字段缺失（部分缺项目名、部分缺认购日期），
    # 只按「项目名+认购开始日期」去重会把这些记录判成新盘 → 制造重复。
    # 采用三级匹配：
    #   L1 项目名 + 认购开始日期
    #   L2 项目名 + 套数 + 备案均价   （应对缺日期的记录）
    #   L3 套数 + 备案均价            （应对项目名也缺失的记录）
    keys_name_date = set()
    keys_name_num = set()
    keys_num = set()
    for rec in recs:
        n = gv(rec, '项目名称')
        s = ms_to_date(gv(rec, '认购开始日期'))
        u = gv(rec, '套数（套）')
        p = gv(rec, '备案均价（元/㎡）')
        n = str(n) if n else None
        if n and s:
            keys_name_date.add((n, s))
        if n and u is not None and p is not None:
            keys_name_num.add((n, u, p))
        if u is not None and p is not None:
            keys_num.add((u, p))

    def matched(it):
        name = it.get('项目名称')
        start = it.get('认购开始时间')
        u, p = it.get('套数'), it.get('备案均价')
        if name and start and (name, start) in keys_name_date:
            return 'L1'
        if name and u is not None and p is not None and (name, u, p) in keys_name_num:
            return 'L2'
        if u is not None and p is not None and (u, p) in keys_num:
            return 'L3'
        return None

    # pending: [(本地条目, 该批次数据日期), ...]
    pending = []
    if plan is not None:
        index = {}
        for it in items:
            index.setdefault((it.get('项目名称'), it.get('认购开始时间')), it)
        for p in plan:
            key = (p['项目名称'], p['认购开始时间'])
            it = index.get(key)
            if it is None:
                print('PLAN_MISS 本地无此批次: %s' % (key,))
                sys.exit(2)
            if matched(it):
                print('PLAN_SKIP 表内已存在: %s (%s)' % (it.get('项目名称'), it.get('认购开始时间')))
                continue
            pending.append((it, p['数据日期']))
    else:
        for it in items:
            if not matched(it):
                pending.append((it, data_date))

    print('待新增: %d 条' % len(pending))
    for it, dd in pending:
        print('   + %s | %s | %s套 | %s元/㎡ | 认购 %s~%s | 数据日期 %s' % (
            it.get('项目名称'), it.get('所在区'), it.get('套数'),
            it.get('备案均价'), it.get('认购开始时间'), it.get('认购结束时间'), dd))

    if not pending:
        print('NO_CHANGE 表内已全部存在，无需写入')
        return
    if args.dry_run:
        print('DRY_RUN 跳过写入')
        return

    batch = []
    for it, dd in pending:
        fvs = build_field_values(it, dd)
        # 🚨 写入前自检：字段不全直接拒绝，避免再产生「半截记录」
        got = {fv.get('field') for fv in fvs}
        miss = [f for f in DATE_FIELDS + TEXT_FIELDS + NUM_FIELDS if f not in got]
        if miss:
            print('ABORT 字段缺失(%s) → 拒绝写入 %s' % (miss, it.get('项目名称')))
            print('   本地原始数据: ' + json.dumps(it, ensure_ascii=False)[:300])
            sys.exit(2)
        batch.append({'field_values': fvs})
    resp = call('smartsheet.add_records', {
        'file_id': FILE, 'sheet_id': SHEET, 'records': batch
    })
    if not ok(resp):
        print('ADD_FAIL ' + json.dumps(resp, ensure_ascii=False)[:600])
        sys.exit(1)

    new_ids = [x.get('record_id') for x in (resp.get('records') or [])]
    print('ADD_OK count=%d rid=%s' % (len(batch), new_ids))

    # 回读校验
    time.sleep(2)
    recs2 = load_table()
    print('回读: 表内 %d 条' % len(recs2))
    for it, dd in pending:
        hit = None
        for rec in recs2:
            if gv(rec, '项目名称') == it.get('项目名称') and \
               ms_to_date(gv(rec, '认购开始日期')) == it.get('认购开始时间'):
                hit = rec
                break
        if hit:
            miss = [f for f in DATE_FIELDS + TEXT_FIELDS + NUM_FIELDS
                    if f not in [fv.get('field') for fv in hit.get('field_values', [])]]
            print('  VERIFY %s rid=%s 套=%s 价=%s 缺字段=%s' % (
                it.get('项目名称'), hit.get('record_id'), gv(hit, '套数（套）'),
                gv(hit, '备案均价（元/㎡）'), miss or '(完整)'))
        else:
            print('  VERIFY_FAIL 未找到 %s' % it.get('项目名称'))


if __name__ == '__main__':
    main()
