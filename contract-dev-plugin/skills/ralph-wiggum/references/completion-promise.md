# 结束暗号机制

## 原理

通过 `--completion-promise` 参数设置结束暗号，当 Claude Code 输出该暗号时，Loop 自动停止。

## 使用方式

```bash
bash skills/ralph-wiggum/scripts/ralph-loop.sh \
    "任务描述" \
    --completion-promise "[TASK_COMPLETE]"
```

## 输出暗号

任务完成后，Claude Code 需要输出：

```xml
<promise>[TASK_COMPLETE]</promise>
```

## 严格要求

- ✅ 使用 `<promise>` XML 标签
- ✅ 内容与设置的暗号完全匹配
- ✅ 内容必须完全真实

## 推荐暗号

| 场景 | 推荐暗号 |
|------|---------|
| OpenSpec 任务 | `[TASK_COMPLETE]` |
| 通用任务 | `TASK COMPLETE` |
| 测试场景 | `All tests passing` |

## 检测逻辑

脚本会检测 Claude Code 输出中是否包含：

```
<promise>xxx</promise>
```

匹配即停止。
