"""向腾讯文档工作日志智能表追加/新建某日工作内容。

表: file_id=DTkZDSWpxbWVUa1NN  sheet=NxtEWi
字段: 日期(string_value 毫秒戳, 上海00:00) + 工作内容(text_value 多行序号)
约定: 同一天先查后追加, 续接序号, 绝不替换既有内容。

用法:
    python work_log_sync.py <YYYY-MM-DD> "条目1" "条目2" ...
"""
import sys
import json
import datetime

sys.path.insert(0, r'C:\Users\huaxi\WorkBuddy\Claw')
from tdoc_mcp import call, ok

FILE = 'DTkZDSWpxbWVUa1NN'
SHEET = 'NxtEWi'


def shanghai_ms(y, m, d):
    sh = datetime.timezone(datetime.timedelta(hours=8))
    dt = datetime.datetime(y, m, d, 0, 0, 0, tzinfo=sh)
    return int(dt.timestamp() * 1000)


def find_record(ts_str):
    r = call('smartsheet.list_records',
             {'file_id': FILE, 'sheet_id': SHEET, 'page_size': 200})
    if not ok(r):
        raise RuntimeError('list_records 失败: ' + json.dumps(r, ensure_ascii=False)[:300])
    for rec in r.get('records', []):
        for fv in rec.get('field_values', []):
            if fv.get('field') == '日期' and fv.get('string_value') == ts_str:
                return rec
    return None


def get_content(rec):
    for fv in rec.get('field_values', []):
        if fv.get('field') == '工作内容' and isinstance(fv.get('text_value'), dict):
            return ''.join(it.get('text', '') for it in fv['text_value'].get('items', []))
    return ''


def strip_no(line):
    """去掉行首序号（1. / 1、/ 1) 等），返回用于去重的正文指纹。"""
    import re
    return re.sub(r'^\s*\d+\s*[.、)．]\s*', '', line).strip()


def main():
    if len(sys.argv) < 3:
        print('用法: python work_log_sync.py <YYYY-MM-DD> "条目1" "条目2" ...')
        sys.exit(1)
    date_str = sys.argv[1]
    items = sys.argv[2:]
    y, m, d = map(int, date_str.split('-'))
    ts = shanghai_ms(y, m, d)
    ts_str = str(ts)

    new_block = '\n'.join(f'{i}. {c}' for i, c in enumerate(items, 1))

    rec = find_record(ts_str)
    if rec:
        rid = rec['record_id']
        existing = get_content(rec).strip()
        exist_lines = [l for l in existing.split('\n') if l.strip()]
        exist_keys = [strip_no(l) for l in exist_lines]

        # 🚨 去重：本次条目中已在表里的直接跳过，只追加差异项
        dup = [c for c in items if strip_no(c) in exist_keys]
        todo = [c for c in items if strip_no(c) not in exist_keys]
        if dup:
            print(f'SKIP_DUP({len(dup)}): ' + ' | '.join(dup))
        if not todo:
            print(f'NO_CHANGE record_id={rid} — 本次条目已全部存在，不写入（避免重复追加）')
            print('VERIFY_CONTENT=\n' + existing)
            return

        start = len(exist_lines) + 1
        appended = '\n'.join(f'{start + i}. {c}' for i, c in enumerate(todo))
        merged = (existing + '\n' + appended).strip() if existing else appended
        resp = call('smartsheet.update_records', {
            'file_id': FILE, 'sheet_id': SHEET,
            'records': [{
                'record_id': rid,
                'field_values': [{
                    'field': '工作内容',
                    'text_value': {'items': [{'text': merged, 'type': 'text'}]}
                }]
            }]
        })
        action = 'UPDATE' if ok(resp) else 'UPDATE_FAIL'
        print(f'{action} record_id={rid} (新增 {len(todo)} 条, 原 {len(exist_lines)} 条 → 现 {len(merged.splitlines())} 条)')
    else:
        resp = call('smartsheet.add_records', {
            'file_id': FILE, 'sheet_id': SHEET,
            'records': [{'field_values': [
                {'field': '日期', 'string_value': ts_str},
                {'field': '工作内容', 'text_value': {'items': [{'text': new_block, 'type': 'text'}]}}
            ]}]
        })
        action = 'ADD' if ok(resp) else 'ADD_FAIL'
        rid = ''
        if isinstance(resp, dict):
            recs = resp.get('records', [])
            if recs:
                rid = recs[0].get('record_id', '')
        print(f'{action} record_id={rid} ts={ts_str}')

    # 回读校验
    rec2 = find_record(ts_str)
    if rec2:
        final = get_content(rec2)
        print('VERIFY_CONTENT=\n' + final)
        print('VERIFY_TS=' + str([fv.get('string_value') for fv in rec2['field_values'] if fv.get('field') == '日期']))


if __name__ == '__main__':
    main()
