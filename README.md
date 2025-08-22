# 🔧 APPA (Awesome-PHM-Paper-Agent)

*An intelligent academic paper management system for PHM research*

> 🌟 **每日更新** | 📚 **智能整理** | 🔗 **双向链接** | 📊 **深度分析**

[![Papers](https://img.shields.io/badge/Papers-0-blue)](papers/README.md)
[![Topics](https://img.shields.io/badge/Topics-10-green)](topics/README.md)
[![Venues](https://img.shields.io/badge/Venues-15-orange)](venues/README.md)
[![Authors](https://img.shields.io/badge/Authors-0-purple)](authors/README.md)

## 🚀 快速导航

| 📋 分类浏览 | 📊 统计索引 | 🔍 专项查询 | ⚙️ 系统管理 |
|-------------|-------------|-------------|-------------|
| [📚 所有论文](papers/README.md) | [📅 按年份](indices/by-year.md) | [🔥 热门主题](topics/README.md) | [⚙️ 配置](config.yaml) |
| [🏷️ 研究主题](topics/README.md) | [📊 按引用](indices/by-citations.md) | [⭐ 高影响力](indices/by-citations.md) | [📋 任务状态](logs/appa.log) |
| [📖 期刊会议](venues/README.md) | [🏢 按期刊](indices/by-venue.md) | [🆕 最新发表](indices/by-year.md) | [🔄 更新历史](logs/) |
| [👥 研究作者](authors/README.md) | [🏷️ 按主题](indices/by-topic.md) | [🔗 相关性网络](papers/README.md) | [📈 系统状态](#statistics) |

## 📈 实时统计

- **📚 论文总数**: 0
- **🏷️ 主题分类**: 10
- **📖 期刊会议**: 15
- **👥 作者数量**: 0
- **🔄 最后更新**: 未初始化
- **📅 覆盖周期**: 未配置

## 🎯 核心功能

APPA将非结构化的学术文献转换为可导航的、互联的知识库，通过系统化自动化和智能组织加速PHM研究的发现和分析。

### ✨ 核心特性

- 🔍 **自动论文发现**: 查询多个学术数据库 (OpenAlex, IEEE Xplore, Semantic Scholar, arXiv)
- ⭐ **质量筛选**: 基于期刊声誉、引用指标和质量阈值的智能过滤
- 📝 **结构化分析**: 生成三层次摘要 (TL;DR, 关键点, 深度分析)
- 🔗 **交叉引用导航**: GitHub友好的双向链接系统，实现无缝知识探索
- 🔄 **增量更新**: 基于日期的智能处理，避免重复并保持内容最新
- 📋 **BibTeX兼容**: 与参考文献管理工具完全集成

## 🏗️ 系统架构

APPA采用解耦的多Agent架构，每个Agent都有明确定义的单一职责：

| Agent | 职责 | 工具 | 状态 |
|-------|------|------|------|
| 📚 [Paper Discovery](src/agents/paper_discovery_agent.py) | API查询和去重 | Bash, WebFetch, Grep | ✅ 运行中 |
| ⭐ [Quality Curation](src/agents/quality_curation_agent.py) | 基于质量指标过滤 | Read, Edit, WebFetch | ✅ 运行中 |
| 📝 [Content Analysis](src/agents/content_analysis_agent.py) | 生成结构化摘要 | LLM, Read, Write | ✅ 运行中 |
| 🗂️ [File Organization](src/agents/filesystem_organization_agent.py) | 维护标准目录结构 | Write, LS, MultiEdit | ✅ 运行中 |
| 🔗 [Cross-Reference Linking](src/agents/cross_reference_linking_agent.py) | 实现双向导航 | Edit, Grep, MultiEdit | ✅ 运行中 |

## 📖 双向链接系统

APPA使用GitHub友好的Markdown链接格式，确保在GitHub上直接可点击：

```markdown
## 相关论文
- [相似方法论](../2024-TIE-Liu-TransformerFault/index.md) - 基于Transformer的故障诊断
- [同领域应用](../../2023/2023-REL-Wang-BearingDiagnosis/index.md) - 轴承故障诊断研究
- [作者其他工作](../../../authors/zhang-wei/README.md) - 张伟的研究概览

## 主题标签
- [深度学习](../../topics/deep-learning.md)
- [故障诊断](../../topics/fault-diagnosis.md)
- [轴承监测](../../topics/bearing-monitoring.md)
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Check system status
python main.py --status

# Run paper discovery only (recommended for first test)
python main.py --discovery-only

# Run full pipeline
python main.py

# Run incremental update
python main.py --incremental
```

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

## Workflow

APPA follows a sequential 5-phase workflow:

1. **Paper Discovery**: Query APIs → Deduplicate → Score relevance
2. **Quality Curation**: Apply filters → Rank by quality → Generate justifications
3. **Content Analysis**: Extract metadata → Generate summaries → Assess reproducibility
4. **File Organization**: Create folders → Generate index files → Organize by categories
5. **Cross-Referencing**: Build relationships → Create links → Validate references

Each phase has clear input/output specifications and can be run independently for testing and debugging.

## Output Structure

After processing, APPA creates a comprehensive knowledge base:

```
APPA/
├── papers/2024/2024-MSSP-Smith-DeepLearningFault/
│   ├── index.md          # Complete paper analysis
│   └── refs.bib          # BibTeX citation
├── topics/deep-learning/
│   └── README.md         # Topic overview with related papers
├── venues/mssp/
│   └── README.md         # Venue profile and publications
├── authors/smith-john/
│   └── README.md         # Author profile and works
└── indices/
    ├── by-year.md        # Chronological index
    ├── by-topic.md       # Thematic index
    ├── by-venue.md       # Publication venue index
    └── by-citations.md   # Impact-ranked index
```

## Statistics

- **Total Papers**: 0
- **Last Updated**: Not yet initialized
- **Coverage Period**: Not configured

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

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Citation

If you use APPA in your research, please cite:

```bibtex
@software{appa2024,
  title={APPA: Awesome PHM Paper Agent},
  author={APPA Development Team},
  year={2024},
  url={https://github.com/PHMbench/Awesome-PHM-Paper-Agent},
  note={Intelligent academic paper management system for PHM research}
}
```