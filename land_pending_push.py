# -*- coding: utf-8 -*-
"""
土地涉宅公告「已推送台账」机制 —— 根治漏报/重复推送。

背景（2026-09-24）：
  土地主任务 9/2~9/21 停摆 20 天（rrule 前缀 bug），9/22 被拒，9/23 "假成功"。
  期间 2026-09-21 三宗居住用地（黄浦/静安/浦东）进了 CSV 却从未推送微信。
  根因：推送判定依赖"本次抓取新增"或"发布日期==今天"，而数据可能由人工补跑、
  同步脚本等非推送路径悄悄写进 CSV，之后永远不会被推送。

机制：
  维护 data/land_pushed_keys.txt（每行一个去重键）。
  待推送 = CSV 中的涉宅公告 − 台账里已有的键。
  → 断档恢复、人工补跑、假成功漏推，都能在下次运行时自动补上，且绝不重复推送。

用法：
  python311 land_pending_push.py                      # 列出待推送涉宅公告
  python311 land_pending_push.py --json               # JSON 输出
  python311 land_pending_push.py --mark               # 把当前待推送标记为已推送（推送成功后调用）
  python311 land_pending_push.py --init --skip-date 2026-09-21   # 初始化台账：
        # 把 CSV 中全部涉宅公告视为"已处理"写入台账，但跳过指定日期（用于保留确认漏报的批次待补推）
"""
import csv, os, sys, json, io

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, 'land_monitor_results.csv')
KEY_FILE = os.path.join(BASE, 'data', 'land_pushed_keys.txt')

RESIDENTIAL_KEYWORDS = ['居住', '住宅', '商品房']


def load_csv():
    with io.open(CSV_PATH, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def make_key(row, hdr):
    def col(name):
        return row[hdr.index(name)] if name in hdr else ''
    return '|'.join([col('发布日期'), col('公告类型'), col('地块公告号'), col('地块名称')])


def load_keys():
    if not os.path.exists(KEY_FILE):
        return set()
    with io.open(KEY_FILE, encoding='utf-8') as f:
        return {ln.strip() for ln in f if ln.strip()}


def save_keys(keys):
    os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
    with io.open(KEY_FILE, 'w', encoding='utf-8') as f:
        for k in sorted(keys):
            f.write(k + '\n')


def is_residential(usage):
    return any(k in (usage or '') for k in RESIDENTIAL_KEYWORDS)


def main():
    args = sys.argv[1:]
    hdr, rows = load_csv()
    ui = hdr.index('土地用途')

    if '--init' in args:
        skip_dates = set()
        if '--skip-date' in args:
            i = args.index('--skip-date')
            skip_dates = {args[i + 1]}
        keys = load_keys()
        added = 0
        for r in rows:
            if r[1] in skip_dates:
                continue
            if is_residential(r[ui]):
                k = make_key(r, hdr)
                if k not in keys:
                    keys.add(k)
                    added += 1
        save_keys(keys)
        print('INIT_OK added=%d total=%d skip_date=%s' % (added, len(keys), ','.join(skip_dates) or '-'))
        return

    keys = load_keys()
    pending = [r for r in rows if is_residential(r[ui]) and make_key(r, hdr) not in keys]

    if '--mark' in args:
        for r in pending:
            keys.add(make_key(r, hdr))
        save_keys(keys)
        print('MARK_OK marked=%d total=%d' % (len(pending), len(keys)))
        return

    if '--json' in args:
        out = []
        for r in pending:
            d = {h: (r[i] if i < len(r) else '') for i, h in enumerate(hdr)}
            d['_key'] = make_key(r, hdr)
            out.append(d)
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return

    print('PENDING_COUNT %d' % len(pending))
    for r in sorted(pending, key=lambda x: x[1]):
        def col(n):
            return r[hdr.index(n)] if n in hdr and hdr.index(n) < len(r) else ''
        print('PENDING | %s | %s | %s | 容积率%s | 竞得人%s | 公告号%s' % (
            r[1], col('土地用途'), col('地块名称'), col('容积率'), col('竞得人'), col('地块公告号')))


if __name__ == '__main__':
    main()
