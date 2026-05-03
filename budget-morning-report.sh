#!/bin/bash
# Budget morning report - runs at 7:30 AM daily
# Sends latest budget screenshot + summary to 小马哥 via WeChat

WORKSPACE="/Users/mateng/.openclaw/workspace/budget-tracker"
MEDIA_DIR="/Users/mateng/.openclaw/media/browser"
OPENCLAW_BIN="/opt/homebrew/bin/openclaw"

cd "$WORKSPACE" || exit 1

# Check if HTTP server is running, if not start it
if ! curl -s --connect-timeout 1 http://localhost:8765 > /dev/null 2>&1; then
    python3 -m http.server 8765 --directory "$WORKSPACE" &
    sleep 1
fi

# Screenshot via screencapture
SNAP_FILE="$MEDIA_DIR/budget_morning_$(date +%Y%m%d).png"
screencapture -x -R "200,80,430,2000" "$SNAP_FILE" 2>/dev/null

if [ -f "$SNAP_FILE" ]; then
    # Crop to content area and upscale
    python3 << 'PYEOF'
import sys
from PIL import Image
import os

snap = "/Users/mateng/.openclaw/media/browser/budget_morning_$(date +%Y%m%d).png".replace("$(date +%Y%m%d)", __import__("datetime").datetime.now().strftime("%Y%m%d"))
try:
    img = Image.open(snap)
    w, h = img.size
    
    # Find content bounds
    import numpy as np
    arr = np.array(img)
    gray = arr.mean(axis=2)
    content_mask = gray > 20
    rows = np.where(content_mask.any(axis=1))[0]
    cols = np.where(content_mask.any(axis=0))[0]
    
    if len(rows) > 0:
        top, bottom = rows[0], rows[-1]
        left, right = cols[0], cols[-1]
        pad = 10
        crop = img.crop((max(0,left-pad), max(0,top-pad), min(w,right+pad), min(h,bottom+pad)))
        
        # 3x upscale
        hires = crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS)
        out = "/Users/mateng/.openclaw/workspace/budget-tracker/budget_morning_report.png"
        hires.save(out, quality=100)
        print(f"OK: {out} ({os.path.getsize(out)//1024}KB)")
    else:
        print("ERROR: No content found")
except Exception as e:
    print(f"ERROR: {e}")
PYEOF
fi

# Read budget summary
python3 budget.py status > /tmp/budget_status.txt 2>&1

# Send via WeChat
REPORT_FILE="$WORKSPACE/budget_morning_report.png"
if [ -f "$REPORT_FILE" ]; then
    $OPENCLAW_BIN message send --channel openclaw-weixin --target "o9cq807y9_YjdqyRBW1R1-TyBnfc@im.wechat" --file "$REPORT_FILE" 2>/dev/null
fi

# Also send text summary
STATUS_TEXT=$(cat /tmp/budget_status.txt)
$OPENCLAW_BIN message send --channel openclaw-weixin --target "o9cq807y9_YjdqyRBW1R1-TyBnfc@im.wechat" \
    --message "📊 早安！小马哥月度兴趣开销早报

${STATUS_TEXT}

应用地址：http://localhost:8765/dashboard.html" 2>/dev/null

echo "$(date): Budget morning report sent"