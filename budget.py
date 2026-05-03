#!/usr/bin/env python3
"""
轻记·月度预算追踪器
用法：
  python3 budget.py add "买了鞋1200"
  python3 budget.py status
  python3 budget.py set 类别 金额
  python3 budget.py reset
"""

import json
import sys
import os
from datetime import datetime

DATA_FILE = os.path.expanduser("~/.openclaw/workspace/budget-tracker/budget-data.json")

DEFAULT_CATEGORIES = ["个人爱好", "活动聚会", "鞋品", "餐饮", "交通", "其他"]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "totalBudget": 0,
        "categories": [{"name": c, "limit": 0} for c in DEFAULT_CATEGORIES],
        "expenses": []
    }

def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def parse_expense(text):
    """从自然语言提取金额和类别"""
    import re
    # 提取数字（金额）
    numbers = re.findall(r'\d+', text)
    if not numbers:
        return None, None
    amount = max(int(n) for n in numbers)  # 取最大数字作为金额

    # 类别关键词匹配
    text_lower = text.lower()
    category_map = {
        "个人爱好": ["爱好", "手办", "游戏", "电子产品", "数码", "相机"],
        "活动聚会": ["聚餐", "聚会", "活动", "party", "派对", "社交"],
        "鞋品": ["鞋", "球鞋", "运动鞋", "皮鞋"],
        "餐饮": ["饭", "吃", "餐饮", "外卖", "餐厅", "咖啡", "奶茶"],
        "交通": ["交通", "打车", "地铁", "公交", "机票", "火车", "油", "停车"],
    }
    for cat, keywords in category_map.items():
        for kw in keywords:
            if kw in text:
                return amount, cat
    return amount, "其他"

def add_expense(amount, category, note=""):
    data = load_data()
    expense = {
        "id": len(data["expenses"]) + 1,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": category,
        "amount": amount,
        "note": note
    }
    data["expenses"].append(expense)
    save_data(data)
    return expense

def get_status():
    data = load_data()
    total = data["totalBudget"]
    expenses = data["expenses"]

    # 计算已消费
    total_spent = sum(e["amount"] for e in expenses)
    remaining = total - total_spent

    # 按类别统计
    cat_spent = {}
    for e in expenses:
        cat_spent[e["category"]] = cat_spent.get(e["category"], 0) + e["amount"]

    # 各类别状态
    cat_status = []
    for cat in data["categories"]:
        limit = cat["limit"]
        spent = cat_spent.get(cat["name"], 0)
        pct = (spent / limit * 100) if limit > 0 else 0
        cat_status.append({
            "name": cat["name"],
            "limit": limit,
            "spent": spent,
            "remaining": max(0, limit - spent),
            "pct": round(pct, 1),
            "over": spent > limit if limit > 0 else False
        })

    return {
        "totalBudget": total,
        "totalSpent": total_spent,
        "remaining": remaining,
        "categories": cat_status,
        "recentExpenses": expenses[-5:] if expenses else []
    }

def cmd_add(text):
    amount, cat = parse_expense(text)
    if amount is None:
        print("❌ 无法识别金额，请输入数字")
        return
    exp = add_expense(amount, cat, text)
    status = get_status()
    print(f"✅ 已记：{exp['category']} ¥{amount}")
    print(f"   剩余总预算：¥{status['remaining']}")

def cmd_status():
    s = get_status()
    print(f"\n📊 {datetime.now().strftime('%Y年%m月')} 预算状态")
    print(f"总预算：¥{s['totalBudget']} | 已消耗：¥{s['totalSpent']} | 剩余：¥{s['remaining']}")
    print()
    for c in s["categories"]:
        bar_len = 20
        filled = min(int(c['pct'] / 100 * bar_len), bar_len) if c['limit'] > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)
        flag = " ⚠️ 超支" if c['over'] else ""
        limit_str = f"/¥{c['limit']}" if c['limit'] > 0 else ""
        print(f"  {c['name']:6s} {bar} ¥{c['spent']}{limit_str}{flag}")
    if s["recentExpenses"]:
        print("\n最近记录：")
        for e in reversed(s["recentExpenses"][-3:]):
            print(f"  {e['date'][-5:]} {e['category']} ¥{e['amount']}")

def cmd_set_total(amount):
    data = load_data()
    data["totalBudget"] = amount
    save_data(data)
    print(f"✅ 总预算已设置为 ¥{amount}")

def cmd_set_cat(cat_name, limit):
    data = load_data()
    for c in data["categories"]:
        if c["name"] == cat_name:
            c["limit"] = limit
            save_data(data)
            print(f"✅ {cat_name} 预算上限已设为 ¥{limit}")
            return
    print(f"❌ 未找到类别：{cat_name}")

def cmd_add_cat(cat_name):
    data = load_data()
    if any(c["name"] == cat_name for c in data["categories"]):
        print(f"⚠️ 类别 {cat_name} 已存在")
        return
    data["categories"].append({"name": cat_name, "limit": 0})
    save_data(data)
    print(f"✅ 已添加类别：{cat_name}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
    elif args[0] == "add":
        cmd_add(" ".join(args[1:]))
    elif args[0] == "status":
        cmd_status()
    elif args[0] == "set-total":
        cmd_set_total(int(args[1]))
    elif args[0] == "set-cat":
        cmd_set_cat(args[1], int(args[2]))
    elif args[0] == "add-cat":
        cmd_add_cat(args[1])
    elif args[0] == "reset":
        data = load_data()
        data["expenses"] = []
        save_data(data)
        print("✅ 已重置本月消费记录（保留预算设置）")
    else:
        print(f"未知命令：{args[0]}")
        print(__doc__)