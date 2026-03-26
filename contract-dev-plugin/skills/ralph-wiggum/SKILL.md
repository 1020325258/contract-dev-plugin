---
description: Ralph Wiggum Loop - 自动循环调用 Claude Code 执行任务，包含活跃度检测防止任务意外停止
---

# Ralph Wiggum Loop

## 概述

通过脚本自动循环调用 Claude Code 执行任务，包含：
- 自动循环调用 Claude Code（通过 CLI）
- 活跃度检测（文件长时间无更新时发出警告）
- 完成暗号检测
- 最大迭代次数限制

## 核心脚本

- **主脚本**: `scripts/ralph-loop.sh` - 包含完整功能

## 快速开始

### 基本用法

```bash
bash skills/ralph-wiggum/scripts/ralph-loop.sh "<任务描述>" [OPTIONS]
```

### 常用命令

```bash
# 20 次循环后自动停止
bash skills/ralph-wiggum/scripts/ralph-loop.sh "实现用户登录功能" --max-iterations 20

# 使用完成暗号
bash skills/ralph-wiggum/scripts/ralph-loop.sh "实现订单模块" --completion-promise "[TASK_COMPLETE]"

# 自定义活跃度检测阈值（300秒 = 5分钟）
bash skills/ralph-wiggum/scripts/ralph-loop.sh "任务描述" --max-iterations 30 --stale 300
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--max-iterations` | 最大循环次数 | 无限 |
| `--stale` | 活跃度检测阈值（秒） | 300 |
| `--completion-promise` | 完成暗号 | 无 |

## 状态文件

创建 `.ralph-state/ralph-loop.local.md`：

```yaml
---
active: true
iteration: 5
max_iterations: 30
completion_promise: "[TASK_COMPLETE]"
started_at: "2026-03-24T10:30:00Z"
last_update: "2026-03-24T10:35:00Z"
---

任务描述
```

## 核心功能

### 1. 自动循环调用

脚本通过 `claude -p -c --print` 自动循环调用 Claude Code 执行任务。

### 2. 活跃度检测

超过 `--stale` 阈值（默认 300 秒）文件无更新时，会输出警告：
```
⚠️  WARNING: File not updated for 350s (threshold: 300s)
   Claude Code may have stopped unexpectedly!
```

### 3. 完成暗号

通过 `--completion-promise` 设置暗号，当 Claude Code 输出 `<promise>xxx</promise>` 时自动停止。

### 4. 最大迭代

通过 `--max-iterations` 设置最大循环次数。

## 文档索引

| 文档 | 说明 |
|------|------|
| [使用指南](./references/usage.md) | 完整使用说明 |
| [结束暗号](./references/completion-promise.md) | 完成暗号机制 |
| [监控调试](./references/monitoring.md) | 监控任务状态 |

## 使用场景

- OpenSpec 规范执行
- 批量代码生成
- 长时间运行的开发任务
- 需要防止 Claude Code 意外停止的场景
