#!/usr/bin/env python3
"""
Generate budget morning report PNG — 单栏微信卡片版
- 宽度 750px，完全适配微信查看
- 自动数据校验 + 备份
- 支持所有分类
- emoji 用 Apple Color Emoji，中文用 MiSans，分离绘制
"""
import json, os, shutil, sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

WORKSPACE = os.path.expanduser("~/.openclaw/workspace/budget-tracker")
DATA_FILE = os.path.join(WORKSPACE, "budget-data.json")
REF_FILE  = os.path.join(WORKSPACE, "budget-config-reference.json")
OUTPUT_FILE = os.path.join(WORKSPACE, "budget_morning_report.png")

# ── 字体 ──
def get_font(size, bold=False):
    candidates = [
        ('/Users/mateng/Library/Fonts/MiSans-Demibold.ttf' if bold else None),
        '/Users/mateng/Library/Fonts/MiSans-Normal.ttf',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/PingFang.ttc',
    ]
    for path in candidates:
        if path:
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

def get_emoji_font(size):
    """emoji 专用字体"""
    try:
        return ImageFont.truetype('/System/Library/Fonts/Apple Color Emoji.ttc', size)
    except:
        return get_font(size)

# ── 数据校验与自动修复 ──
def validate_and_fix_data():
    if not os.path.exists(REF_FILE):
        print("[⚠️] 参考配置文件不存在，跳过校验", file=sys.stderr)
        with open(DATA_FILE) as f:
            return json.load(f)

    with open(REF_FILE) as f:
        ref = json.load(f)
    with open(DATA_FILE) as f:
        data = json.load(f)

    needs_fix = False
    errors = []

    if data.get('totalBudget') != ref.get('totalBudget'):
        errors.append(f"总预算 {data.get('totalBudget')} → {ref['totalBudget']}")
        data['totalBudget'] = ref['totalBudget']
        needs_fix = True

    ref_cats = {c['name']: c['limit'] for c in ref.get('categories', [])}
    curr_cats = {c['name']: c.get('limit', 0) for c in data.get('categories', [])}
    missing_in_curr = set(ref_cats.keys()) - set(curr_cats.keys())

    if missing_in_curr:
        errors.append(f"缺少分类: {missing_in_curr}")
        needs_fix = True

    for cat_name, ref_limit in ref_cats.items():
        for c in data['categories']:
            if c['name'] == cat_name and c.get('limit') != ref_limit:
                errors.append(f"{cat_name} 限额 {c.get('limit')} → {ref_limit}")
                c['limit'] = ref_limit
                needs_fix = True

    for cat_name in missing_in_curr:
        data.setdefault('categories', []).append({'name': cat_name, 'limit': ref_cats[cat_name]})

    if needs_fix:
        bak = DATA_FILE + f".bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(DATA_FILE, bak)
        print(f"[📦] 数据异常已修复，备份: {os.path.basename(bak)}", file=sys.stderr)
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("[✅] budget-data.json 已自动修复", file=sys.stderr)

    return data

# ── 配色 & 图标 ──
CAT_META = {
    "个人爱好者":     {"color": "#a78bfa", "bg": "#1a1233", "icon": "🎮"},
    "个人爱好":       {"color": "#a78bfa", "bg": "#1a1233", "icon": "🎮"},
    "好物购买":       {"color": "#22d3ee", "bg": "#0d1f24", "icon": "🛍️"},
    "鞋品":           {"color": "#f97316", "bg": "#1f1308", "icon": "👟"},
    "家庭幸福感好物": {"color": "#fb923c", "bg": "#1f1408", "icon": "🏠"},
    "餐饮":           {"color": "#fbbf24", "bg": "#1f1a08", "icon": "🍜"},
    "活动聚会":       {"color": "#f472b6", "bg": "#1f0c18", "icon": "🥂"},
    "交通":           {"color": "#60a5fa", "bg": "#0c1020", "icon": "🚗"},
    "其他":           {"color": "#6b7280", "bg": "#111",    "icon": "📦"},
}

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ── 圆角矩形 ──
def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    fill_rgb = hex_to_rgb(fill) if fill.startswith('#') else fill
    r = radius
    draw.rectangle([x1+r, y1, x2-r, y2], fill=fill_rgb)
    draw.rectangle([x1, y1+r, x2, y2-r], fill=fill_rgb)
    draw.pieslice([x1, y1, x1+2*r, y1+2*r], 180, 270, fill=fill_rgb)
    draw.pieslice([x2-2*r, y1, x2, y1+2*r], 270, 360, fill=fill_rgb)
    draw.pieslice([x1, y2-2*r, x1+2*r, y2], 90, 180, fill=fill_rgb)
    draw.pieslice([x2-2*r, y2-2*r, x2, y2], 0, 90, fill=fill_rgb)

