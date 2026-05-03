# GitHub Pages 部署架构

## 整体架构

```
本地 Mac Mini
    │
    ├── budget-data.json（真实数据源，本地优先）
    │
    ├── generate_report.py（生成微信截图）
    │
    ├── sync_and_report.sh（完整更新流程）
    │       │
    │       ▼
    └── build_dashboard.sh（静态 HTML 构建）
            │
            ▼
    GitHub 仓库（tengma6666-source/budget-tracker）
            │
            ├── main 分支 push
            │
            ▼
    GitHub Actions（deploy.yml）
            │  触发条件：push to main
            │  动作：bash build_dashboard.sh
            │
            ▼
    GitHub Pages
    https://tengma6666-source.github.io/budget-tracker/
```

## 数据流

1. **push 数据**：`git add budget-data.json && git push origin main`
2. **Actions 触发**：约 10-20 秒后开始执行
3. **build_dashboard.sh**：
   - 读取 `budget-data.json`
   - 用 Python 将 JSON 注入 `index.html` 的 `const DATA = ...`
   - 输出到 `_site/` 目录
4. **deploy-pages action**：将 `_site/` 部署到 GitHub Pages
5. **生效**：约 30-40 秒后，https://tengma6666-source.github.io/budget-tracker/ 显示最新数据

## 关键文件

| 文件 | 作用 |
|------|------|
| `build_dashboard.sh` | 将 JSON 数据注入 HTML，用 Python 替代 sed 避免命令行长度限制 |
| `sync_and_report.sh` | 完整流程：push → sleep 35 → generate_report.py → 发微信 |
| `.github/workflows/deploy.yml` | GitHub Actions 部署配置 |

## build_dashboard.sh 关键逻辑

```bash
# 旧版（失败）：sed 命令超过 macOS 命令行长度限制
sed -i '' "s|JSON_DATA_PLACEHOLDER|$DATA_JSON|g" index.html
# → "File name too long" 错误

# 新版（成功）：Python 字符串替换
python3 - << 'PYEOF'
with open("index.html") as f: html = f.read()
with open("budget-data.json") as f: data = json.load(f)
html = html.replace("JSON_DATA_PLACEHOLDER", json.dumps(data, ensure_ascii=False))
with open("index.html", "w") as f: f.write(html)
PYEOF
```

## 常见故障排查

| 症状 | 原因 | 解法 |
|------|------|------|
| Pages 显示 "JSON_DATA_PLACEHOLDER" | sed 命令过长，未执行替换 | 确认 build_dashboard.sh 使用 Python 注入 |
| Pages 数据落后 30+ 分钟 | Actions 未触发 | 检查仓库 Settings → Actions → 允许 workflow |
| push 后 Pages 仍显示旧数据 | rebuild 未完成 | 等 35-40 秒再验证 |
| 中文显示乱码 `\u4e2a...` | `json.dumps()` 默认 `ensure_ascii=True` | 用 `ensure_ascii=False` |
| emoji 显示方块 | emoji 未用 Apple Color Emoji 字体 | generate_report.py 用分离字体绘制 |
| Dashboard 无数据 | `budget-data.json` 未 push | 先 `git add budget-data.json && git push` |

## 安全说明

- **仓库**：私有（private），不公开可见
- **数据暴露风险**：GitHub raw 文件 URL 格式固定但难以猜测，实际风险极低
- **Token**：已从脚本中移除，git remote URL 内嵌 token 推送不受 GitHub Secret Scanning 影响

## 与 OpenClaw 协作

当 Hermes Agent 或 OpenClaw 调用 budget-tracker skill 时：
1. 记账操作：直接修改 `budget-data.json`（通过 record.py）
2. 同步：调用 `sync_and_report.sh` 或手动执行 push + rebuild
3. 发送：使用 `openclaw message send --channel weixin`
4. 不要修改 `budget-config-reference.json`（只读）
5. 所有截图文件路径必须在 `~/.openclaw/workspace/budget-tracker/` 内
