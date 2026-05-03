#!/bin/bash
# 启动检查脚本 — Mac Mini 重启后自动执行
CHROME_PID=$(pgrep -f "chrome.*headless.*9222" | head -1)
DASHBOARD_PID=$(pgrep -f "http.server.*8765" | head -1)

echo "[启动检查] $(date)"

# 1. 检查 Chrome headless
if [ -z "$CHROME_PID" ]; then
    echo "⚠️ Chrome headless 未运行，正在启动..."
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --headless=new \
        --remote-debugging-port=9222 \
        --remote-allow-origins='*' \
        --no-first-run \
        --disable-dev-shm-usage \
        --user-data-dir=/tmp/chrome-headless-perm \
        >> /tmp/chrome-headless.log 2>&1 &
    sleep 4
    echo "✅ Chrome headless 已启动"
else
    echo "✅ Chrome headless 已在运行 (PID=$CHROME_PID)"
fi

# 2. 检查 Dashboard HTTP 服务
if [ -z "$DASHBOARD_PID" ]; then
    echo "⚠️ Dashboard HTTP 服务未运行，正在启动..."
    launchctl load ~/Library/LaunchAgents/com.mateng.budget-dashboard.plist 2>/dev/null
    sleep 2
    echo "✅ Dashboard HTTP 服务已启动"
else
    echo "✅ Dashboard HTTP 服务已在运行 (PID=$DASHBOARD_PID)"
fi

# 3. 验证服务可用
sleep 2
HTTP_OK=$(curl -s --connect-timeout 3 http://localhost:8765/ | grep -c "小马哥" || echo 0)
CHROME_OK=$(curl -s http://localhost:9222/json/version 2>/dev/null | grep -c "Browser" || echo 0)

if [ "$HTTP_OK" -gt 0 ] && [ "$CHROME_OK" -gt 0 ]; then
    echo "✅ 所有服务就绪"
else
    echo "❌ 服务异常 — HTTP:$HTTP_OK CHROME:$CHROME_OK"
fi