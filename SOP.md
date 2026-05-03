# 预算应用 SOP — Hermes Agent 接手指南

**目标**：任何 Agent 都能通过本 SOP 独立操作小马哥的个人预算应用。

---

## 应用基本信息

| 项目 | 路径 |
|------|------|
| 工作目录 | `~/.openclaw/workspace/budget-tracker/` |
| 数据文件 | `budget-data.json` |
| 参考配置 | `budget-config-reference.json`（只读，不可覆盖） |
| 本地看板 | `http://localhost:8765/dashboard.html` |
| 外网看板 | `https://tengma6666-source.github.io/budget-tracker/` |
| 早报截图 | `budget_morning_report.png` |
| 完整同步脚本 | `sync_and_report.sh` |
| GitHub 仓库 | `tengma6666-source/budget-tracker` |

---

## 核心命令

### 1. 记账（add expense）

```bash
python3 ~/.openclaw/workspace/budget-tracker/record.py add "描述内容"
```

**自动归类规则**（无需手动指定分类）：
- "个人兴趣/个人爱好/手办/游戏" → `个人爱好`
- "礼物/给家人买/家庭用品" → `家庭幸福感好物`
- "衣服/鞋/包/配饰" → `鞋品`
- "电子设备/数码/手机/电脑" → `好物购买`
- "聚餐/聚会/活动" → `个人爱好`
- 拿不准 → 最接近分类 + note 备注原话

**输出格式**：
```
[2026-05-03 21:00] | ADD | 好物购买 | ¥1998 | iPhone配件 | OK
```

---

### 2. 查询状态（status）

```bash
python3 ~/.openclaw/workspace/budget-tracker/budget.py status
```

返回：总预算 / 已消耗 / 剩余 / 各分类进度

---

### 3. 修改分类限额（set）

```bash
python3 ~/.openclaw/workspace/budget-tracker/budget.py set 类别 新限额
```

**⚠️ 修改后必须同步更新 `budget-config-reference.json`**（两个文件保持一致）。

---

### 4. 生成早报图片（generate report）

```bash
python3 ~/.openclaw/workspace/budget-tracker/generate_report.py
```

- 输出：`budget_morning_report.png`（2490x2460, 约 600KB）
- 内置数据校验，发现异常自动用 reference 修复
- 所有操作写 `budget-ops.log.md`（append-only）

---

### 5. 重置月份（reset）

```bash
python3 ~/.openclaw/workspace/budget-tracker/budget.py reset
```

清空当月消费记录，保留分类配置。

---

## 发送给马腾的标准三件套

每次与马腾沟通预算/记账时，**必须同时发送**：

1. **文字总结**：`budget.py status` 的输出
2. **Dashboard 截图**：发送到微信（路径：`~/.openclaw/workspace/budget-tracker/budget_morning_report.png`）
3. **外网链接**：`https://tengma6666-source.github.io/budget-tracker/`

发送命令：
```bash
# 完整流程（一键）：push 数据 → rebuild → 生成截图 → 发微信截图 → 发链接
bash ~/.openclaw/workspace/budget-tracker/sync_and_report.sh

# 或者分步执行：
# 1. 截图
python3 ~/.openclaw/workspace/budget-tracker/generate_report.py

# 2. 微信发送截图
openclaw message send --channel weixin --target "o9cq807y9_YjdqyRBW1R1-TyBnfc@im.wechat" --file "~/.openclaw/workspace/budget-tracker/budget_morning_report.png"

# 3. 微信发送链接
openclaw message send --channel weixin --target "o9cq807y9_YjdqyRBW1R1-TyBnfc@im.wechat" --message "🌐 外网看板：https://tengma6666-source.github.io/budget-tracker/"
```

---

## 预算配置（永久准确）

```
总预算：¥10,000
分类：
  - 个人爱好      ¥4,000
  - 好物购买      ¥3,000
  - 鞋品          ¥1,000
  - 家庭幸福感好物 ¥2,000
```

当前消费：千问G1 AI眼镜 ¥1,998（好物购买，2026-05-01）

---

## ⚠️ 关键禁止规则

1. **禁止直接覆盖 `budget-data.json`**，所有修改通过 `budget.py` 或 `record.py`
2. **禁止在飞书发送非 workspace 路径的文件**，先复制到 `~/.openclaw/workspace/`
3. **禁止跳过三件套**（文字 + 截图 + 地址），每次与马腾沟通预算必须同时提供
4. **禁止在 `budget-config-reference.json` 写入任何内容**，它是只读的恢复参考

---

## 失败处理

| 失败类型 | 处理方式 |
|---------|---------|
| 截图生成失败（退出码≠0） | 记录 `FAIL` 到 `budget-ops.log.md`，发送文字版 |
| 文件路径错误 | 检查路径是否在 workspace 内，复制后再发 |
| 数据校验失败 | `generate_report.py` 自动用 reference 修复，不要手动干预 |

---

## 马腾的沟通偏好

- **直接、不废话**，不需要"好问题！"这类废话
- **主动做事**，不等他问"要不要"
- 消息简洁，重要时详尽

---

_Last updated: 2026-05-03_