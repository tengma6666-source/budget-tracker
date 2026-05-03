#!/bin/bash
# 月度归档 cron — 每月1日 00:10 执行
python3 /Users/mateng/.openclaw/workspace/budget-tracker/budget_archive.py check
echo "$(date): 月度归档检查完成"