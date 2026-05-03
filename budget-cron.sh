#!/bin/bash
# Budget morning cron — runs at 7:30 AM Asia/Shanghai daily
WORKSPACE="/Users/mateng/.openclaw/workspace/budget-tracker"
OPENCLAW="/opt/homebrew/bin/openclaw"
TARGET="o9cq807y9_YjdqyRBW1R1-TyBnfc@im.wechat"

cd "$WORKSPACE"

# Generate report PNG from JSON (no browser needed)
python3 generate_report.py

REPORT="$WORKSPACE/budget_morning_report.png"

# Send screenshot
if [ -f "$REPORT" ]; then
    $OPENCLAW message send \
        --channel openclaw-weixin \
        --target "$TARGET" \
        --file "$REPORT" 2>/dev/null
fi

# Get budget status
STATUS=$(python3 budget.py status 2>/dev/null)

# Send text
$OPENCLAW message send \
    --channel openclaw-weixin \
    --target "$TARGET" \
    --message "📊 早安！小马哥月度兴趣开销早报

$STATUS

应用地址：http://localhost:8765/dashboard.html" 2>/dev/null

echo "$(date): Budget report sent"