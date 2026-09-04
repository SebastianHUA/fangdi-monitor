# -*- coding: utf-8 -*-
"""上海土地市场监控 → 腾讯文档电子表格 NHsPBsupJrkx / 000001 全量比对补录。

背景：
 - 表格是**传统电子表格**（不是 smartsheet），用 sheet.* 系列工具。
 - 列序与 land_monitor_results.csv 完全一致（A=公告标题 … P=四至范围），共 16 列。
 - 数据行从第 2 行起（第 1 行是字段名表头），越往下越旧。
 - 去重键：发布日期 + 公告类型 + 地块公告号 + 地块名称。
 - 已知坑：2026-07-28 的「拟出让预告」在表内被旧版脚本写成「出让预告」（公告号为空），
   属同一条记录，必须排除，否则会造出重复。

用法：
    python land_tdoc_sync.py --dry-run   # 只报告不写入
    python land_tdoc_sync.py             # 正式写入
"""

import csv
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tdoc_mcp import call, ok  # noqa: E402

FILE_ID = "NHsPBsupJrkx"
SHEET_ID = "000001"

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "land_monitor_results.csv")

# CSV 列顺序 = 表格 A..P
COLUMNS = ['公告标题', '发布日期', '公告类型', '地块公告号', '地块名称', '土地用途',
           '土地总面积(㎡)', '出让面积(㎡)', '容积率', '竞得人', '成交价格(万元)',
           '起始价(万元)', '保证金(万元)', '拟出让方式', '所在区', '四至范围']

# 这几个字段尽量写成数字，便于表格里排序/筛选
NUMERIC_COLS = {'土地总面积(㎡)', '出让面积(㎡)', '容积率', '成交价格(万元)',
                '起始价(万元)', '保证金(万元)'}

CHUNK = 300  # get_cell_data 单次最大行数


def read_table():
    """读整张表，返回 (表头行, 数据行列表)。"""
    rows = []
    start = 0
    while True:
        end = start + CHUNK - 1
        r = call('sheet.get_cell_data', {
            'file_id': FILE_ID, 'sheet_id': SHEET_ID,
            'start_row': start, 'end_row': end,
            'start_col': 0, 'end_col': 15, 'return_csv': True,
        })
        if not ok(r):
            raise RuntimeError('读取失败: %s' % str(r)[:300])
        lines = (r.get('csv_data') or '').split('\n')
        rows.extend(list(csv.reader(io.StringIO('\n'.join(lines)))))
        if len(lines) <= CHUNK and not (r.get('csv_data') or '').strip():
            break
        if start >= 1037:
            break
        start = end + 1
        if start > 1037:
            break
    # 去掉尾部全空行
    while rows and not any(c.strip() for c in rows[-1]):
        rows.pop()
    return rows[0], rows[1:]


def norm(v):
    return (v or '').strip()


def key_of(r):
    if isinstance(r, dict):
        return (norm(r.get('发布日期')), norm(r.get('公告类型')),
                norm(r.get('地块公告号')), norm(r.get('地块名称')))
    return (norm(r[1]), norm(r[2]), norm(r[3]), norm(r[4]) if len(r) > 4 else '')


def is_legacy_duplicate(item, doc_data):
    """排除旧版脚本造成的同记录异名：日期相同 + 地块名相同 + 表内是『出让预告』且 CSV 是『拟出让预告』。"""
    d = norm(item.get('发布日期'))
    name = norm(item.get('地块名称'))
    typ = norm(item.get('公告类型'))
    if not d or not name:
        return False
    for row in doc_data:
        if len(row) < 5:
            continue
        if norm(row[1]) == d and norm(row[4]) == name and norm(row[2]) in ('出让预告', '拟出让预告') \
                and typ in ('出让预告', '拟出让预告'):
            return True
    return False


def to_number(v):
    if v is None:
        return None
    s = str(v).strip().replace(',', '')
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def build_values(rows_to_write):
    """rows_to_write: list[dict]，写入表格第 2 行起（0-based row=1）。"""
    values = []
    for i, item in enumerate(rows_to_write):
        for c, field in enumerate(COLUMNS):
            raw = item.get(field)
            if raw is None:
                continue
            s = norm(raw)
            if field in NUMERIC_COLS:
                n = to_number(s)
                if n is not None:
                    values.append({'row': 1 + i, 'col': c, 'value_type': 'NUMBER',
                                   'number_value': n})
                    continue
            if s == '':
                continue
            values.append({'row': 1 + i, 'col': c, 'value_type': 'STRING',
                           'string_value': s})
    return values


