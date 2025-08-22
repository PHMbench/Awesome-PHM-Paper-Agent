#!/bin/bash
# APPA Daily Greeting Script
# Claude Code驱动的每日问候和更新脚本

set -e  # Exit on any error

# 配置变量
APPA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$APPA_ROOT/logs/daily_$(date +%Y%m%d).log"
STATS_FILE="$APPA_ROOT/logs/stats.json"

# 确保日志目录存在
mkdir -p "$APPA_ROOT/logs"

# 记录脚本开始时间
echo "$(date '+%Y-%m-%d %H:%M:%S') - Daily greeting script started" >> "$LOG_FILE"

# 生成问候消息
generate_greeting() {
    local hour=$(date +%H)
    local date_str=$(date '+%Y年%m月%d日 %A')
    local greeting=""
    
    # 根据时间选择问候语
    if [ $hour -lt 12 ]; then
        greeting="🌅 早上好"
    elif [ $hour -lt 18 ]; then
        greeting="☀️ 下午好"
    else
        greeting="🌙 晚上好"
    fi
    
    echo "$greeting！今天是$date_str"
}

# 统计系统状态
collect_stats() {
    local total_papers=$(find "$APPA_ROOT/papers" -name "index.md" 2>/dev/null | wc -l)
    local total_topics=$(find "$APPA_ROOT/topics" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    local total_authors=$(find "$APPA_ROOT/authors" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    local total_venues=$(find "$APPA_ROOT/venues" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)
    
    # 检查是否有新增论文（过去24小时）
    local new_papers=$(find "$APPA_ROOT/papers" -name "index.md" -newermt "24 hours ago" 2>/dev/null | wc -l)
    
    # 生成统计JSON
    cat > "$STATS_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "total_papers": $total_papers,
    "total_topics": $total_topics,
    "total_authors": $total_authors,
    "total_venues": $total_venues,
    "new_papers_24h": $new_papers,
    "last_update": "$(date '+%Y-%m-%d')"
}
EOF
    
    echo "$total_papers,$total_topics,$total_authors,$total_venues,$new_papers"
}

# 查找今日推荐论文
find_recommended_papers() {
    local papers_dir="$APPA_ROOT/papers"
    local recommendations=""
    
    # 查找最近的高引用论文
    if [ -d "$papers_dir" ]; then
        # 简化版：查找最新的论文
        local latest_paper=$(find "$papers_dir" -name "index.md" -exec ls -t {} + | head -1)
        if [ -n "$latest_paper" ]; then
            local paper_title=$(grep "^#" "$latest_paper" | head -1 | sed 's/^# //')
            local paper_path=$(echo "$latest_paper" | sed "s|$APPA_ROOT/||")
            recommendations="📚 推荐阅读：[$paper_title]($paper_path)"
        fi
    fi
    
    echo "$recommendations"
}

# 生成每日摘要
generate_daily_summary() {
    local stats="$1"
    IFS=',' read -r total_papers total_topics total_authors total_venues new_papers <<< "$stats"
    
    echo "📊 APPA系统状态："
    echo "   📚 论文总数: $total_papers"
    echo "   🏷️ 主题分类: $total_topics"  
    echo "   👥 研究作者: $total_authors"
    echo "   📖 期刊会议: $total_venues"
    
    if [ "$new_papers" -gt 0 ]; then
        echo "   🆕 过去24小时新增: $new_papers 篇论文"
    else
        echo "   ✅ 系统数据已是最新状态"
    fi
    
    echo ""
    find_recommended_papers
}

# 检查是否需要更新
check_updates_needed() {
    # 简化检查：如果配置文件被修改，则需要更新
    local config_file="$APPA_ROOT/config.yaml"
    local last_update_file="$APPA_ROOT/logs/last_update.timestamp"
    
    if [ ! -f "$last_update_file" ]; then
        echo "首次运行，需要初始化"
        return 0
    fi
    
    if [ "$config_file" -nt "$last_update_file" ]; then
        echo "配置文件已更新，需要重新处理"
        return 0
    fi
    
    # 检查是否到了每日更新时间
    local today=$(date '+%Y-%m-%d')
    local last_update=$(cat "$last_update_file" 2>/dev/null || echo "")
    
    if [ "$today" != "$last_update" ]; then
        echo "日期已更新，执行每日更新"
        return 0
    fi
    
    return 1  # 不需要更新
}

# 主要执行流程
main() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Generating greeting and summary" >> "$LOG_FILE"
    
    # 生成问候
    echo "$(generate_greeting)"
    echo ""
    
    # 收集统计信息
    local stats=$(collect_stats)
    
    # 生成摘要
    generate_daily_summary "$stats"
    echo ""
    
    # 检查是否需要更新
    if check_updates_needed; then
        echo "🔄 检测到更新需求，建议运行论文更新..."
        echo "   可以说：'运行论文发现更新' 或 '获取最新PHM论文'"
    else
        echo "✅ 系统状态良好，无需更新"
    fi
    
    echo ""
    echo "💡 可用命令："
    echo "   📚 '显示所有论文' - 浏览论文库"
    echo "   🔍 '搜索深度学习论文' - 主题搜索"
    echo "   📊 '生成统计报告' - 详细分析"
    echo "   ⚙️ '系统配置状态' - 查看设置"
    
    # 记录成功完成
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Daily greeting completed successfully" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d')" > "$APPA_ROOT/logs/last_update.timestamp"
}

# 执行主流程
main "$@"