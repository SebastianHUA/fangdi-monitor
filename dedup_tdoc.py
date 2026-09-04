# -*- coding: utf-8 -*-
"""腾讯文档智能表去重（无损）。

背景：23:50 一手房任务先写入"只有一手房"的残缺行，07:00 任务未匹配到该行、
又新增了一条完整行 -> 同一日期出现 2 条记录，表格里出现面积/套均为 0 的行。

安全策略：只有当 A 的所有字段（除日期）都在 B 中存在且值完全相同（即 A ⊂ B）时，
才删除 A。否则跳过并报告，绝不猜测。

用法：
    python dedup_tdoc.py            # dry-run，只报告
    python dedup_tdoc.py --apply    # 实际删除
"""
import sys, json, datetime
sys.path.insert(0, r'C:\Users\huaxi\WorkBuddy\Claw')
sys.stdout.reconfigure(encoding='utf-8')
from tdoc_helper import call, ok

FILE_ID = 'DTnNsSXVoc21TbkhF'
SHEETS = ('GxaSD5', 'bwHrDx')
APPLY = '--apply' in sys.argv


def fv_map(rec):
    out = {}
    for fv in rec.get('field_values', []):
        f = fv.get('field')
        if 'number_value' in fv:
            out[f] = fv['number_value']
        elif 'string_value' in fv:
            out[f] = fv['string_value']
        elif 'text_value' in fv:
            try:
                out[f] = fv['text_value']['items'][0]['text']
            except Exception:
                out[f] = ''
    return out


def norm_date(v):
    if v is None:
        return None
    s = str(v)
    if s.isdigit():
        return datetime.datetime.utcfromtimestamp(int(s) / 1000).strftime('%Y-%m-%d')
    return s[:10]


backup = {}
summary = []

for sheet in SHEETS:
    lst = call('smartsheet.list_records', {'file_id': FILE_ID, 'sheet_id': sheet})
    if not ok(lst):
        print('LIST_FAIL', sheet, str(lst)[:300])
        sys.exit(1)
    records = lst.get('records', [])
    backup[sheet] = records

    bydate = {}
    for r in records:
        m = fv_map(r)
        bydate.setdefault(norm_date(m.get('日期')), []).append((r['record_id'], m))

    to_delete = []
    for d, entries in sorted(bydate.items()):
        if len(entries) < 2:
            continue
        # 按字段数降序，最"完整"的留下
        entries = sorted(entries, key=lambda x: -len(x[1]))
        keep_rid, keep_m = entries[0]
        for rid, m in entries[1:]:
            sub = {k: v for k, v in m.items() if k != '日期'}
            is_subset = all(k in keep_m and keep_m[k] == v for k, v in sub.items())
            if is_subset:
                to_delete.append((d, rid, len(sub)))
                print(f'[{sheet}] {d} 冗余条 {rid}（{len(sub)}字段，是 {keep_rid} 的子集）-> 可删')
            else:
                diff = {k: (v, keep_m.get(k, '<缺>')) for k, v in sub.items()
                        if k not in keep_m or keep_m[k] != v}
                print(f'[{sheet}] {d} 两条不一致，跳过不动：{rid} vs {keep_rid}')
                print(f'         差异字段: {json.dumps(diff, ensure_ascii=False)[:300]}')

    summary.append((sheet, to_delete))

print()
print('=========== 汇总 ===========')
total = 0
for sheet, dels in summary:
    print(f'{sheet}: 可安全删除 {len(dels)} 条 -> {[r for _, r, _ in dels]}')
    total += len(dels)
print('合计', total, '条')

if not APPLY:
    print('\n[dry-run] 未做任何修改。加 --apply 执行删除。')
    sys.exit(0)

# 备份
bpath = r'C:\Users\huaxi\WorkBuddy\Claw\data\tdoc_backup_before_dedup.json'
with open(bpath, 'w', encoding='utf-8') as f:
    json.dump(backup, f, ensure_ascii=False, indent=2)
print('\n已备份原始记录 ->', bpath)

for sheet, dels in summary:
    if not dels:
        continue
    rids = [r for _, r, _ in dels]
    resp = call('smartsheet.delete_records',
                {'file_id': FILE_ID, 'sheet_id': sheet, 'record_ids': rids})
    print(f'{sheet} 删除 {len(rids)} 条 ->', 'OK' if ok(resp) else f'FAIL {str(resp)[:300]}')