def main():
    dry = '--dry-run' in sys.argv

    print('读取表格全量数据...')
    header, doc_data = read_table()
    print('  表头: %s' % header[:4])
    print('  数据行: %d' % len(doc_data))

    with io.open(CSV_PATH, encoding='utf-8-sig') as f:
        csv_rows = list(csv.DictReader(f))
    valid = [r for r in csv_rows if norm(r.get('地块名称'))]
    print('  CSV 有效行: %d (总 %d)' % (len(valid), len(csv_rows)))

    doc_keys = set(key_of(r) for r in doc_data if len(r) > 4)

    missing = [r for r in valid if key_of(r) not in doc_keys]
    legacy = [r for r in missing if is_legacy_duplicate(r, doc_data)]
    todo = [r for r in missing if r not in legacy]

    print()
    print('原始缺失: %d 条' % len(missing))
    print('旧版异名重复(排除): %d 条' % len(legacy))
    for r in legacy:
        print('   - %s %s %s' % (norm(r.get('发布日期')), norm(r.get('公告类型')),
                                 norm(r.get('地块名称'))[:34]))
    print()
    print('待补录: %d 条' % len(todo))

    # 按发布日期倒序（写在表格最上方，保持越往下越旧）
    todo.sort(key=lambda x: norm(x.get('发布日期')), reverse=True)

    from collections import Counter
    c = Counter(norm(r.get('发布日期')) for r in todo)
    for d in sorted(c, reverse=True):
        print('   %s : %d 条' % (d, c[d]))

    print()
    kw = ('住宅', '居住', '普通商品房', '商品房')
    for r in todo:
        hit = any(k in norm(r.get('土地用途')) for k in kw)
        print('   %s | %-6s | %-40s | %-22s%s' % (
            norm(r.get('发布日期')), norm(r.get('公告类型')),
            norm(r.get('地块名称'))[:40], norm(r.get('土地用途'))[:22],
            '  ★住宅类' if hit else ''))

    if not todo:
        print()
        print('NO_CHANGE 表内已全部存在，无需写入')
        return
    if dry:
        print()
        print('DRY_RUN 跳过写入')
        return

    # ---- 1) 清理表头下方两条孤儿标题行（只有 A 列有值，其余全空）----
    orphans = [i for i, r in enumerate(doc_data[:5])
               if norm(r[0]) and not any(norm(x) for x in r[1:])]
    if orphans:
        print()
        print('发现孤儿标题行(表格 1-based 行号): %s' % [i + 2 for i in orphans])
        for i in sorted(orphans, reverse=True):
            r = call('sheet.delete_dimension', {
                'file_id': FILE_ID, 'sheet_id': SHEET_ID,
                'dimension_type': 'row', 'index': i + 1, 'count': 1,
            })
            print('  删除行 %d -> %s' % (i + 2, 'OK' if ok(r) else 'FAIL %s' % str(r)[:200]))
            if not ok(r):
                raise RuntimeError('删除孤儿行失败，终止，避免误伤')
            time.sleep(2)

    # ---- 2) 修正表头 A1（历史写入污染成了公告标题）----
    if norm(header[0]) != '公告标题':
        print()
        print('修正表头 A1: %r -> 公告标题' % norm(header[0])[:30])
        r = call('sheet.set_range_value', {
            'file_id': FILE_ID, 'sheet_id': SHEET_ID,
            'values': [{'row': 0, 'col': 0, 'value_type': 'STRING',
                        'string_value': '公告标题'}],
        })
        print('  -> %s' % ('OK' if ok(r) else 'FAIL %s' % str(r)[:200]))
        time.sleep(2)

    # ---- 3) 在第 2 行位置插入 N 行 ----
    print()
    print('在第 2 行位置插入 %d 行...' % len(todo))
    r = call('sheet.insert_dimension', {
        'file_id': FILE_ID, 'sheet_id': SHEET_ID,
        'dimension_type': 'row', 'index': 1, 'count': len(todo),
        'direction': 'before',
    })
    print('  -> %s' % ('OK' if ok(r) else 'FAIL %s' % str(r)[:300]))
    if not ok(r):
        raise RuntimeError('插入行失败，终止')
    time.sleep(3)

    # ---- 4) 写入数据 ----
    values = build_values(todo)
    print('写入单元格 %d 个...' % len(values))
    for attempt in range(3):
        r = call('sheet.set_range_value', {
            'file_id': FILE_ID, 'sheet_id': SHEET_ID, 'values': values,
        })
        if ok(r):
            print('  -> OK')
            break
        print('  -> FAIL(第%d次): %s' % (attempt + 1, str(r)[:200]))
        time.sleep(10 * (attempt + 1))
    else:
        raise RuntimeError('写入失败')

    print()
    print('补录完成，共 %d 条' % len(todo))


if __name__ == '__main__':
    main()
