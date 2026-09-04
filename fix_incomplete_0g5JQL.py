# -*- coding: utf-8 -*-
"""修复 0g5JQL 子表内的「残缺记录」——补回丢失的字段值。

背景：历史上腾讯文档通道多次失效（mcporter/tencentdocs/tdoc_helper），
add_records 有时只创建记录不写字段，导致表内留下 6 条半截记录：
  - 3 条缺 项目名称/所在区/开发企业/认购比   （只能靠 套数+备案均价 反查身份）
  - 3 条缺 数据日期/认购开始日期/认购结束日期

修复策略：用「套数 + 备案均价」从本地 subscription_data.json 反查完整数据，
然后 update_records 全量重写 10 个字段（保留已有正确值，补上缺失值）。

用法:
    python fix_incomplete_0g5JQL.py --dry-run
    python fix_incomplete_0g5JQL.py
"""
import sys
import os
import json
import io
import time
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tdoc_mcp import call, ok                      # noqa: E402
from sync_subscription_0g5JQL import (             # noqa: E402
    FILE, SHEET, gv, ms_to_date, sh_ms, load_table, build_field_values)

# record_id → 该批次在数据里的定位键（套数 + 备案均价）+ 数据日期
# 数据日期依据：认购自动化 memory.md 历史新增记录 + 「发现日≈认购开始日当天或前1天」口径
FIX_PLAN = [
    # rid,      套数, 备案均价,   数据日期
    ('rAxQrM',  92,  73878,   '2026-08-07'),  # 水岸和煦名邸 memory 08-07 新增
    ('rNCLMh',  98,  51384,   '2026-08-22'),  # 潮鸣宸邸   沿用记录内已有数据日期
    ('r7oFEA',  22,  67000,   '2026-08-26'),  # 贤和雅园   沿用记录内已有数据日期
    ('reZxet',  176, 390000,  '2026-08-27'),  # 乐满庭     认购8/27，早于誉品雅苑(8/28)发现
    ('rwbVgb',  120, 52295,   '2026-08-28'),  # 誉品雅苑   memory 08-28 新增(已确认)
    ('reDrHb',  92,  58483,   '2026-08-30'),  # 锦棠瑞宸名邸 认购8/30，晚于誉品雅苑发现
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    data = json.load(io.open(os.path.join(here, 'data', 'subscription_data.json'),
                             encoding='utf-8'))
    items = data.get('recentSubscriptions', [])

    recs = load_table()
    by_rid = {r.get('record_id'): r for r in recs}
    print('表内 %d 条' % len(recs))

    updates = []
    for rid, units, price, data_date in FIX_PLAN:
        rec = by_rid.get(rid)
        if rec is None:
            print('MISS 记录不存在: %s' % rid)
            continue
        # 用 套数+备案均价 定位本地数据
        hits = [x for x in items
                if x.get('套数') == units and x.get('备案均价') == price]
        if not hits:
            print('FAIL 本地无匹配: rid=%s 套=%s 价=%s' % (rid, units, price))
            continue
        if len(hits) > 1:
            print('WARN 本地多条匹配: rid=%s 套=%s 价=%s → %s' % (
                rid, units, price, [h.get('项目名称') for h in hits]))
        it = hits[0]

        print()
        print('rid=%s  →  %s (%s) 套=%s 价=%s 认购 %s~%s' % (
            rid, it.get('项目名称'), it.get('所在区'), units, price,
            it.get('认购开始时间'), it.get('认购结束时间')))
        print('    表内现状: 项目=%s 数据日期=%s 认购开始=%s' % (
            gv(rec, '项目名称'), ms_to_date(gv(rec, '数据日期')),
            ms_to_date(gv(rec, '认购开始日期'))))
        print('    将写入  : 数据日期=%s 认购 %s~%s' % (
            data_date, it.get('认购开始时间'), it.get('认购结束时间')))

        fvs = build_field_values(it, data_date)
        got = {fv.get('field') for fv in fvs}
        miss = [f for f in ['数据日期', '认购开始日期', '认购结束日期', '项目名称', '所在区',
                            '开发企业', '认购比', '套数（套）', '上市面积（㎡）',
                            '备案均价（元/㎡）'] if f not in got]
        if miss:
            print('    ABORT 本地数据缺字段 %s' % miss)
            sys.exit(2)
        updates.append({'record_id': rid, 'field_values': fvs})

    if not updates:
        print('NO_CHANGE 无需修复')
        return
    if args.dry_run:
        print()
        print('DRY_RUN 跳过写入（待修复 %d 条）' % len(updates))
        return

    resp = call('smartsheet.update_records', {
        'file_id': FILE, 'sheet_id': SHEET, 'records': updates
    })
    if not ok(resp):
        print('UPDATE_FAIL ' + json.dumps(resp, ensure_ascii=False)[:600])
        sys.exit(1)
    print()
    print('UPDATE_OK count=%d' % len(updates))

    time.sleep(2)
    recs2 = {r.get('record_id'): r for r in load_table()}
    print()
    print('=== 回读校验 ===')
    ALL = ['数据日期', '认购开始日期', '认购结束日期', '项目名称', '所在区',
           '开发企业', '认购比', '套数（套）', '上市面积（㎡）', '备案均价（元/㎡）']
    all_ok = True
    for rid, units, price, data_date in FIX_PLAN:
        rec = recs2.get(rid)
        if rec is None:
            print('  %s VERIFY_FAIL 消失' % rid)
            all_ok = False
            continue
        fields = [fv.get('field') for fv in rec.get('field_values', [])]
        miss = [f for f in ALL if f not in fields]
        print('  %s %-14s 数据日期=%s 认购=%s~%s 缺字段=%s' % (
            rid, gv(rec, '项目名称'), ms_to_date(gv(rec, '数据日期')),
            ms_to_date(gv(rec, '认购开始日期')), ms_to_date(gv(rec, '认购结束日期')),
            miss or '(完整)'))
        if miss:
            all_ok = False
    print()
    print('ALL_OK' if all_ok else 'SOME_INCOMPLETE')


if __name__ == '__main__':
    main()
