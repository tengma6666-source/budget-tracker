#!/usr/bin/env python3
"""
Dashboard 服务 — 稳定版
提供 budget-data.json 的动态读取 + 自动刷新
"""
import json, os, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import atexit

WORKSPACE = os.path.expanduser("~/.openclaw/workspace/budget-tracker")
DATA_FILE = os.path.join(WORKSPACE, "budget-data.json")
PORT = 8765

# ── 保活 ──
_proc_pid = None

def load_data():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e), "totalBudget": 0, "categories": [], "expenses": []}

def render_dashboard():
    data = load_data()
    cats = data.get("categories", [])
    expenses = data.get("expenses", [])
    total = data.get("totalBudget", 0)

    cat_spent = {}
    for e in expenses:
        cat_spent[e["category"]] = cat_spent.get(e["category"], 0) + e["amount"]

    active_cats = [c for c in cats if c.get("limit", 0) > 0 or cat_spent.get(c["name"], 0) > 0]
    total_limit = sum(c["limit"] for c in active_cats) or total
    total_spent = sum(cat_spent.get(c["name"], 0) for c in active_cats)
    remaining = total_limit - total_spent
    pct = min(100, int(total_spent / total_limit * 100)) if total_limit > 0 else 0
    is_over = remaining < 0

    recent = list(reversed(expenses))[:8]

    # 计算页面高度
    hero_h = 200
    cat_h = 82
    txn_h = 60
    header_h = 70
    footer_h = 60
    sections_h = 80
    page_h = header_h + sections_h + hero_h + 20 + len(active_cats) * cat_h + 20 + len(recent) * txn_h + footer_h + 40

    cat_rows = ""
    for c in active_cats:
        name = c["name"]
        limit = c["limit"]
        spent = cat_spent.get(name, 0)
        pct2 = min(100, int(spent / limit * 100)) if limit > 0 else 0
        is_over_cat = limit > 0 and spent > limit

        bar_color = "#f87171" if is_over_cat else CAT_COLORS.get(name, "#6366f1")
        status_txt = f'<span class="badge over">超¥{spent-limit:,}</span>' if is_over_cat else f'<span class="badge ok">剩¥{limit-spent:,}</span>'
        icon = CAT_ICONS.get(name, "📦")

        cat_rows += f"""
        <div class="cat-item">
          <div class="cat-icon" style="background:{CAT_BG.get(name,'#12122a')}">{icon}</div>
          <div class="cat-info">
            <div class="cat-name">{name}</div>
            <div class="cat-budget">预算 ¥{limit:,}</div>
            <div class="progress-bar"><div class="progress-bar-fill" style="width:{pct2}%;background:{bar_color}"></div></div>
          </div>
          <div class="cat-right">
            <div class="cat-amount" style="color:{'#f87171' if is_over_cat else '#fff'}">¥{spent:,}</div>
            {status_txt}
          </div>
        </div>"""

    txn_rows = ""
    for e in recent:
        name = e["category"]
        icon = CAT_ICONS.get(name, "📦")
        date = e.get("date", "")[5:]
        note = e.get("note", "")
        amt = e["amount"]
        txn_rows += f"""
        <div class="txn-item">
          <div class="txn-icon" style="background:{CAT_BG.get(name,'#12122a')}">{icon}</div>
          <div class="txn-info">
            <div class="txn-cat">{name}</div>
            <div class="txn-note">{note}</div>
          </div>
          <div class="txn-right">
            <div class="txn-amount">-¥{amt:,}</div>
            <div class="txn-date">{date}</div>
          </div>
        </div>"""

    update_time = time.strftime("%Y-%m-%d %H:%M")
    rem_color = "#4ade80" if remaining >= 0 else "#f87171"
    ring_color = "#22d3ee" if remaining >= 0 else "#f87171"

    # SVG 圆环
    circumference = 2 * 3.14159 * 42
    offset = circumference * (1 - pct / 100)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>小马哥预算追踪</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
  background: #0a0a14; color: #fff;
  min-height: 100vh; padding: 0 0 60px;
  max-width: 750px; margin: 0 auto;
}}
/* ── Header ── */
.header {{
  background: #0d0d1f; padding: 16px 20px;
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid #1c1c38;
  position: sticky; top: 0; z-index: 100;
}}
.header-title {{ font-size: 18px; font-weight: 700; }}
.live-dot {{
  display: inline-block; width: 8px; height: 8px;
  background: #4ade80; border-radius: 50%;
  margin-right: 6px; vertical-align: middle;
  animation: blink 2s infinite;
}}
@keyframes blink {{ 0%,100% {{ opacity:1 }} 50% {{ opacity: 0.4 }} }}
.header-time {{ font-size: 12px; color: #555; }}

/* ── Hero ── */
.hero {{ background: #12122a; margin: 16px; border-radius: 20px; padding: 20px; display: flex; align-items: center; gap: 24px; }}
.ring-wrap {{ text-align: center; flex-shrink: 0; position: relative; }}
.ring-svg {{ width: 110px; height: 110px; }}
.ring-label {{ font-size: 10px; color: #444; letter-spacing: 1px; margin-top: 4px; }}
.hero-info {{ flex: 1; min-width: 0; }}
.hero-remain {{ font-size: 30px; font-weight: 800; color: {rem_color}; line-height: 1.1; }}
.hero-sub {{ font-size: 12px; color: #555; margin-top: 6px; }}
.hero-stats {{ display: flex; justify-content: space-between; margin-top: 16px; }}
.hero-stat {{ text-align: center; flex: 1; }}
.hero-stat-label {{ font-size: 10px; color: #444; letter-spacing: 1px; margin-bottom: 4px; }}
.hero-stat-value {{ font-size: 16px; font-weight: 700; }}
.hero-stat-value.gray {{ color: #666; }}
.hero-stat-value.white {{ color: #fff; }}
.hero-stat-value.green {{ color: #4ade80; }}
.hero-stat-value.cyan {{ color: #22d3ee; }}
/* ── Section ── */
.section-title {{ font-size: 11px; color: #444; letter-spacing: 2px; padding: 8px 20px 8px; text-transform: uppercase; }}
/* ── Category ── */
.section {{ background: #12122a; margin: 0 16px 12px; border-radius: 16px; padding: 4px 0; }}
.cat-item {{ display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid #1c1c38; }}
.cat-item:last-child {{ border-bottom: none; }}
.cat-icon {{ width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }}
.cat-info {{ flex: 1; min-width: 0; }}
.cat-name {{ font-size: 14px; font-weight: 600; color: #ddd; }}
.cat-budget {{ font-size: 11px; color: #555; margin-top: 2px; }}
.progress-bar {{ height: 5px; background: #1c1c38; border-radius: 3px; margin-top: 6px; overflow: hidden; }}
.progress-bar-fill {{ height: 100%; border-radius: 3px; transition: width 0.6s ease; }}
.cat-right {{ text-align: right; flex-shrink: 0; margin-left: 8px; }}
.cat-amount {{ font-size: 16px; font-weight: 700; }}
.cat-remaining {{ font-size: 10px; color: #555; margin-top: 2px; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; }}
.badge.over {{ background: rgba(248,113,113,0.2); color: #f87171; }}
.badge.ok {{ background: rgba(74,222,128,0.15); color: #4ade80; }}
/* ── Transaction ── */
.txn-item {{ display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-bottom: 1px solid #1c1c38; }}
.txn-item:last-child {{ border-bottom: none; }}
.txn-icon {{ width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }}
.txn-info {{ flex: 1; min-width: 0; }}
.txn-cat {{ font-size: 13px; font-weight: 600; color: #ccc; }}
.txn-note {{ font-size: 11px; color: #555; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }}
.txn-right {{ text-align: right; flex-shrink: 0; }}
.txn-amount {{ font-size: 14px; font-weight: 700; }}
.txn-date {{ font-size: 10px; color: #444; margin-top: 2px; }}
/* ── Footer ── */
.footer {{ text-align: center; padding: 20px; font-size: 11px; color: #333; }}
.notice {{ background: #1a1a3a; margin: 0 16px 12px; border-radius: 12px; padding: 10px 16px; font-size: 12px; color: #555; text-align: center; }}
/* ── Over budget alert ── */
.alert {{ background: rgba(248,113,113,0.12); margin: 0 16px 12px; border-radius: 12px; padding: 10px 16px; font-size: 12px; color: #f87171; text-align: center; border: 1px solid rgba(248,113,113,0.2); }}
</style>
</head>
<body>

<div class="header">
  <div class="header-title">📊 小马哥月度预算</div>
  <div class="header-time"><span class="live-dot"></span>实时更新</div>
</div>

<div class="notice">💡 数据每5秒自动刷新 · 无需网络持续查看</div>
{f'<div class="alert">⚠️ 整体预算已超支！</div>' if is_over else ''}

<div class="hero">
  <div class="ring-wrap">
    <svg class="ring-svg" viewBox="0 0 110 110" xmlns="http://www.w3.org/2000/svg">
      <circle cx="55" cy="55" r="42" fill="none" stroke="#1c1c38" stroke-width="10"/>
      <circle cx="55" cy="55" r="42" fill="none" stroke="{ring_color}" stroke-width="10" stroke-linecap="round"
        stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}"
        transform="rotate(-90 55 55)"/>
      <text x="55" y="50" text-anchor="middle" fill="white" font-size="20" font-weight="700" font-family="-apple-system,sans-serif">{pct}%</text>
      <text x="55" y="66" text-anchor="middle" fill="#555" font-size="10" font-family="-apple-system,sans-serif">消耗</text>
    </svg>
    <div class="ring-label">OVERALL</div>
  </div>
  <div class="hero-info">
    <div class="hero-remain">{'¥' + f'{remaining:,}' if remaining >= 0 else '-¥' + f'{-remaining:,}'}</div>
    <div class="hero-sub">{'剩余可支配' if remaining >= 0 else '⚠️ 已超支'}</div>
    <div class="hero-stats">
      <div class="hero-stat"><div class="hero-stat-label">总预算</div><div class="hero-stat-value gray">¥{total_limit:,}</div></div>
      <div class="hero-stat"><div class="hero-stat-label">已消耗</div><div class="hero-stat-value white">¥{total_spent:,}</div></div>
      <div class="hero-stat"><div class="hero-stat-label">剩余</div><div class="hero-stat-value green">{'¥' + f'{remaining:,}' if remaining >= 0 else '-¥' + f'{-remaining:,}'}</div></div>
    </div>
  </div>
</div>

<div class="section-title">📂 预算分类</div>
<div class="section">{cat_rows}</div>

<div class="section-title">🧾 最新消费</div>
<div class="section">{txn_rows}</div>

<div class="footer">
  更新于 {update_time} · 预算追踪器<br>
  数据来源：本地 budget-data.json
</div>

<script>
// 每5秒刷新数据
async function reload() {{
  const r = await fetch('budget-data.json');
  if (!r.ok) return;
  const d = await r.json();
  // 数据未变则不刷新页面
  window._lastHash = window._lastHash || '';
  const h = JSON.stringify([d.totalBudget, d.categories, d.expenses]);
  if (h !== window._lastHash) {{
    window._lastHash = h;
    location.reload();
  }}
}}
setInterval(reload, 5000);
</script>
</body>
</html>"""
    return html

# ── Cat 颜色映射 ──
CAT_COLORS = {
    "个人爱好":       "#a78bfa",
    "好物购买":       "#22d3ee",
    "鞋品":           "#f97316",
    "家庭幸福感好物": "#fb923c",
    "餐饮":           "#fbbf24",
    "活动聚会":       "#f472b6",
    "交通":           "#60a5fa",
    "其他":           "#6b7280",
}
CAT_BG = {
    "个人爱好":       "#1a1233",
    "好物购买":       "#0d1f24",
    "鞋品":           "#1f1308",
    "家庭幸福感好物": "#1f1408",
    "餐饮":           "#1f1a08",
    "活动聚会":       "#1f0c18",
    "交通":           "#0c1020",
    "其他":           "#111111",
}
CAT_ICONS = {
    "个人爱好":       "🎮",
    "好物购买":       "🛍️",
    "鞋品":           "👟",
    "家庭幸福感好物": "🏠",
    "餐饮":           "🍜",
    "活动聚会":       "🥂",
    "交通":           "🚗",
    "其他":           "📦",
}

# ── 静态文件服务器（动态 dashboard） ──
class DynamicHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE, **kwargs)

    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard.html' or self.path == '/index.html':
            content = render_dashboard().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/budget-data.json':
            with open(DATA_FILE) as f:
                data = f.read().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)
        else:
            super().do_GET()

    def log_message(self, format, *args):
        pass  # 静默日志

def start_server(port=PORT):
    global _proc_pid
    while True:
        try:
            server = HTTPServer(('0.0.0.0', port), DynamicHandler)
            print(f"✅ Dashboard 服务运行中: http://localhost:{port}/dashboard.html")
            _proc_pid = os.getpid()
            server.serve_forever()
        except Exception as e:
            print(f"⚠️ 服务中断: {e}，3秒后重启…")
            time.sleep(3)

def keep_alive():
    """保活入口 — 从 shell 调用"""
    while True:
        try:
            pid_file = os.path.join(WORKSPACE, "dashboard.pid")
            pid = int(open(pid_file).read().strip()) if os.path.exists(pid_file) else None
            if pid and os.path.exists(f"/proc/{pid}"):
                pass
            else:
                # 重启服务
                print("🔄 服务已停止，重新启动…")
        except: pass
        time.sleep(10)

if __name__ == '__main__':
    start_server()