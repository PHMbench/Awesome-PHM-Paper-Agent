#!/bin/bash
# APPA Paper Search Script
# Claude Code驱动的论文搜索和范围查询脚本

set -e

APPA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 显示帮助信息
show_help() {
    echo "APPA论文搜索工具"
    echo ""
    echo "用法:"
    echo "  $0 [选项] [搜索词]"
    echo ""
    echo "选项:"
    echo "  --year YEAR           按年份搜索 (如: 2024)"
    echo "  --author AUTHOR       按作者搜索 (如: zhang)"
    echo "  --topic TOPIC         按主题搜索 (如: deep-learning)"
    echo "  --venue VENUE         按期刊搜索 (如: mssp)"
    echo "  --keyword KEYWORD     按关键词搜索"
    echo "  --citations MIN       最小引用数 (如: 10)"
    echo "  --recent DAYS         最近N天的论文 (如: 30)"
    echo "  --all                 显示所有论文"
    echo "  --help                显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 --year 2024                    # 2024年的所有论文"
    echo "  $0 --author zhang                 # 作者包含zhang的论文"
    echo "  $0 --topic deep-learning          # 深度学习相关论文"
    echo "  $0 --keyword \"bearing fault\"      # 关键词搜索"
    echo "  $0 --citations 15                 # 引用数>=15的论文"
    echo "  $0 --recent 7                     # 最近7天的论文"
}

# 按年份搜索
search_by_year() {
    local year="$1"
    echo "🗓️ 搜索${year}年的论文..."
    echo ""
    
    local year_dir="$APPA_ROOT/papers/$year"
    if [ ! -d "$year_dir" ]; then
        echo "❌ 未找到${year}年的论文"
        return 1
    fi
    
    local count=0
    for paper_dir in "$year_dir"/*; do
        if [ -d "$paper_dir" ] && [ -f "$paper_dir/index.md" ]; then
            count=$((count + 1))
            local title=$(grep "^#" "$paper_dir/index.md" | head -1 | sed 's/^# //')
            local rel_path=$(echo "$paper_dir/index.md" | sed "s|$APPA_ROOT/||")
            echo "$count. [$title]($rel_path)"
        fi
    done
    
    echo ""
    echo "📊 共找到 $count 篇${year}年的论文"
}

# 按作者搜索
search_by_author() {
    local author="$1"
    echo "👤 搜索作者'$author'的论文..."
    echo ""
    
    local count=0
    find "$APPA_ROOT/papers" -name "index.md" -exec grep -l "$author" {} \; | while read -r file; do
        count=$((count + 1))
        local title=$(grep "^#" "$file" | head -1 | sed 's/^# //')
        local rel_path=$(echo "$file" | sed "s|$APPA_ROOT/||")
        echo "$count. [$title]($rel_path)"
    done
}

# 按主题搜索
search_by_topic() {
    local topic="$1"
    echo "🏷️ 搜索主题'$topic'的论文..."
    echo ""
    
    local topic_file="$APPA_ROOT/topics/$topic/README.md"
    if [ -f "$topic_file" ]; then
        echo "📖 主题详情: [查看$topic主题页面](topics/$topic/README.md)"
        echo ""
        # 从主题页面提取论文列表
        grep -n "^\*\*\[.*\](" "$topic_file" | while IFS=':' read -r line_num content; do
            echo "• $content"
        done
    else
        echo "❌ 主题'$topic'不存在"
        echo "💡 可用主题:"
        ls "$APPA_ROOT/topics" 2>/dev/null | head -5
    fi
}

# 按关键词搜索
search_by_keyword() {
    local keyword="$1"
    echo "🔍 搜索包含关键词'$keyword'的论文..."
    echo ""
    
    local count=0
    find "$APPA_ROOT/papers" -name "index.md" -exec grep -il "$keyword" {} \; | while read -r file; do
        count=$((count + 1))
        local title=$(grep "^#" "$file" | head -1 | sed 's/^# //')
        local rel_path=$(echo "$file" | sed "s|$APPA_ROOT/||")
        local context=$(grep -i "$keyword" "$file" | head -1 | sed 's/^[[:space:]]*//')
        echo "$count. [$title]($rel_path)"
        echo "   💡 匹配内容: $context"
        echo ""
    done
}

