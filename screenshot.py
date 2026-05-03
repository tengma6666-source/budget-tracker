#!/usr/bin/env python3
"""
截图工具 — 用 Chrome headless 截取 Dashboard 最新画面
"""
import websocket, json, base64, time, sys, os

WS_HOST = 'localhost'
WS_PORT = 9222
BROWSER_WS = 'ws://localhost:9222/devtools/browser/36ed8104-1667-43cb-a93b-d2a95c31cd31'
OUTPUT_FILE = os.path.expanduser('~/.openclaw/workspace/budget-tracker/dashboard_full.png')

def capture(url='http://localhost:8765/dashboard.html', output=OUTPUT_FILE):
    try:
        ws = websocket.create_connection(BROWSER_WS, timeout=15)
        ws.send(json.dumps({'id': 1, 'method': 'Target.createTarget', 'params': {'url': url}}))
        resp = json.loads(ws.recv())
        page_id = resp.get('result', {}).get('targetId', '')
        ws.close()
        time.sleep(3)

        ws2 = websocket.create_connection(f'ws://localhost:9222/devtools/page/{page_id}', timeout=15)
        ws2.send(json.dumps({'id': 2, 'method': 'Emulation.setDeviceMetricsOverride', 'params': {
            'width': 480, 'height': 1200, 'deviceScaleFactor': 2, 'mobile': True
        }}))
        ws2.recv()
        time.sleep(2.5)

        ws2.send(json.dumps({'id': 3, 'method': 'Runtime.evaluate', 'params': {
            'expression': 'Math.max(document.documentElement.scrollHeight, document.body.scrollHeight, 700)'
        }}))
        resp = json.loads(ws2.recv())
        content_h = resp.get('result', {}).get('result', {}).get('value', 800)

        ws2.send(json.dumps({'id': 4, 'method': 'Page.setDefaultBackgroundColorOverride', 'params': {'color': {'r': 9, 'g': 9, 'b': 20, 'a': 1}}}))
        ws2.recv()

        ws2.send(json.dumps({'id': 5, 'method': 'Page.captureScreenshot', 'params': {
            'format': 'png', 'quality': 90,
            'clip': {'x': 0, 'y': 0, 'width': 480, 'height': int(content_h), 'scale': 1}
        }}))
        resp = json.loads(ws2.recv())
        data = resp.get('result', {}).get('data', '')
        ws2.close()

        if data:
            with open(output, 'wb') as f:
                f.write(base64.b64decode(data))
            print(f'✅ 截图已保存: {output} ({len(data)} bytes)')
            return output
        else:
            print('❌ 无截图数据')
            return None
    except Exception as e:
        print(f'❌ 截图失败: {e}')
        return None

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8765/dashboard.html'
    out = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE
    capture(url, out)