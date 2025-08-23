#!/bin/bash
# APPA Enhanced Paper Search Script
# Claude Code驱动的增强型论文搜索和发现系统

set -e

APPA_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 显示帮助信息
show_help() {
    echo "🔍 APPA增强型论文搜索和发现工具"
    echo ""
    echo "用法:"
    echo "  $0 [选项] [搜索词]"
    echo ""
    echo "本地搜索选项:"
    echo "  --year YEAR           按年份搜索 (如: 2024)"
    echo "  --author AUTHOR       按作者搜索 (如: zhang)"
    echo "  --topic TOPIC         按主题搜索 (如: deep-learning)"
    echo "  --venue VENUE         按期刊搜索 (如: mssp)"
    echo "  --keyword KEYWORD     按关键词搜索"
    echo "  --citations MIN       最小引用数 (如: 10)"
    echo "  --recent DAYS         最近N天的论文 (如: 30)"
    echo "  --all                 显示所有论文"
    echo ""
    echo "在线发现选项 (使用增强型MCP系统):"
    echo "  --discover            启动在线论文发现模式"
    echo "  --fetch-recent        获取最新PHM论文"
    echo "  --demo                运行演示模式"
    echo ""
    echo "  --help                显示此帮助信息"
    echo ""
    echo "本地搜索示例:"
    echo "  $0 --year 2024                    # 2024年的所有论文"
    echo "  $0 --author zhang                 # 作者包含zhang的论文"
    echo "  $0 --topic deep-learning          # 深度学习相关论文"
    echo "  $0 --keyword \"bearing fault\"      # 关键词搜索"
    echo "  $0 --citations 15                 # 引用数>=15的论文"
    echo "  $0 --recent 7                     # 最近7天的论文"
    echo ""
    echo "在线发现示例:"
    echo "  $0 --discover                     # 交互式论文发现"
    echo "  $0 --fetch-recent                 # 获取2025年最新论文"
    echo "  $0 --demo                         # 运行系统演示"
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

# 在线论文发现模式
discover_papers_online() {
    echo "🌐 启动增强型在线论文发现系统..."
    echo ""
    echo "请选择发现模式:"
    echo "1. 获取2025年5月后的最新PHM论文"
    echo "2. 搜索特定关键词的论文"
    echo "3. 运行完整演示"
    echo ""
    read -p "请选择 (1-3): " choice
    
    case "$choice" in
        1)
            echo "🚀 正在获取最新PHM论文..."
            python3 "$APPA_ROOT/scripts/fetch_recent_papers.py" --date-after "2025-05-01" --analyze --max-results 10
            ;;
        2)
            echo "请输入搜索关键词 (用空格分隔):"
            read -p "> " keywords
            echo "🔍 正在搜索关键词: $keywords"
            python3 "$APPA_ROOT/scripts/fetch_recent_papers.py" --keywords $keywords --analyze --max-results 15
            ;;
        3)
            echo "🎭 运行完整系统演示..."
            python3 "$APPA_ROOT/scripts/fetch_recent_papers.py" --demo --analyze
            ;;
        *)
            echo "❌ 无效选择"
            return 1
            ;;
    esac
}

# 快速获取最新论文
fetch_recent_papers() {
    echo "🆕 获取2025年最新PHM论文..."
    echo ""
    
    # 检查Python脚本是否存在
    if [ ! -f "$APPA_ROOT/scripts/fetch_recent_papers.py" ]; then
        echo "❌ 增强型发现脚本未找到"
        echo "💡 请确保系统已正确安装并配置"
        return 1
    fi
    
    # 运行Python脚本获取最新论文
    echo "🔄 正在从学术数据库获取最新论文..."
    python3 "$APPA_ROOT/scripts/fetch_recent_papers.py" \
        --date-after "2025-05-01" \
        --keywords "prognostics" "health management" "fault diagnosis" "predictive maintenance" \
        --max-results 20 \
        --analyze \
        --output "logs/latest_papers_$(date +%Y%m%d).json"
    
    echo ""
    echo "✅ 最新论文获取完成！"
    echo "📄 结果已保存到 logs/latest_papers_$(date +%Y%m%d).json"
}

# 运行演示模式
run_demo_mode() {
    echo "🎭 APPA增强系统演示模式"
    echo ""
    
    # 检查依赖
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 未安装"
        return 1
    fi
    
    echo "🚀 启动演示..."
    echo "这将展示以下功能:"
    echo "• 🔍 在线论文发现"
    echo "• 📊 智能内容分析"
    echo "• 🎯 PHM相关性评估"
    echo "• 📝 多语言TL;DR生成"
    echo ""
    
    python3 "$APPA_ROOT/scripts/fetch_recent_papers.py" --demo --verbose
    
    echo ""
    echo "🎉 演示完成！"
    echo "💡 您可以使用 --discover 进入交互模式"
}

# 检查增强功能可用性
check_enhanced_features() {
    echo "🔧 检查增强功能状态..."
    echo ""
    
    # 检查Python脚本
    if [ -f "$APPA_ROOT/scripts/fetch_recent_papers.py" ]; then
        echo "✅ 增强型发现脚本: 可用"
    else
        echo "❌ 增强型发现脚本: 不可用"
    fi
    
    # 检查Python依赖
    if command -v python3 &> /dev/null; then
        echo "✅ Python3: 可用"
    else
        echo "❌ Python3: 不可用"
    fi
    
    # 检查目录结构
    if [ -d "$APPA_ROOT/src/agents" ]; then
        echo "✅ 增强型代理: 可用"
    else
        echo "❌ 增强型代理: 不可用"
    fi
    
    # 统计现有论文
    local paper_count=$(find "$APPA_ROOT/papers" -name "index.md" 2>/dev/null | wc -l)
    echo "📊 本地论文数量: $paper_count"
    
    echo ""
    echo "💡 使用 --discover 或 --demo 体验增强功能"
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
        --discover)
            discover_papers_online
            ;;
        --fetch-recent)
            fetch_recent_papers
            ;;
        --demo)
            run_demo_mode
            ;;
        --check)
            check_enhanced_features
            ;;
        *)
            echo "❌ 未知选项: $1"
            echo "使用 --help 查看帮助信息"
            ;;
    esac
}

# 执行主函数
main "$@"