# 按引用数搜索
search_by_citations() {
    local min_citations="$1"
    echo "📊 搜索引用数≥${min_citations}的论文..."
    echo ""
    
    local count=0
    find "$APPA_ROOT/papers" -name "index.md" | while read -r file; do
        local citations=$(grep "引用数" "$file" | grep -o '[0-9]\+' | head -1)
        if [ -n "$citations" ] && [ "$citations" -ge "$min_citations" ]; then
            count=$((count + 1))
            local title=$(grep "^#" "$file" | head -1 | sed 's/^# //')
            local rel_path=$(echo "$file" | sed "s|$APPA_ROOT/||")
            echo "$count. [$title]($rel_path) - 引用数: $citations"
        fi
    done
}

# 显示所有论文
show_all_papers() {
    echo "📚 所有论文列表:"
    echo ""
    
    local total=0
    for year_dir in "$APPA_ROOT/papers"/*; do
        if [ -d "$year_dir" ]; then
            local year=$(basename "$year_dir")
            echo "### $year年"
            local year_count=0
            
            for paper_dir in "$year_dir"/*; do
                if [ -d "$paper_dir" ] && [ -f "$paper_dir/index.md" ]; then
                    year_count=$((year_count + 1))
                    total=$((total + 1))
                    local title=$(grep "^#" "$paper_dir/index.md" | head -1 | sed 's/^# //')
                    local rel_path=$(echo "$paper_dir/index.md" | sed "s|$APPA_ROOT/||")
                    echo "$year_count. [$title]($rel_path)"
                fi
            done
            echo ""
        fi
    done
    
    echo "📊 论文总数: $total"
}

# 最近N天的论文
search_recent_papers() {
    local days="$1"
    echo "🆕 最近${days}天的论文..."
    echo ""
    
    local count=0
    find "$APPA_ROOT/papers" -name "index.md" -newermt "$days days ago" | while read -r file; do
        count=$((count + 1))
        local title=$(grep "^#" "$file" | head -1 | sed 's/^# //')
        local rel_path=$(echo "$file" | sed "s|$APPA_ROOT/||")
        local mod_date=$(stat -c %y "$file" | cut -d' ' -f1)
        echo "$count. [$title]($rel_path) - 更新于: $mod_date"
    done
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        show_help
        return 0
    fi
    
    case "$1" in
        --help|-h)
            show_help
            ;;
        --year)
            if [ -n "$2" ]; then
                search_by_year "$2"
            else
                echo "❌ 请指定年份"
            fi
            ;;
        --author)
            if [ -n "$2" ]; then
                search_by_author "$2"
            else
                echo "❌ 请指定作者名称"
            fi
            ;;
        --topic)
            if [ -n "$2" ]; then
                search_by_topic "$2"
            else
                echo "❌ 请指定主题名称"
            fi
            ;;
        --keyword)
            if [ -n "$2" ]; then
                search_by_keyword "$2"
            else
                echo "❌ 请指定搜索关键词"
            fi
            ;;
        --citations)
            if [ -n "$2" ]; then
                search_by_citations "$2"
            else
                echo "❌ 请指定最小引用数"
            fi
            ;;
        --recent)
            if [ -n "$2" ]; then
                search_recent_papers "$2"
            else
                echo "❌ 请指定天数"
            fi
            ;;
        --all)
            show_all_papers
            ;;
        *)
            echo "❌ 未知选项: $1"
            echo "使用 --help 查看帮助信息"
            ;;
    esac
}

# 执行主函数
main "$@"