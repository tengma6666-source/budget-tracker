#!/bin/bash
# sync_and_report.sh — 完整流程：更新数据 → 同步 GitHub → 生成截图 → 发送微信
# 用法: ./sync_and_report.sh
# 注意：git remote URL 已含 token，push 时自动使用，无需单独配置

set -e
WORKSPACE="/Users/mateng/.openclaw/workspace/budget-tracker"
TARGET_WX="o9cq807y9_YjdqyRBW1R1-TyBnfc@im.wechat"
GITHUB_PAGES="https://tengma6666-source.github.io/budget-tracker/"

cd "$WORKSPACE"

echo "[1/4] 📝 同步数据到 GitHub..."
git add budget-data.json
git commit -m "Data sync $(date '+%Y-%m-%d %H:%M')" || echo "无需提交（数据无变化）"
git push origin main 2>&1
echo "✅ GitHub push 完成"

echo "[2/4] ⏳ 等待 GitHub Pages rebuild（35秒）..."
sleep 35

echo "[3/4] 🖼️  生成日报截图..."
python3 generate_report.py

REPORT="$WORKSPACE/budget_morning_report.png"
if [ -f "$REPORT" ]; then
    echo "✅ 截图已生成: $(wc -c < "$REPORT") bytes"
else
    echo "❌ 截图生成失败"
    exit 1
fi

echo "[4/4] 📤 发送微信..."
openclaw message send --channel weixin --target "$TARGET_WX" --file "$REPORT" 2>/dev/null && echo "✅ 截图已发送"
openclaw message send --channel weixin --target "$TARGET_WX" \
    --message "📊 今日预算报告已更新

🌐 实时看板：$GITHUB_PAGES" 2>/dev/null && echo "✅ 链接已发送"

echo ""
echo "✅ 全部完成！"
echo "   看板：$GITHUB_PAGES"
echo "   本地截图：$REPORT"
