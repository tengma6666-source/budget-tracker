#!/bin/bash
# build_dashboard.sh — 读取 budget-data.json，注入 dashboard.html，输出 index.html
# 用法: ./build_dashboard.sh

DATA_FILE="budget-data.json"
TEMPLATE_FILE="dashboard_template.html"
OUTPUT_FILE="index.html"

if [ ! -f "$DATA_FILE" ]; then
    echo "❌ budget-data.json not found"
    exit 1
fi

# 读取 JSON 数据（单行，去掉空白）
DATA_JSON=$(cat "$DATA_FILE")

# 生成 HTML
cat > "$OUTPUT_FILE" << 'HTML_HEAD'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>小马哥预算追踪</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', Arial, sans-serif; background: #0a0a14; color: #fff; min-height: 100vh; padding: 20px; }
.container { max-width: 750px; margin: 0 auto; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #12122a; border-radius: 16px; margin-bottom: 16px; }
.header h1 { font-size: 20px; font-weight: 700; }
.header .time { font-size: 12px; color: #666; }
.hero { background: #12122a; border-radius: 16px; padding: 24px; margin-bottom: 16px; display: flex; align-items: center; gap: 32px; }
.progress-ring { position: relative; width: 120px; height: 120px; }
.progress-ring svg { transform: rotate(-90deg); }
.progress-ring circle { fill: none; stroke-width: 12; }
.progress-bg { stroke: #1e1e40; }
.progress-fill { stroke-linecap: round; transition: stroke-dashoffset 1s ease; }
.hero-stats { flex: 1; }
.hero-stats .row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1e1e40; }
.hero-stats .row:last-child { border-bottom: none; }
.hero-stats .label { color: #888; font-size: 14px; }
.hero-stats .value { font-weight: 700; font-size: 16px; }
.hero-stats .value.green { color: #4ade80; }
.hero-stats .value.red { color: #f87171; }
.hero-stats .value.cyan { color: #22d3ee; }
.section { background: #12122a; border-radius: 16px; padding: 20px; margin-bottom: 16px; }
.section-title { font-size: 13px; color: #666; margin-bottom: 16px; }
.cat-item { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #1e1e40; }
.cat-item:last-child { border-bottom: none; }
.cat-icon { width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.cat-info { flex: 1; min-width: 0; }
.cat-name { font-size: 14px; font-weight: 600; margin-bottom: 4px; }
.cat-budget { font-size: 11px; color: #666; }
.cat-right { text-align: right; }
.cat-amount { font-size: 15px; font-weight: 700; }
.cat-remaining { font-size: 11px; color: #666; }
.progress-bar { height: 6px; background: #1e1e40; border-radius: 3px; margin-top: 6px; overflow: hidden; }
.progress-bar-fill { height: 100%; border-radius: 3px; transition: width 1s ease; }
.txn-item { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #1e1e40; }
.txn-item:last-child { border-bottom: none; }
.txn-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0; }
.txn-info { flex: 1; min-width: 0; }
.txn-cat { font-size: 13px; font-weight: 600; }
.txn-note { font-size: 11px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.txn-right { text-align: right; }
.txn-amount { font-size: 14px; font-weight: 700; }
.txn-date { font-size: 11px; color: #666; }
.footer { text-align: center; padding: 20px; font-size: 11px; color: #333; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; }
.badge.over { background: rgba(248,113,113,0.2); color: #f87171; }
.badge.ok { background: rgba(74,222,128,0.15); color: #4ade80; }
</style>
</head>
<body>
<div class="container">
HTML_HEAD

# 注入时间
NOW=$(date '+%Y年%m月%d日 %H:%M')

cat >> "$OUTPUT_FILE" << HTML_BODY
  <div class="header">
    <h1>📊 小马哥月度预算</h1>
    <span class="time" id="updateTime">—</span>
  </div>

  <div class="hero">
    <div class="progress-ring">
      <svg width="120" height="120" viewBox="0 0 120 120">
        <circle class="progress-bg" cx="60" cy="60" r="48"/>
        <circle class="progress-fill" id="progressCircle" cx="60" cy="60" r="48"
          stroke-dasharray="301.59" stroke-dashoffset="301.59"/>
      </svg>
    </div>
    <div class="hero-stats">
      <div class="row"><span class="label">总预算</span><span class="value" id="totalBudget">—</span></div>
      <div class="row"><span class="label">已消耗</span><span class="value cyan" id="totalSpent">—</span></div>
      <div class="row"><span class="label">剩余</span><span class="value green" id="totalRemaining">—</span></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">📂 预算分类</div>
    <div id="categories"></div>
  </div>

  <div class="section">
    <div class="section-title">🧾 最新消费</div>
    <div id="transactions"></div>
  </div>

  <div class="footer">
    更新于 <span id="footerTime">—</span> · 预算追踪器<br>
    数据来源：本地 budget-data.json
  </div>
</div>

<script>
const DATA = JSON_DATA_PLACEHOLDER;

const CAT_META = {
  "个人爱好":       { color: "#a78bfa", bg: "#1a1233", icon: "🎮" },
  "好物购买":       { color: "#22d3ee", bg: "#0d1f24", icon: "🛍️" },
  "鞋品":           { color: "#f97316", bg: "#1f1308", icon: "👟" },
  "家庭幸福感好物": { color: "#fb923c", bg: "#1f1408", icon: "🏠" },
  "餐饮":           { color: "#fbbf24", bg: "#1f1a08", icon: "🍜" },
  "活动聚会":       { color: "#f472b6", bg: "#1f0c18", icon: "🥂" },
  "交通":           { color: "#60a5fa", bg: "#0c1020", icon: "🚗" },
  "其他":           { color: "#6b7280", bg: "#111",    icon: "📦" },
};

function fmt(n) { return '¥' + n.toLocaleString('zh-CN'); }

const cats = DATA.categories || [];
const expenses = DATA.expenses || [];
const totalBudget = DATA.totalBudget || 0;

const catSpent = {};
expenses.forEach(e => { catSpent[e.category] = (catSpent[e.category]||0) + e.amount; });

const activeCats = cats.filter(c => c.limit > 0 || catSpent[c.name]);
const totalLimit = activeCats.reduce((s,c) => s + c.limit, 0) || totalBudget;
const totalSpent = Object.values(catSpent).reduce((s,v) => s+v, 0);
const remaining = totalLimit - totalSpent;
const pct = Math.min(100, Math.round(totalSpent / totalLimit * 100));

// Update time
const dateStr = DATA.expenses && DATA.expenses[0] ? DATA.expenses[0].date : new Date().toISOString().slice(0,16).replace('T',' ');
document.getElementById('updateTime').textContent = dateStr;
document.getElementById('footerTime').textContent = dateStr;

// Hero stats
document.getElementById('totalBudget').textContent = fmt(totalLimit);
document.getElementById('totalSpent').textContent = fmt(totalSpent);
const remEl = document.getElementById('totalRemaining');
remEl.textContent = remaining >= 0 ? fmt(remaining) : '-' + fmt(Math.abs(remaining));
remEl.className = 'value ' + (remaining >= 0 ? 'green' : 'red');

// Progress ring
const circ = document.getElementById('progressCircle');
const circumference = 2 * Math.PI * 48;
circ.style.strokeDasharray = circumference;
circ.style.strokeDashoffset = circumference * (1 - pct / 100);
circ.style.stroke = remaining >= 0 ? '#22d3ee' : '#f87171';

// Categories
const catsEl = document.getElementById('categories');
catsEl.innerHTML = activeCats.map(c => {
  const meta = CAT_META[c.name] || CAT_META["其他"];
  const spent = catSpent[c.name] || 0;
  const pct2 = Math.min(100, Math.round(spent / c.limit * 100));
  const isOver = c.limit > 0 && spent > c.limit;
  return '<div class="cat-item">' +
    '<div class="cat-icon" style="background:' + meta.bg + '">' + meta.icon + '</div>' +
    '<div class="cat-info">' +
      '<div class="cat-name">' + c.name + '</div>' +
      '<div class="cat-budget">预算 ' + fmt(c.limit) + '</div>' +
      '<div class="progress-bar"><div class="progress-bar-fill" style="width:' + pct2 + '%;background:' + meta.color + '"></div></div>' +
    '</div>' +
    '<div class="cat-right">' +
      '<div class="cat-amount">' + fmt(spent) + '</div>' +
      '<div class="cat-remaining">' + (isOver ? '<span class="badge over">超' + fmt(spent-c.limit) + '</span>' : '<span class="badge ok">剩' + fmt(c.limit-spent) + '</span>') + '</div>' +
    '</div>' +
  '</div>';
}).join('');

// Transactions
const txnsEl = document.getElementById('transactions');
const recent = [...expenses].reverse().slice(0, 8);
txnsEl.innerHTML = recent.length ? recent.map(e => {
  const meta = CAT_META[e.category] || CAT_META["其他"];
  const date = e.date ? e.date.slice(5) : '';
  return '<div class="txn-item">' +
    '<div class="txn-icon" style="background:' + meta.bg + '">' + meta.icon + '</div>' +
    '<div class="txn-info">' +
      '<div class="txn-cat">' + e.category + '</div>' +
      '<div class="txn-note">' + (e.note || '') + '</div>' +
    '</div>' +
    '<div class="txn-right">' +
      '<div class="txn-amount">-' + fmt(e.amount) + '</div>' +
      '<div class="txn-date">' + date + '</div>' +
    '</div>' +
  '</div>';
}).join('') : '<div style="color:#666;text-align:center;padding:20px">暂无消费记录</div>';
</script>
</body>
</html>
HTML_BODY

# 替换 JSON 占位符（Python 避免 sed 命令行长度的 shell 限制）
python3 - << 'PYEOF'
import json

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

with open("budget-data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

json_str = json.dumps(data, ensure_ascii=False)
html = html.replace("JSON_DATA_PLACEHOLDER", json_str)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
PYEOF

echo "✅ dashboard 构建完成: $OUTPUT_FILE"
