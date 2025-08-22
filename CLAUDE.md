# 🤖 CLAUDE.md - Claude Code专用配置

*APPA系统的Claude Code配置文件*

## 🚀 快速命令

| 命令 | 功能 | 脚本 |
|------|------|------|
| **每日问候** | 显示系统状态和推荐 | `./scripts/daily_greeting.sh` |
| **搜索论文** | 按条件查找论文 | `./scripts/search_papers.sh --help` |
| **显示所有论文** | 浏览完整论文库 | `./scripts/search_papers.sh --all` |
| **系统状态** | 查看统计信息 | `python main.py --status` |

## 📋 Claude Code工作流

### 1. 每日启动流程
```bash
# Claude可以直接执行
./scripts/daily_greeting.sh
```

### 2. 论文搜索示例
```bash
# 按年份搜索
./scripts/search_papers.sh --year 2024

# 按作者搜索  
./scripts/search_papers.sh --author zhang

# 按主题搜索
./scripts/search_papers.sh --topic deep-learning-phm

# 按关键词搜索
./scripts/search_papers.sh --keyword "bearing fault"
```

### 3. 内容管理
```bash
# 查看目录结构
ls -la papers/ topics/ authors/ venues/

# 统计信息
find papers -name "index.md" | wc -l
```

## 🛠️ Claude Code工具配置

### 📚 Paper Discovery Agent
**工具**: Bash, WebFetch, Grep, Write, TodoWrite
```bash
# API查询示例
curl -s "https://api.openalex.org/works?search=bearing+fault+diagnosis" | jq '.results[0]'
```

### 🌟 Daily Greeting Agent  
**工具**: Read, Bash, Write, WebSearch
```bash
# 每日问候
echo "🌅 $(date '+%A, %B %d') - PHM Daily Update"
```

### 🔍 Quality Curation Agent
**工具**: Read, Edit, WebFetch, Grep
```bash
# 质量检查
grep -r "引用数" papers/ | grep -v "0$"
```

### 📝 Content Analysis Agent
**工具**: Read, Write, Task, WebSearch  
```bash
# 分析摘要
head -20 papers/*/index.md | grep -A 5 "TL;DR"
```

### 🔗 Smart Linking Agent
**工具**: Edit, Grep, MultiEdit, Glob
```bash
# 查找链接
grep -r "\.md)" papers/ | head -5
```

## 📊 用户交互模式

### 🗣️ 自然语言命令映射
| 用户说话 | Claude执行 |
|----------|------------|
| "早上好，有什么新论文吗？" | `./scripts/daily_greeting.sh` |
| "搜索深度学习相关论文" | `./scripts/search_papers.sh --topic deep-learning-phm` |
| "显示2024年的所有论文" | `./scripts/search_papers.sh --year 2024` |
| "查找张伟的论文" | `./scripts/search_papers.sh --author zhang` |
| "最近一周有什么更新？" | `./scripts/search_papers.sh --recent 7` |

### 📈 智能响应模板
```markdown
Claude响应格式：
1. 🎯 直接回答用户问题
2. 📊 提供相关统计信息  
3. 🔗 给出相关链接
4. 💡 建议下一步操作
```

## 🔧 系统配置

### 📂 目录结构
```
APPA/
├── papers/YYYY/YYYY-VENUE-Author-Title/
│   ├── index.md          # 论文详情页
│   └── refs.bib          # BibTeX引用
├── topics/topic-name/
│   └── README.md         # 主题概览
├── authors/author-name/
│   └── README.md         # 作者资料
├── venues/venue-name/
│   └── README.md         # 期刊信息
├── indices/              # 各种索引
├── scripts/              # Claude Code脚本
└── logs/                 # 日志和状态
```

### 🔗 链接格式规范
```markdown
# GitHub友好的相对路径链接
[论文标题](../papers/2024/2024-MSSP-Zhang-DeepLearning/index.md)
[主题页面](../topics/deep-learning-phm/README.md) 
[作者页面](../authors/zhang-wei/README.md)
[期刊页面](../venues/mssp/README.md)
```

### 📅 自动化调度
```bash
# 每日9点执行问候
0 9 * * * cd ~/APPA && ./scripts/daily_greeting.sh

# 每周日执行全量更新
0 1 * * 0 cd ~/APPA && python main.py --incremental
```

## 🎯 Claude Code执行模式

### 模式1: 交互式对话
```
用户: "帮我找一下轴承故障诊断的论文"
Claude: [执行] ./scripts/search_papers.sh --keyword "bearing fault"
        [分析] 找到1篇相关论文
        [展示] 论文链接和摘要
        [建议] 是否需要查看详细分析？
```

### 模式2: 主动服务
```
Claude: [定时执行] ./scripts/daily_greeting.sh
        [检测] 发现新增论文
        [通知] 主动推荐给用户
        [等待] 用户进一步指令
```

### 模式3: 深度分析
```
用户: "分析一下深度学习在PHM中的发展趋势"
Claude: [读取] topics/deep-learning-phm/README.md
        [统计] 论文数量和引用情况
        [分析] 技术发展脉络
        [生成] 趋势分析报告
```

## 🔍 调试和监控

### 📊 状态检查
```bash
# 检查系统状态
ls -la logs/
cat logs/stats.json
tail -20 logs/appa.log
```

### 🐛 常见问题
1. **脚本权限**: `chmod +x scripts/*.sh`
2. **路径问题**: 确保在APPA根目录执行
3. **依赖检查**: `python main.py --status`

## 💡 扩展建议

### 🚀 未来功能
- **语音交互**: 集成语音识别和合成
- **可视化**: 论文关系网络图表
- **推荐算法**: 基于用户兴趣的智能推荐
- **多语言**: 支持中英文双语界面

### 🔗 集成可能
- **Obsidian**: 导出为知识图谱
- **Zotero**: 自动同步参考文献
- **Slack/Teams**: 团队协作通知
- **Jupyter**: 交互式数据分析

---

*📅 配置更新: 2024-01-22 | 🤖 专为Claude Code优化*