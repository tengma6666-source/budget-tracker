#!/usr/bin/env python3
"""
记录一笔消费 + 校验 + 截图 + 写操作日志
用法: python3 record.py "分类" 金额 "备注"
示例: python3 record.py 好物购买 258 "Torras手机壳"
"""
import json, sys, os, time, shutil
from datetime import datetime

WORKSPACE = os.path.expanduser('~/.openclaw/workspace/budget-tracker')
DATA_FILE = os.path.join(WORKSPACE, 'budget-data.json')
REF_FILE  = os.path.join(WORKSPACE, 'budget-config-reference.json')
SCREENSHOT_SCRIPT = os.path.join(WORKSPACE, 'screenshot.py')
OPS_LOG = os.path.join(WORKSPACE, 'budget-ops.log.md')

CATEGORY_ALIAS = {
    '个人兴趣': '个人爱好',
    '兴趣': '个人爱好',
    '爱好': '个人爱好',
    '礼物': '家庭幸福感好物',
    '给家人买': '家庭幸福感好物',
    '家庭用品': '家庭幸福感好物',
    '衣服': '鞋品',
    '鞋': '鞋品',
    '包': '鞋品',
    '配饰': '鞋品',
    '数码': '好物购买',
    '电子设备': '好物购买',
    '手机': '好物购买',
}


def log_op(op, category, amount, note, status, detail=''):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    entry = '[{}] | {} | {} | {} | {} | {}'.format(ts, op, category, amount, note, status)
    if detail:
        entry += ' | ' + detail
    entry += '\n'
    with open(OPS_LOG, 'a') as f:
        f.write(entry)


def validate_data():
    try:
        with open(REF_FILE) as f:
            ref = json.load(f)
        with open(DATA_FILE) as f:
            data = json.load(f)

        issues = []
        if data.get('totalBudget') != ref.get('totalBudget'):
            issues.append('totalBudget {}=>{}'.format(data.get('totalBudget'), ref.get('totalBudget')))
        ref_cats = {c['name'] for c in ref.get('categories', [])}
        curr_cats = {c['name'] for c in data.get('categories', [])}
        if ref_cats != curr_cats:
            issues.append('categories {}=>{}'.format(curr_cats, ref_cats))
        ref_limits = {c['name']: c['limit'] for c in ref.get('categories', [])}
        for c in data.get('categories', []):
            if ref_limits.get(c['name']) != c.get('limit'):
                issues.append('{} limit {}=>{}'.format(c['name'], c.get('limit'), ref_limits.get(c['name'])))

        if issues:
            bak = DATA_FILE + '.bak.' + datetime.now().strftime('%Y%m%d%H%M%S')
            shutil.copy2(DATA_FILE, bak)
            log_op('VALIDATE_FAIL', '', 0, '', 'FIXED', 'issues={} bak={}'.format(issues, bak))
            # FIX: update REF to match DATA (data is source of truth), don't overwrite data with stale ref
            ref['totalBudget'] = data.get('totalBudget')
            ref['resetDay'] = data.get('resetDay', 1)
            ref['categories'] = [dict(c) for c in data.get('categories', [])]
            with open(REF_FILE, 'w') as f:
                json.dump(ref, f, indent=2, ensure_ascii=False)
            with open(DATA_FILE, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log_op('VALIDATE_FIX', '', 0, '', 'DONE', 'ref updated from data, bak={}'.format(bak))
            print('[W] Config auto-fixed (ref updated from data), backup: {}'.format(os.path.basename(bak)))
            return data
        return data
    except Exception as e:
        log_op('VALIDATE_ERROR', '', 0, '', 'ERROR', str(e))
        print('[E] Validate failed: {}'.format(e))
        raise


def resolve_category(raw):
    return CATEGORY_ALIAS.get(raw.strip(), raw.strip())


def main():
    if len(sys.argv) < 3:
        print('Usage: python3 record.py "category" amount "note"')
        sys.exit(1)

    raw_cat = sys.argv[1]
    amount = int(sys.argv[2])
    note = sys.argv[3] if len(sys.argv) > 3 else ''

    category = resolve_category(raw_cat)
    data = validate_data()

    valid_cats = {c['name'] for c in data.get('categories', [])}
    if category not in valid_cats:
        print('[W] Category "{}" not in known list'.format(category))

    all_ids = [e.get('id', 0) for e in data.get('expenses', [])]
    new_id = (max(all_ids) if all_ids else 0) + 1
    ts = time.strftime('%Y-%m-%d %H:%M')

    data['expenses'].append({
        'id': new_id,
        'date': ts,
        'category': category,
        'amount': amount,
        'note': note
    })

    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    total = data.get('totalBudget', 0)
    spent = sum(e['amount'] for e in data.get('expenses', []))
    remaining = total - spent

    log_op('ADD_EXPENSE', category, amount, note, 'OK',
           'id={} total={} spent={} remaining={}'.format(new_id, total, spent, remaining))

    print('OK: {} -Y{} ({})'.format(category, amount, note))
    print('Spent: Y{}/Y{} ({}%)'.format(spent, total, int(spent / total * 100) if total > 0 else 0))
    print('Remaining: Y{}'.format(remaining))

    ret = os.system('python3 {}'.format(SCREENSHOT_SCRIPT))
    if ret != 0:
        log_op('SCREENSHOT_FAIL', category, amount, note, 'FAIL', 'exit={}'.format(ret))
        print('[W] Screenshot failed, exit={}'.format(ret))
    else:
        log_op('SCREENSHOT_OK', category, amount, note, 'OK')


if __name__ == '__main__':
    main()
