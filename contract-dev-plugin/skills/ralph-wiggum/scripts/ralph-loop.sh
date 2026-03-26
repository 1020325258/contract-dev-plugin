#!/bin/bash

# Ralph Loop - 自动循环调用 Claude Code
# 功能：
# 1. 创建状态文件
# 2. 自动循环调用 Claude Code 执行任务
# 3. 监控文件活跃度，检测 Claude 是否停止

# ============ 配置 ============
SESSION_FILE=".ralph-state/ralph-loop.local.md"
STALE_THRESHOLD=300        # 文件 stale 阈值（秒），超过此时间无更新认为可能停止
MAX_ITERATIONS=0           # 最大迭代次数，0=无限
COMPLETION_PROMISE=""      # 完成暗号
TASK_PROMPT=""             # 任务描述

# ============ 帮助信息 ============
show_help() {
    cat << 'HELP_EOF'
Ralph Loop - Auto-repeating Claude Code execution loop

USAGE:
  ralph-loop.sh [PROMPT...] [OPTIONS]

ARGUMENTS:
  PROMPT...    Task description to execute

OPTIONS:
  --max-iterations <n>    Max iterations before auto-stop (default: unlimited)
  --stale <seconds>       Stale threshold (default: 300)
  --completion-promise    Promise phrase to signal completion
  -h, --help            Show this help message

EXAMPLES:
  ./ralph-loop.sh "implement login" --max-iterations 20
  ./ralph-loop.sh "follow openspec" --completion-promise "[TASK_COMPLETE]"
HELP_EOF
}

# ============ 解析参数 ============
PROMPT_PARTS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        --max-iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        --stale)
            STALE_THRESHOLD="$2"
            shift 2
            ;;
        --completion-promise)
            COMPLETION_PROMISE="$2"
            shift 2
            ;;
        *)
            PROMPT_PARTS+=("$1")
            shift
            ;;
    esac
done

# 合并 prompt
TASK_PROMPT="${PROMPT_PARTS[*]:-}"

if [[ -z "$TASK_PROMPT" ]]; then
    echo "❌ Error: No task prompt provided"
    show_help
    exit 1
fi

# ============ 创建状态文件 ============
mkdir -p .ralph-state

# 生成 YAML 安全的 completion_promise
if [[ -n "$COMPLETION_PROMISE" ]]; then
    COMPLETION_PROMISE_YAML="\"$COMPLETION_PROMISE\""
else
    COMPLETION_PROMISE_YAML="null"
fi

# 创建初始状态文件
cat > "$SESSION_FILE" << EOF
---
active: true
iteration: 0
max_iterations: $MAX_ITERATIONS
completion_promise: $COMPLETION_PROMISE_YAML
started_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
last_update: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---

$TASK_PROMPT
EOF

echo "📝 State file created: $SESSION_FILE"

# ============ 辅助函数 ============

# 获取文件最后修改时间
get_last_modified() {
    stat -f %m "$SESSION_FILE" 2>/dev/null || echo "0"
}

# 更新 iteration
update_iteration() {
    local iter=$1
    local now
    now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
    # 使用临时文件避免并发问题
    sed "s/^iteration:.*/iteration: $iter/" "$SESSION_FILE" > "${SESSION_FILE}.tmp"
    mv "${SESSION_FILE}.tmp" "$SESSION_FILE"
    sed "s/^last_update:.*/last_update: \"$now\"/" "$SESSION_FILE" > "${SESSION_FILE}.tmp"
    mv "${SESSION_FILE}.tmp" "$SESSION_FILE"
}

# 检查是否应该停止
should_stop() {
    local current_iteration=$1

    # 检查是否达到最大迭代次数
    if [[ $MAX_ITERATIONS -gt 0 ]] && [[ $current_iteration -ge $MAX_ITERATIONS ]]; then
        echo "✅ Reached max iterations: $MAX_ITERATIONS"
        sed -i '' 's/^active:.*/active: false/' "$SESSION_FILE"
        return 0
    fi

    # 检查是否已标记为完成
    local active_status
    active_status=$(grep "^active:" "$SESSION_FILE" 2>/dev/null | awk '{print $2}' | tr -d '\r' || echo "true")
    if [[ "$active_status" != "true" ]]; then
        echo "✅ Loop marked as inactive"
        return 0
    fi

    return 1
}

# 调用 Claude Code 并检测完成暗号
call_claude() {
    local prompt="$1"

    echo "🤖 Calling Claude Code..."

    # 记录输出到临时文件
    local output_file
    output_file=$(mktemp)

    # 调用 Claude Code
    claude -p -c --dangerously-skip-permissions --print "$prompt" 2>&1 | tee "$output_file"
    local exit_code=${PIPESTATUS[0]}

    # 检测完成暗号
    local should_exit=0
    if [[ -n "$COMPLETION_PROMISE" ]]; then
        if grep -q "<promise>.*$COMPLETION_PROMISE.*</promise>" "$output_file" 2>/dev/null; then
            echo ""
            echo "✅ Detected completion promise: $COMPLETION_PROMISE"
            should_exit=1
        fi
    fi

    rm -f "$output_file"

    if [[ $should_exit -eq 1 ]]; then
        sed -i '' 's/^active:.*/active: false/' "$SESSION_FILE"
        return 0
    fi

    return 1
}

# ============ 主循环 ============
iteration=0

echo "🔄 Ralph Loop started!"
echo "   Task: $TASK_PROMPT"
echo "   Max iterations: $([ $MAX_ITERATIONS -gt 0 ] && echo $MAX_ITERATIONS || echo 'unlimited')"
echo "   Stale threshold: ${STALE_THRESHOLD}s"
echo ""

while true; do
    # 检查是否应该停止
    if should_stop $iteration; then
        break
    fi

    iteration=$((iteration + 1))
    update_iteration $iteration

    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "📍 Iteration $iteration / $([ $MAX_ITERATIONS -gt 0 ] && echo $MAX_ITERATIONS || echo '∞')"
    echo "═══════════════════════════════════════════════════════════"

    # 活跃度检测
    last_mod=$(get_last_modified)
    now=$(date +%s)
    stale_seconds=$((now - last_mod))

    if [[ $stale_seconds -gt $STALE_THRESHOLD ]]; then
        echo "⚠️  WARNING: File not updated for ${stale_seconds}s (threshold: ${STALE_THRESHOLD}s)"
        echo "   Claude Code may have stopped unexpectedly!"
        echo "   Attempting to continue..."
    fi

    # 调用 Claude Code
    if call_claude "$TASK_PROMPT"; then
        echo ""
        echo "✅ Task completed!"
        break
    fi

    # 继续下一轮
    echo ""
    echo "⏳ Iteration $iteration complete, continuing to next round..."
done

echo ""
echo "👋 Ralph Loop finished at iteration $iteration"
echo "   Final state:"
cat "$SESSION_FILE"