# ── 绘制带 emoji 的文本行（emoji + 文字分离）─
def draw_mixed_text(draw, xy, emoji, text, emoji_font, text_font, fill):
    """先画 emoji，再画文字，自动衔接"""
    ex, ey = xy
    # emoji 部分
    draw.text((ex, ey), emoji, font=emoji_font, fill=fill)
    # 用 text_font 量一下文字宽度
    try:
        bbox = text_font.getbbox(text)
        tw = bbox[2]
    except:
        tw = len(text) * text_font.size * 0.6
    # 文字部分（紧接 emoji，略微偏下让视觉居中）
    tex = ex + int(emoji_font.size * 0.85)
    # 小字体文字略低于 emoji 视觉中心
    tey = ey + int(emoji_font.size * 0.15)
    draw.text((tex, tey), text, font=text_font, fill=fill)
    return tex + tw

def render_report():
    data = validate_and_fix_data()
    cats = data.get("categories", [])
    expenses = data.get("expenses", [])
    total_budget = data.get("totalBudget", 0)

    cat_spent = {}
    for e in expenses:
        cat_spent[e["category"]] = cat_spent.get(e["category"], 0) + e["amount"]

    active_cats = [c for c in cats if c.get("limit", 0) > 0 or cat_spent.get(c["name"], 0) > 0]
    total_limit = sum(c["limit"] for c in active_cats) or total_budget
    total_spent = sum(cat_spent.get(c["name"], 0) for c in active_cats)
    remaining = total_limit - total_spent
    pct = min(100, int(total_spent / total_limit * 100)) if total_limit > 0 else 0

    month_str = datetime.now().strftime("%Y年%m月")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── 颜色 ──
    BG    = "#0a0a14"; CARD  = "#12122a"; DARK  = "#1e1e40"
    GRAY  = "#666666"; LGRAY = "#888888"; WHITE = "#ffffff"
    BLUE  = "#22d3ee"; GREEN = "#4ade80"; RED   = "#f87171"

    W = 750
    PADDING = 40

    # ── 高度计算 ──
    HEADER_H  = 100; HERO_H = 210; CAT_H = 92; TXN_H = 68
    FOOTER_H  = 80
    cat_sec   = len(active_cats) * CAT_H + 60
    txn_sec   = (min(len(expenses), 8) * TXN_H + 60) if expenses else 60
    H = PADDING + HEADER_H + HERO_H + 30 + cat_sec + 20 + txn_sec + 30 + FOOTER_H

    img  = Image.new("RGB", (W, int(H)), BG)
    draw = ImageDraw.Draw(img)

    # 预加载字体
    f16   = get_font(16)
    f12   = get_font(12)
    f20b  = get_font(20, bold=True)
    f26b  = get_font(26, bold=True)
    f14b  = get_font(14, bold=True)
    f13   = get_font(13)
    f11   = get_font(11)
    f10   = get_font(10)
    f18b  = get_font(18, bold=True)
    emoji_f20 = get_emoji_font(20)
    emoji_f17 = get_emoji_font(17)
    emoji_f16 = get_emoji_font(16)

    y = PADDING

    # ══ 1. 标题栏 ══
    draw.rectangle((0, 0, W, HEADER_H + 20), fill="#0d0d1f")
    draw.text((40, 28), "📊 小马哥月度预算", font=f26b, fill=WHITE)
    draw.text((40, 60), f"{month_str} · {now_str}", font=f13, fill=GRAY)
    draw.text((W - 160, 36), f"{len(expenses)}笔消费", font=f13, fill=LGRAY)

    y = HEADER_H + 30

    # ══ 2. Hero 总览卡片 ══
    draw_rounded_rect(draw, (PADDING, y, W - PADDING, y + HERO_H), 20, CARD)

    # 环形图
    cx, cy = 110, y + HERO_H // 2; r = 52
    draw.arc((cx-r, cy-r, cx+r, cy+r), 0, 360, fill=DARK, width=14)
    if pct > 0:
        draw.arc((cx-r, cy-r, cx+r, cy+r), -90, -90 + int(360*pct/100),
                 fill=BLUE if remaining >= 0 else RED, width=14)
    # 环形内 emoji 百分比（用 emoji 字体）
    draw.text((cx - 18, cy - 22), f"{pct}%", font=f26b, fill=WHITE)
    draw.text((cx - 16, cy + 10), "消耗", font=f12, fill=GRAY)

    # 三个数字
    rx = 220
    for label, val, col in [
        ("总预算", f"¥{total_limit:,}", LGRAY),
        ("已消耗", f"¥{total_spent:,}", WHITE),
    ]:
        draw.text((rx, y + 30), label, font=f12, fill=col)
        draw.text((rx, y + 56), val,    font=f20b, fill=col)
        rx += 150

    # 剩余
    rem_label = "剩余可支配" if remaining >= 0 else "⚠️ 已超支"
    rem_val   = (f"¥{remaining:,}" if remaining >= 0 else f"-¥{-remaining:,}")
    rem_col   = GREEN if remaining >= 0 else RED
    draw.text((rx, y + 30), rem_label, font=f12, fill=rem_col)
    draw.text((rx, y + 56), rem_val,   font=f20b, fill=rem_col)

    y += HERO_H + 30

    # ══ 3. 预算分类 ══
    draw.text((PADDING, y), "📂 预算分类", font=f13, fill=GRAY)
    y += 36

    for c in active_cats:
        name  = c["name"]
        limit = c["limit"]
        spent = cat_spent.get(name, 0)
        pct2  = min(100, int(spent / limit * 100)) if limit > 0 else 0
        is_over = limit > 0 and spent > limit
        meta  = CAT_META.get(name, {"color": "#6366f1", "bg": "#12122a", "icon": "📦"})
        col_hex = meta["color"]
        icon_bg = hex_to_rgb(meta["bg"])

        draw_rounded_rect(draw, (PADDING, y, W - PADDING, y + CAT_H - 10), 16, CARD)

        # emoji 图标圆底
        draw.ellipse((PADDING + 10, y + 14, PADDING + 50, y + 54), fill=icon_bg)
        draw.text((PADDING + 17, y + 17), meta["icon"], font=emoji_f20)

        # 分类名 + 限额
        draw.text((PADDING + 66, y + 12), name,  font=f14b, fill=WHITE)
        draw.text((PADDING + 66, y + 38), f"预算 ¥{limit:,}", font=f11, fill=GRAY)

        # 已用金额
        spent_col = RED if is_over else WHITE
        over_info = f"超¥{spent - limit:,}" if is_over else f"剩¥{limit - spent:,}"
        draw.text((W - PADDING - 120, y + 12), f"¥{spent:,}",   font=f18b, fill=spent_col)
        draw.text((W - PADDING - 120, y + 36), over_info, font=f11, fill=GRAY)

        # 进度条
        bar_x = PADDING + 66; bar_y = y + CAT_H - 20
        bar_w = W - PADDING - 66 - PADDING - 130; bar_h = 8
        draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), 4, DARK)
        if pct2 > 0:
            fw = int(bar_w * min(pct2, 100) / 100)
            draw_rounded_rect(draw, (bar_x, bar_y, bar_x + fw, bar_y + bar_h), 4, col_hex)

        y += CAT_H

    y += 20

    # ══ 4. 最新消费 ══
    draw.text((PADDING, y), "🧾 最新消费", font=f13, fill=GRAY)
    y += 36

    if not expenses:
        draw_rounded_rect(draw, (PADDING, y, W - PADDING, y + 60), 16, CARD)
        draw.text((W//2 - 60, y + 20), "暂无消费记录", font=f14b, fill=GRAY)
        y += 80
    else:
        for e in expenses[-8:]:
            name  = e["category"]
            meta  = CAT_META.get(name, {"color": "#6366f1", "bg": "#12122a", "icon": "📦"})
            note  = e.get("note", "")
            date_str = e.get("date", "")[5:]
            amt  = e["amount"]
            icon_bg = hex_to_rgb(meta["bg"])

            draw_rounded_rect(draw, (PADDING, y, W - PADDING, y + TXN_H - 8), 16, CARD)

            # emoji 图标
            draw.ellipse((PADDING + 10, y + 12, PADDING + 44, y + 46), fill=icon_bg)
            draw.text((PADDING + 15, y + 15), meta["icon"], font=emoji_f16)

            # 分类名
            draw.text((PADDING + 56, y + 8),  name, font=f14b, fill=WHITE)
            if note:
                note_disp = note if len(note) <= 14 else note[:14] + "…"
                draw.text((PADDING + 56, y + 30), note_disp, font=f11, fill=GRAY)

            # 金额 + 时间
            draw.text((W - PADDING - 110, y + 12), f"-¥{amt:,}", font=f16, fill=WHITE)
            draw.text((W - PADDING - 110, y + 34), date_str, font=f11, fill=GRAY)

            y += TXN_H

    y += 30

    # ══ 5. 底部 ══
    draw.rectangle((0, int(y), W, int(y) + FOOTER_H + 20), fill="#0d0d1f")
    draw.text((W//2 - 140, int(y) + 20),
              f"更新于 {now_str}  ·  预算追踪器", font=f11, fill="#333333")
    draw.text((W//2 - 100, int(y) + 44),
              "数据：~/.openclaw/workspace/budget-tracker/", font=f10, fill="#222222")

    # ── 保存 ──
    img.save(OUTPUT_FILE, quality=95)
    hires = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    hires.save(OUTPUT_FILE.replace('.png', '_hires.png'), quality=95)

    size_kb = os.path.getsize(OUTPUT_FILE) // 1024
    print(f"✅ 生成成功: {OUTPUT_FILE} ({img.width}x{img.height}, {size_kb}KB)")

if __name__ == "__main__":
    render_report()
