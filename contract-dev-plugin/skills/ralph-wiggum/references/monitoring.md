# 监控与调试

## 实时监控

### 查看状态文件

```bash
# 查看完整状态
cat .ralph-state/ralph-loop.local.md

# 只看关键信息
grep -E "^(active|iteration|last_update):" .ralph-state/ralph-loop.local.md

# 实时监控
watch -n 5 'grep -E "^(active|iteration):" .ralph-state/ralph-loop.local.md'
```

## 活跃度检测

### 原理

```
┌─────────────────────────────────────────────────────────────────┐
│                    活跃度检测逻辑                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 获取文件最后修改时间                                         │
│     last_mod = stat -f %m .ralph-state/ralph-loop.local.md    │
│                                                                 │
│  2. 计算无更新时长                                               │
│     stale_seconds = now - last_mod                             │
│                                                                 │
│  3. 判断                                                         │
│     if stale_seconds > STALE_THRESHOLD (默认 300 秒)          │
│        → 输出警告：Claude Code 可能已停止                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 自定义阈值

```bash
# 5 分钟无更新认为 stale
bash scripts/ralph-loop.sh "任务" --stale 300

# 10 分钟无更新认为 stale
bash scripts/ralph-loop.sh "任务" --stale 600
```

## 状态解读

| active | iteration | 状态 |
|--------|-----------|------|
| true | 1 | 运行中，第1轮 |
| true | 10 | 运行中，第10轮 |
| true | 10 (stale) | ⚠️ 可能已停止 |
| false | 20 | 已完成 |
| false | 5 | 已完成（暗号检测） |

## 常见问题

### 问题：一直显示 "iteration 1"

可能原因：
- Claude Code 执行时间过长
- 网络问题导致卡住
- Claude Code 异常退出

### 问题：活跃度警告

这是正常现象，当：
- Claude Code 执行耗时操作
- 长时间等待 LLM 响应

超过阈值会输出警告，但会继续尝试执行。

### 问题：如何强制停止

```bash
# 手动修改状态文件
sed -i '' 's/active: true/active: false/' .ralph-state/ralph-loop.local.md

# 或直接删除
rm .ralph-state/ralph-loop.local.md
```
