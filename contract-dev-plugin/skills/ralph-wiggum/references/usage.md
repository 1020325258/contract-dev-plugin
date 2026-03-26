# Ralph Loop 使用指南

## 基本用法

### 启动 Ralph Loop

```bash
bash skills/ralph-wiggum/scripts/ralph-loop.sh "<任务描述>" [OPTIONS]
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--max-iterations <n>` | 最大循环次数 | 无限 |
| `--stale <seconds>` | 活跃度检测阈值 | 300 秒 |
| `--completion-promise '<text>'` | 完成暗号 | 无 |

### 完整示例

```bash
# 推荐用法
bash skills/ralph-wiggum/scripts/ralph-loop.sh \
    "根据 openspec 规范实现用户登录功能" \
    --max-iterations 30 \
    --stale 300 \
    --completion-promise "[TASK_COMPLETE]"

# 简单用法
bash skills/ralph-wiggum/scripts/ralph-loop.sh "实现订单管理模块" --max-iterations 20
```

## 工作原理

```
┌─────────────────────────────────────────────────────────────────┐
│                    Ralph Loop 执行流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 创建状态文件 .ralph-state/ralph-loop.local.md            │
│                                                                 │
│  2. 循环执行：                                                 │
│     ├── 调用 Claude Code 执行任务                                │
│     ├── 检测完成暗号                                            │
│     ├── 检测活跃度（文件更新间隔）                               │
│     ├── 更新 iteration                                          │
│     └── 检查是否达到最大次数                                     │
│                                                                 │
│  3. 退出条件：                                                 │
│     ├── 达到 max_iterations                                    │
│     ├── 检测到完成暗号                                          │
│     └── active 标记为 false                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 状态文件

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

### 字段说明

| 字段 | 说明 |
|------|------|
| `active` | 是否活跃运行 |
| `iteration` | 当前第几轮 |
| `max_iterations` | 最大循环次数 |
| `completion_promise` | 完成暗号 |
| `started_at` | 开始时间 |
| `last_update` | 最后更新时间（用于活跃度检测） |

## 查看状态

```bash
# 查看当前状态
cat .ralph-state/ralph-loop.local.md

# 只看关键信息
grep -E "^(active|iteration):" .ralph-state/ralph-loop.local.md
```

## 停止 Ralph Loop

1. **达到最大迭代次数** - `iteration >= max_iterations`
2. **检测到完成暗号** - 输出 `<promise>xxx</promise>`
3. **手动停止** - `Ctrl+C`
