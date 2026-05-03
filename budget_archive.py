#!/usr/bin/env python3
"""
每月预算归档脚本
- 每月1日自动运行，将上月数据存档
- 保留所有历史数据用于月度对比分析
"""
import json, os, sys
from datetime import datetime

WORKSPACE = os.path.expanduser('~/.openclaw/workspace/budget-tracker')
DATA_FILE = os.path.join(WORKSPACE, 'budget-data.json')
ARCHIVE_DIR = os.path.join(WORKSPACE, 'archives')
os.makedirs(ARCHIVE_DIR, exist_ok=True)


def get_data_month(data):
    expenses = data.get('expenses', [])
    if not expenses:
        return None
    return expenses[0].get('date', '')[:7]  # YYYY-MM


def archive_current_month():
    with open(DATA_FILE) as f:
        data = json.load(f)

    month = get_data_month(data)
    if not month:
        print('No expenses found, skipping archive')
        return

    archive_file = os.path.join(ARCHIVE_DIR, f'budget-{month}.json')
    if os.path.exists(archive_file):
        print(f'{month} already archived')
        return

    cat_spent = {}
    for e in data.get('expenses', []):
        cat_spent[e['category']] = cat_spent.get(e['category'], 0) + e['amount']

    total = data.get('totalBudget', 0)
    total_spent = sum(cat_spent.values())

    archive_entry = {
        'month': month,
        'archivedAt': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'totalBudget': total,
        'totalSpent': total_spent,
        'remaining': total - total_spent,
        'categories': [{**c, 'spent': cat_spent.get(c['name'], 0)} for c in data.get('categories', [])],
        'expenses': data.get('expenses', [])
    }

    with open(archive_file, 'w') as f:
        json.dump(archive_entry, f, indent=2, ensure_ascii=False)

    print(f'Archived {month}: spent {total_spent} / {total}')


def list_archives():
    archives = sorted(os.listdir(ARCHIVE_DIR))
    print(f'{len(archives)} months archived:')
    for f in archives:
        print(f'  {f}')


def compare_months(m1=None, m2=None):
    archives = sorted(os.listdir(ARCHIVE_DIR))
    if len(archives) < 2:
        print('Need at least 2 months for comparison')
        return

    if not m1:
        m1 = archives[-2]
    if not m2:
        m2 = archives[-1]

    d1 = json.load(open(os.path.join(ARCHIVE_DIR, m1)))
    d2 = json.load(open(os.path.join(ARCHIVE_DIR, m2)))

    print(f'Monthly comparison: {m1} vs {m2}')
    print(f'{"":<16} {m1:<12} {m2:<12}')
    print(f'{"Total Spent":<16} {d1["totalSpent"]:>10}    {d2["totalSpent"]:>10}')
    print(f'{"Remaining":<16} {d1["remaining"]:>10}    {d2["remaining"]:>10}')

    cats1 = {c['name']: c['spent'] for c in d1.get('categories', [])}
    cats2 = {c['name']: c['spent'] for c in d2.get('categories', [])}
    all_cats = set(cats1.keys()) | set(cats2.keys())
    for cat in sorted(all_cats):
        s1 = cats1.get(cat, 0)
        s2 = cats2.get(cat, 0)
        diff = s2 - s1
        arrow = '+' if diff > 0 else '-' if diff < 0 else '='
        print(f'{cat:<16} {s1:>10}  {arrow} {s2:>10}')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'archive':
        archive_current_month()
    elif cmd == 'list':
        list_archives()
    elif cmd == 'compare':
        compare_months(sys.argv[2] if len(sys.argv) > 2 else None,
                       sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd == 'check':
        with open(DATA_FILE) as f:
            data = json.load(f)
        month = get_data_month(data)
        current = datetime.now().strftime('%Y-%m')
        if month and month != current:
            print(f'Data belongs to {month}, archiving before reset')
            archive_current_month()
        else:
            print(f'Data is current ({month or "empty"}), no archive needed')
    else:
        print('Usage: budget_archive.py [archive|list|compare|check]')