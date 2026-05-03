#!/bin/bash
# 恢复启动脚本 — 加载所有预算追踪相关服务
# 由 macOS 登录项自动调用
SCRIPT_DIR="/Users/mateng/.openclaw/workspace/budget-tracker"

echo "[预算追踪恢复启动] $(date)"

# 1. 加载 Dashboard HTTP 服务
if ! launchctl list | grep -q "com.mateng.budget-dashboard"; then
    launchctl load ~/Library/LaunchAgents/com.mateng.budget-dashboard.plist
    echo "✅ Dashboard HTTP 服务已加载"
fi

# 2. 加载每日备份服务
if ! launchctl list | grep -q "com.mateng.budget-backup"; then
    launchctl load ~/Library/LaunchAgents/com.mateng.budget-backup.plist
    echo "✅ 备份服务已加载"
fi

# 3. 检查 Chrome headless（不重复启动）
if ! curl -s --connect-timeout 2 http://localhost:9222/json > /dev/null 2>&1; then
    echo "⚠️ Chrome headless 未运行，正在启动..."
    /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
        --headless=new \
        --remote-debugging-port=9222 \
        --remote-allow-origins='*' \
        --no-first-run \
        --disable-dev-shm-usage \
        --user-data-dir=/tmp/chrome-headless-perm \
        >> /tmp/chrome-headless.log 2>&1 &
    sleep 5
    echo "✅ Chrome headless 已启动"
else
    echo "✅ Chrome headless 已在运行"
fi

# 4. 验证数据完整性
DATA_FILE="$SCRIPT_DIR/budget-data.json"
if [ -f "$DATA_FILE" ]; then
    echo "✅ 数据文件正常 ($(wc -c < "$DATA_FILE") bytes)"
else
    echo "❌ 数据文件缺失！"
fi

# 5. 验证 reference 一致性
REF_FILE="$SCRIPT_DIR/budget-config-reference.json"
REF_TOTAL=$(python3 -c "import json; print(json.load(open('$REF_FILE'))['totalBudget'])" 2>/dev/null)
DATA_TOTAL=$(python3 -c "import json; print(json.load(open('$DATA_FILE'))['totalBudget'])" 2>/dev/null)
if [ "$REF_TOTAL" = "$DATA_TOTAL" ]; then
    echo "✅ 配置校验通过 (totalBudget=$REF_TOTAL)"
else
    echo "⚠️ 配置不一致! Reference=$REF_TOTAL Data=$DATA_TOTAL — 自动修复中..."
    python3 -c "
import json, shutil, datetime
ref = json.load(open('$REF_FILE'))
data = json.load(open('$DATA_FILE'))
# 备份当前数据
shutil.copy2('$DATA_FILE', '$SCRIPT_DIR/budget-data.json.autosave.' + datetime.datetime.now().strftime('%Y%m%d%H%M%S'))
# 修复 totalBudget 和 categories
data['totalBudget'] = ref['totalBudget']
data['categories'] = ref['categories']
json.dump(data, open('$DATA_FILE','w'), indent=2, ensure_ascii=False)
print('✅ 配置已自动修复')
"
fi

echo "[恢复启动完成] $(date)"