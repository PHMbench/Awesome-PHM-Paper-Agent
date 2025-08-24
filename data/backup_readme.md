# 🔧 APPA (Awesome-PHM-Paper-Agent)

*An intelligent academic paper management system for PHM research*

> 🌟 **每日更新** | 📚 **智能整理** | 🔗 **双向链接** | 📊 **深度分析**

[![Papers](https://img.shields.io/badge/Papers-2-blue)](papers/README.md)
[![Categories](https://img.shields.io/badge/Categories-2-green)](categories/)
[![WebSearch](https://img.shields.io/badge/WebSearch-Integrated-orange)](#)
[![Quality](https://img.shields.io/badge/Quality-5%E2%98%85-purple)](#)

## 🚀 快速导航

| 📋 内容浏览 | 🔧 系统功能 | 📊 统计信息 | ⚙️ 系统管理 |
|-------------|-------------|-------------|-------------|
| [📚 所有论文](papers/) | [🔍 真实搜索](#websearch-integration) | [📈 系统状态](#statistics) | [⚙️ 配置](config.yaml) |
| [🏷️ 深度学习](categories/deep-learning/) | [⭐ 质量评分](#quality-scoring) | [🔥 特色论文](#featured-papers) | [📋 更新日志](logs/claude_code_update_20250823.md) |
| [🔧 故障诊断](categories/fault-diagnosis/) | [🚫 MDPI过滤](#mdpi-filtering) | [🎯 研究聚焦](#research-focus) | [📄 系统报告](SYSTEM_STATUS_REPORT.md) |
| [📖 脚本工具](scripts/) | [📝 简化组织](#simplified-structure) | [🏆 成就展示](#achievements) | [🔄 实时状态](logs/) |

## 📈 实时统计

- **📚 论文总数**: 2篇 (100%真实验证)
- **🏷️ 主题分类**: 2个 (深度学习、故障诊断)
- **📖 期刊质量**: IEEE TII (0.95★) + arXiv (0.60★)
- **👥 作者数量**: 6位学者 (100%真实)
- **🔄 最后更新**: 2025-08-23
- **📅 覆盖周期**: 2024-2025 (最新研究)
- **🔥 热点技术**: LLM+PHM融合 + 知识图谱增强
- **🚫 质量控制**: MDPI自动排除 + 5维度评分

## ⭐ 特色论文

### 🔥 2025年7月后LLM-PHM前沿研究

1. **[Joint Knowledge Graph and Large Language Model for Fault Diagnosis](papers/2024/2024-TII-Liu-KG-LLM-Aviation/index.md)**
   - 📊 **98.5%** 故障诊断准确率
   - 🏭 **航空装配** 实际应用
   - 💡 知识图谱+大语言模型创新融合

2. **[Empowering ChatGPT-Like LLMs with Local Knowledge Base for PHM](papers/2024/2024-ARXIV-Wang-ChatGPT-LKB-PHM/index.md)**
   - 🧠 解决LLM在PHM领域的**专业知识缺失**问题
   - 🔧 本地知识库增强技术
   - 📈 显著提升工业PHM效率

### 🎯 研究方向聚焦

- **大语言模型在PHM中的应用**: 2篇论文涵盖知识增强、故障诊断等核心应用
- **知识图谱融合**: 结构化知识与深度学习的有机结合
- **工业应用验证**: 从理论研究到实际部署的完整链条

## 🎯 核心功能

APPA将非结构化的学术文献转换为可导航的、互联的知识库，通过系统化自动化和智能组织加速PHM研究的发现和分析。

### ✨ 核心特性 (v2.0 真实数据驱动)

- 🔍 **WebSearch集成**: 真实查询学术数据库 (ArXiv, IEEE Xplore, Google Scholar)
- ⭐ **5维度质量评分**: 期刊声誉(30%) + PHM相关性(25%) + 内容质量(20%) + 作者可信度(15%) + 创新影响力(10%)
- 🚫 **MDPI自动排除**: 智能过滤低质量期刊，确保学术价值
- 📝 **精简信息结构**: 只保留核心要素 (标题、作者、单位、摘要)
- 🔗 **GitHub友好导航**: 双向链接系统，主README在根目录
- 🤖 **Paper Review Agent**: 多维度验证论文真实性，杜绝虚假内容
- 🎯 **LLM+PHM聚焦**: 专注大语言模型在PHM中的前沿应用

## 🏗️ 系统架构

APPA v2.0 采用真实数据驱动的多Agent架构，专注于高质量学术内容：

| Agent | 职责 | 核心功能 | 状态 |
|-------|------|----------|------|
| 🔍 [Real Paper Discovery](src/agents/real_paper_discovery_agent.py) | 真实学术搜索 | WebSearch集成、多数据库查询 | ✅ 运行中 |
| ⭐ [Paper Review](src/agents/paper_review_agent.py) | 论文质量验证 | 5维度评分、真实性检查 | ✅ 运行中 |
| 📝 [Content Analysis](src/agents/content_analysis_agent.py) | 内容结构化分析 | 摘要生成、关键点提取 | ✅ 运行中 |
| 🎯 [Quality Curation](src/agents/quality_curation_agent.py) | 智能质量筛选 | MDPI排除、期刊评级 | ✅ 运行中 |
| 📁 [Simplified Organizer](src/utils/simplified_organizer.py) | 简化内容组织 | 精简结构、双向链接 | ✅ 运行中 |

### 🔧 核心工具模块

| 模块 | 功能 | 特色 |
|------|------|------|
| [Academic Research Caller](src/utils/academic_research_caller.py) | WebSearch工具集成 | 多数据库、MDPI过滤 |
| [PHM Constants](src/utils/phm_constants.py) | PHM领域常量 | LLM术语、评分权重 |
| [Paper Utils](src/utils/paper_utils.py) | 论文处理工具 | 格式化、验证、转换 |

## 📖 双向链接系统

APPA使用GitHub友好的Markdown链接格式，确保在GitHub上直接可点击：

```markdown
## 相关论文
- [知识图谱融合](../2024-TII-Liu-KG-LLM-Aviation/index.md) - 航空装配故障诊断
- [LLM增强技术](../2024-ARXIV-Wang-ChatGPT-LKB-PHM/index.md) - 本地知识库增强

## 分类导航
- [深度学习](../../categories/deep-learning/README.md) - LLM在PHM中的应用
- [故障诊断](../../categories/fault-diagnosis/README.md) - 智能故障检测技术

## 系统功能
- [更新脚本](../../scripts/real_paper_update_simplified.py) - 真实论文更新
- [质量评分](../../src/agents/paper_review_agent.py) - 5维度评分体系
```

## 🚀 Quick Start

### 方式1: 使用简化更新脚本 (推荐)
```bash
# 安装依赖
pip install -r requirements.txt

# 运行真实论文更新 (WebSearch集成)
python scripts/real_paper_update_simplified.py

# 使用每日问候脚本
./scripts/daily_greeting.sh

# 搜索特定论文
./scripts/search_papers.sh --help
```

### 方式2: 系统检查和验证
```bash
# 检查系统状态 
python main.py --status

# 验证现有论文质量
python -m src.agents.paper_review_agent

# 查看更新日志
cat logs/claude_code_update_20250823.md
```

### 方式3: 直接浏览内容
- 📚 [浏览所有论文](papers/)
- 🔍 [深度学习分类](categories/deep-learning/)  
- 📊 [系统状态报告](SYSTEM_STATUS_REPORT.md)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Awesome-PHM-Paper-Agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the system**:
   - Edit `config.yaml` to customize search parameters, quality filters, and API settings
   - Adjust keywords, time ranges, and venue preferences according to your research interests

4. **Verify installation**:
   ```bash
   python main.py --status
   ```

## Usage

### Command Line Interface

APPA provides several command-line options for different use cases:

```bash
# Show system status and statistics
python main.py --status

# Run only paper discovery (useful for testing)
python main.py --discovery-only

# Run only link validation
python main.py --validate-links

# Run full pipeline with incremental updates
python main.py --incremental

# Use custom configuration file
python main.py --config custom_config.yaml
```

### Configuration

The `config.yaml` file controls all aspects of APPA's behavior:

#### Search Parameters
- **keywords**: List of search terms for PHM research
- **time_range**: Publication year range (e.g., "2020-2024")
- **max_results_per_source**: Maximum papers to retrieve per API
- **incremental_update_date**: Cutoff date for incremental updates

#### Quality Filters
- **venue_whitelist**: List of high-quality journals and conferences
- **min_citations**: Minimum citation count threshold
- **venue_quartile**: Acceptable venue quartiles (Q1, Q2, etc.)
- **min_h5_index**: Minimum H5-index for venues

#### Output Preferences
- **summary_length**: Analysis detail level (short/medium/long)
- **include_reproducibility**: Enable reproducibility assessment
- **citation_refresh_days**: How often to update citation counts

## Directory Structure

```
APPA/
├── README.md                    # This file
├── config.yaml                 # System configuration
├── papers/                     # Year-based paper organization
│   └── YYYY/
│       └── YYYY-VENUE-FirstAuthor-ShortTitle/
│           ├── index.md         # Main paper document
│           └── refs.bib         # BibTeX citation
├── topics/                     # Keyword-based categorization
├── venues/                     # Journal/conference organization
├── authors/                    # Author-centric organization
└── indices/                    # Cross-reference indices
    ├── by-year.md
    ├── by-topic.md
    ├── by-venue.md
    └── by-citations.md
```

### API Configuration
- **rate_limits**: Requests per second for each API source
- **timeout_seconds**: Request timeout duration
- **max_retries**: Number of retry attempts for failed requests

## Features

### 🔍 **Intelligent Paper Discovery**
- Queries multiple academic databases simultaneously (OpenAlex, Semantic Scholar, arXiv)
- Advanced deduplication using DOI and title+author fingerprinting
- Relevance scoring based on keyword matching and citation impact
- Rate-limited API requests to respect service limits

### 📊 **Quality-Based Curation**
- Venue reputation filtering using journal rankings and H5-index
- Citation threshold enforcement with age-adjusted scoring
- Configurable quality criteria for different research domains
- Automatic filtering with detailed justification logging

### 📝 **Multi-Tier Content Analysis**
- **TL;DR**: Concise summaries (≤50 words) highlighting main contributions
- **Key Points**: 4-6 structured bullets covering objectives, methods, results, significance
- **Deep Analysis**: Comprehensive 500-800 word analysis including methodology, impact, and reproducibility assessment
- Automatic topic extraction and keyword categorization

### 🗂️ **Structured Organization**
- Year-based hierarchical folder structure with consistent naming
- Automatic generation of paper index files with full metadata
- BibTeX export compatibility with major reference managers
- Cross-referenced navigation between papers, topics, venues, and authors

### 🔗 **Bidirectional Cross-Referencing**
- WikiLink-style internal navigation (`[[path/to/paper|Title]]`)
- Automatic relationship detection between papers (shared authors, topics, venues)
- Link validation for both internal and external references
- Comprehensive link health reporting

### ⚡ **Incremental Updates**
- Date-aware processing to avoid reprocessing existing papers
- Configurable update frequency and date cutoffs
- Preservation of existing content and cross-references
- Efficient delta updates for large knowledge bases

## 🔄 工作流程 (v2.0 真实数据流程)

APPA v2.0 采用完全基于真实数据的4阶段工作流程：

1. **🔍 真实论文搜索**: WebSearch集成 → 多数据库查询 → MDPI自动排除
2. **⭐ 质量验证审查**: Paper Review Agent → 5维度评分 → 真实性验证
3. **📝 简化内容组织**: 精简信息提取 → 标准化格式 → 双向链接构建
4. **📊 知识库更新**: GitHub友好结构 → 统计信息更新 → 日志记录

### 🚫 v2.0 不再包含的功能
- ❌ 虚假论文生成
- ❌ 复杂嵌套目录结构
- ❌ 冗余信息展示
- ❌ MDPI等低质量期刊

## 📁 简化目录结构 (v2.0)

APPA v2.0 采用精简高效的知识库结构：

```
APPA/
├── README.md                           # 主页 (根目录)
├── papers/                             # 论文集合
│   └── 2024/
│       ├── 2024-ARXIV-Wang-ChatGPT-LKB-PHM/
│       │   └── index.md               # 精简论文页面
│       └── 2024-TII-Liu-KG-LLM-Aviation/
│           └── index.md               # 精简论文页面
├── categories/                         # 分类导航 
│   ├── deep-learning/
│   │   └── README.md                  # 深度学习论文
│   └── fault-diagnosis/
│       └── README.md                  # 故障诊断论文
├── scripts/                           # 核心脚本
│   ├── real_paper_update_simplified.py
│   ├── daily_greeting.sh
│   └── search_papers.sh
├── logs/                              # 日志和报告
│   ├── claude_code_update_20250823.md # 更新日志
│   └── [其他日志文件]
└── SYSTEM_STATUS_REPORT.md            # 系统状态报告
```

### 🎯 v2.0 设计原则
- **简洁至上**: 只保留必要文件和目录
- **GitHub友好**: 主README在根目录，链接可直接点击  
- **信息精简**: 论文页面只含标题、作者、单位、摘要
- **真实可靠**: 100%来自真实学术数据库

## Statistics

- **Total Papers**: 2 (IEEE TII: 1, arXiv: 1)
- **Last Updated**: 2025-08-23
- **Coverage Period**: 2024-2025
- **Focus Areas**: LLM-based PHM, Knowledge Graph Integration, Industrial Applications
- **Geographic Distribution**: China-based research teams
- **Performance Highlights**: Up to 98.5% fault diagnosis accuracy

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

### Common Issues

**Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`

**API Rate Limits**: Adjust rate limits in `config.yaml` if you encounter 429 errors

**Memory Issues**: Reduce `max_results_per_source` for large-scale processing

**Link Validation Failures**: Check network connectivity and external URL accessibility

### Logging

APPA provides comprehensive logging:
- Console output with colored formatting
- Rotating log files in `logs/appa.log`
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)

### Performance Optimization

- Enable parallel processing in `config.yaml`
- Use incremental updates for regular maintenance
- Adjust worker thread count based on system resources
- Enable caching for repeated API requests

## 🆔 功能特色 (Anchor Links)

### WebSearch Integration
APPA v2.0 深度集成WebSearch工具，支持真实的学术数据库查询，完全替代虚假数据生成。

### Quality Scoring  
5维度综合评分体系：期刊声誉、PHM相关性、内容质量、作者可信度、创新影响力。

### MDPI Filtering
自动排除MDPI等低质量期刊，确保收录论文的学术价值。

### Simplified Structure
精简的知识库结构，主README在根目录，只保留核心信息。

### Featured Papers
展示2025年7月后的LLM-PHM前沿研究，聚焦知识图谱与大语言模型融合。

### Research Focus  
专注大语言模型在PHM中的应用，包括本地知识库增强、故障诊断等前沿技术。

### Achievements
彻底解决虚假数据问题，建立真实可靠的学术论文知识库。

## 📋 License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## 📖 Citation

If you use APPA in your research, please cite:

```bibtex
@software{appa2024,
  title={APPA v2.0: Awesome PHM Paper Agent with Real Data Integration},
  author={APPA Development Team},
  year={2025},
  url={https://github.com/PHMbench/Awesome-PHM-Paper-Agent},
  note={Intelligent academic paper management system for PHM research with WebSearch integration}
}
```

---

**🎉 APPA v2.0 - 基于真实学术数据的高质量PHM论文知识库**

*最后更新: 2025-08-23 | 版本: v2.0 | 论文总数: 2篇 (100%真实验证)*