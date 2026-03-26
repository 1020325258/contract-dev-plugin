#!/bin/bash

# Ralph Loop Monitor Script
# 监控 Ralph Loop 状态，包括文件活跃度检测

set -euo pipefail

# ============ 配置 ============
SESSION_FILE=".claude/ralph-loop.local.md"
CHECK_INTERVAL=10           # 检查间隔（秒）
STALE_THRESHOLD=300         # 文件 stale 阈值（秒），超过此时间无更新认为可能停止
MAX_ITERATIONS_DEFAULT=30   # 默认最大迭代次数

# ============ 函数 ============

# 显示帮助
show_help() {
    cat << 'HELP_EOF'
Ralph Loop Monitor - 监控 Ralph Loop 状态

USAGE:
  ./monitor-loop.sh [OPTIONS]

OPTIONS:
  --interval <seconds>    检查间隔（默认 10 秒）
  --stale <seconds>      文件 stale 阈值（默认 300 秒 = 5 分钟）
  -h, --help            显示帮助

EXAMPLES:
  ./monitor-loop.sh                    # 使用默认配置
  ./monitor-loop.sh --interval 5       # 每 5 秒检查一次
  ./monitor-loop.sh --stale 600       # 10 分钟无更新认为 stale
HELP_EOF
}

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            CHECK_INTERVAL="$2"
            shift 2
            ;;
        --stale)
            STALE_THRESHOLD="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 获取文件最后修改时间（秒）
get_last_modified() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        stat -f %m "$SESSION_FILE" 2>/dev/null || echo "0"
    else
        # Linux
        stat -c %Y "$SESSION_FILE" 2>/dev/null || echo "0"
    fi
}

# 格式化时间
format_timestamp() {
    local timestamp="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        date -r "$timestamp" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "未知"
    else
        date -d "@$timestamp" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "未知"
    fi
}

# 显示状态
display_status() {
    local active="$1"
    local iteration="$2"
    local max_iter="$3"
    local last_update="$4"
    local stale_seconds="$5"

    echo "┌─────────────────────────────────────────┐"
    echo "│         Ralph Loop 监控状态               │"
    echo "├─────────────────────────────────────────┤"
    printf "│ %-15s %-25s │\n" "状态:" "$active"
    printf "│ %-15s %-25s │\n" "迭代:" "$iteration / $max_iter"
    printf "│ %-15s %-25s │\n" "最后更新:" "$(format_timestamp $last_update)"
    printf "│ %-15s %-25s │\n" "无更新时长:" "${stale_seconds}秒"

    if [[ $stale_seconds -gt $STALE_THRESHOLD ]]; then
        echo "├─────────────────────────────────────────┤"
        echo "│ ⚠️  WARNING: 文件长时间未更新，可能已停止！  │"
    fi

    echo "└─────────────────────────────────────────┘"
}

# ============ 主逻辑 ============

# 检查状态文件是否存在
if [[ ! -f "$SESSION_FILE" ]]; then
    echo "❌ 错误: 状态文件不存在: $SESSION_FILE"
    echo "   请先启动 Ralph Loop"
    exit 1
fi

echo "🔍 开始监控 Ralph Loop..."
echo "   检查间隔: ${CHECK_INTERVAL}秒"
echo "   Stale 阈值: ${STALE_THRESHOLD}秒"
echo ""

# 记录上一次的 iteration，用于检测是否增加
last_iteration=0

while true; do
    # 检查状态文件是否存在
    if [[ ! -f "$SESSION_FILE" ]]; then
        echo "❌ Ralph Loop 已结束（状态文件不存在）"
        exit 0
    fi

    # 解析状态
    active=$(grep "^active:" "$SESSION_FILE" | awk '{print $2}' | tr -d '\r')
    iteration=$(grep "^iteration:" "$SESSION_FILE" | awk '{print $2}' | tr -d '\r')
    max_iter=$(grep "^max_iterations:" "$SESSION_FILE" | awk '{print $2}' | tr -d '\r')

    # 获取文件最后修改时间
    last_modified=$(get_last_modified)
    current_time=$(date +%s)
    stale_seconds=$((current_time - last_modified))

    # 设置默认值
    max_iter=${max_iter:-$MAX_ITERATIONS_DEFAULT}

    # 检测 iteration 是否有增加
    if [[ "$iteration" -gt "$last_iteration" ]]; then
        echo "📈 Iteration 变化: $last_iteration → $iteration"
        last_iteration=$iteration
    fi

    # 显示状态
    clear
    display_status "$active" "$iteration" "$max_iter" "$last_modified" "$stale_seconds"

    # 检查是否结束
    if [[ "$active" != "true" ]]; then
        echo ""
        echo "✅ Ralph Loop 已完成"
        echo "   最终迭代: $iteration / $max_iter"
        exit 0
    fi

    # 检查是否 stale（可能已停止）
    if [[ $stale_seconds -gt $STALE_THRESHOLD ]]; then
        echo ""
        echo "⚠️  警告: 文件超过 ${STALE_THRESHOLD} 秒未更新"
        echo "   Ralph Loop 可能已停止运行"
        echo "   请检查 Claude Code 状态"
    fi

    sleep "$CHECK_INTERVAL"
done
