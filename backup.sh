#!/bin/bash
BACKUP_DIR="/Users/mateng/.openclaw/workspace/budget-tracker/backups"
mkdir -p "$BACKUP_DIR"
cp "/Users/mateng/.openclaw/workspace/budget-tracker/budget-data.json" "$BACKUP_DIR/budget-data-$(date +%Y%m%d-%H%M%S).json"
# 只保留最近10份备份
ls -t "$BACKUP_DIR" | tail -n +11 | xargs -I{} rm "$BACKUP_DIR/{}"
echo "Backup done: $(date)"
