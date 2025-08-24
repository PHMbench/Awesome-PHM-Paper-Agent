# 🔐 Elsevier ScienceDirect API 配置指南

## 📋 概述

Elsevier ScienceDirect是世界领先的科学文献数据库，包含大量高质量的PHM相关论文。通过配置API密钥，APPA系统可以访问Elsevier的丰富文献资源。

## 🚀 快速配置

### 1️⃣ 获取API密钥

1. **访问Elsevier开发者门户**
   - 🔗 [https://dev.elsevier.com/apikey/create](https://dev.elsevier.com/apikey/create)

2. **注册开发者账户**
   - 使用您的机构邮箱注册
   - 填写研究目的和用途说明
   - 选择"Academic/Research"用途

3. **申请API密钥**
   - 选择所需的API服务（推荐：ScienceDirect Article Retrieval API）
   - 说明用途：PHM领域学术文献自动化管理和分析
   - 等待审核通过（通常1-2个工作日）

4. **获取密钥**
   - 审核通过后，您将收到API密钥
   - API密钥格式：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 2️⃣ 配置APPA系统

1. **更新配置文件**
   ```yaml
   # config.yaml
   data_sources:
     elsevier:
       enabled: true  # 启用Elsevier支持
       api_key: "your-api-key-here"  # 填入您的API密钥
   ```

2. **验证配置**
   ```bash
   # 测试API连接
   python -c "from src.utils.elsevier_client import ElsevierClient; 
              client = ElsevierClient('config.yaml'); 
              print('✅ Elsevier API配置成功' if client.test_connection() else '❌ API配置失败')"
   ```

### 3️⃣ 使用Elsevier搜索

```bash
# 使用academic-researcher agent进行搜索（会自动使用Elsevier）
"搜索Elsevier数据库中关于轴承故障诊断的论文"

# 或者在搜索时明确指定数据源
"从ScienceDirect搜索最新的PHM研究"
```

## 🔧 高级配置

### 📊 搜索参数优化

```yaml
# config.yaml - Elsevier高级设置
data_sources:
  elsevier:
    settings:
      # 包含完整摘要
      include_abstracts: true
      # 包含作者信息
      include_authors: true
      # 包含关键词
      include_keywords: true
      # 每次请求最大结果数（最大200）
      max_results_per_request: 100
      
    search_filters:
      # 内容类型过滤
      content_types: ["journal"]  # 仅期刊论文
      # 学科领域过滤
      subject_areas: ["ENGI", "COMP"]  # 工程学和计算机科学
      # 仅开放获取论文
      open_access_only: false
```

### 🎯 PHM专用搜索策略

```yaml
# PHM领域优化的Elsevier搜索
elsevier_phm_search:
  # 高影响因子期刊优先
  preferred_journals:
    - "Mechanical Systems and Signal Processing"
    - "Reliability Engineering & System Safety"
    - "Engineering Applications of Artificial Intelligence"
    - "Expert Systems with Applications"
    
  # PHM关键词权重
  keyword_weights:
    "prognostics": 1.0
    "health management": 1.0
    "fault diagnosis": 0.9
    "predictive maintenance": 0.9
    "condition monitoring": 0.8
    "remaining useful life": 0.9
```

## 📈 API使用限制与优化

### 🚦 速率限制

| API类型 | 免费配额 | 付费配额 | 推荐设置 |
|---------|----------|----------|----------|
| **ScienceDirect Article Retrieval** | 25,000次/年 | 无限制 | 2 req/sec |
| **Scopus Search** | 20,000次/年 | 无限制 | 9 req/sec |
| **Abstract Retrieval** | 25,000次/年 | 无限制 | 2 req/sec |

### ⚡ 性能优化建议

```python
# 批量搜索优化
elsevier_optimization:
  # 使用批量请求
  batch_size: 25  # 每批处理25篇论文
  
  # 智能缓存
  cache_duration: 7  # 缓存7天
  
  # 并发控制
  max_concurrent: 2  # 最大2个并发请求
  
  # 重试策略
  retry_delays: [1, 3, 5]  # 指数退避重试
```

## 🔍 支持的搜索功能

### 📋 基本搜索

- **全文搜索**: 标题、摘要、关键词全文检索
- **作者搜索**: 按作者姓名精确搜索
- **期刊筛选**: 指定期刊或出版商
- **时间范围**: 按发表年份过滤
- **学科分类**: 按Elsevier学科分类筛选

### 🎯 高级搜索

- **引用分析**: 获取论文引用数据
- **影响因子**: 自动获取期刊影响因子
- **开放获取**: 筛选OA论文
- **相关推荐**: 基于内容的相关论文推荐

## 🛠️ 故障排除

### ❌ 常见错误

#### 1. API密钥无效
```
错误：401 Unauthorized
解决：检查API密钥是否正确，是否已激活
```

#### 2. 超出速率限制
```
错误：429 Too Many Requests
解决：降低请求频率，启用缓存机制
```

#### 3. 无法访问论文
```
错误：403 Forbidden
解决：检查机构访问权限，确认论文访问权限
```

#### 4. 网络连接问题
```
错误：Connection timeout
解决：检查网络连接，使用代理服务器
```

### 🔧 调试模式

```python
# 启用详细日志
import logging
logging.getLogger('elsevier_client').setLevel(logging.DEBUG)

# 测试API连接
from src.utils.elsevier_client import ElsevierClient
client = ElsevierClient(debug=True)
result = client.search("bearing fault diagnosis", limit=5)
print(f"搜索结果: {len(result)} 篇论文")
```

## 📚 API文档参考

### 🔗 官方资源
- **API文档**: [Elsevier Developer Portal](https://dev.elsevier.com/)
- **ScienceDirect API**: [Article Retrieval API Guide](https://dev.elsevier.com/documentation/ScienceDirectSearchAPI.wadl)
- **Scopus API**: [Scopus Search API Guide](https://dev.elsevier.com/documentation/SCOPUSSearchAPI.wadl)

### 📊 数据字段说明

| 字段名 | 描述 | 示例 |
|--------|------|------|
| `dc:identifier` | 文章DOI | `10.1016/j.ymssp.2024.001` |
| `dc:title` | 文章标题 | `Deep Learning for PHM` |
| `dc:creator` | 作者信息 | `Zhang, W.; Liu, M.` |
| `prism:publicationName` | 期刊名称 | `Mechanical Systems and Signal Processing` |
| `prism:coverDate` | 发表日期 | `2024-05-15` |
| `citedby-count` | 引用次数 | `25` |

## 🚀 最佳实践

### 1️⃣ 搜索策略
- **组合关键词**: 使用AND、OR逻辑组合关键词
- **期刊筛选**: 优先搜索高影响因子期刊
- **时间窗口**: 设置合理的时间范围避免过多结果

### 2️⃣ 数据管理
- **增量更新**: 仅获取新发表的论文
- **去重处理**: 基于DOI进行重复检测
- **质量过滤**: 应用APPA质量过滤标准

### 3️⃣ 成本控制
- **智能缓存**: 避免重复API请求
- **批量处理**: 合并多个搜索请求
- **精准搜索**: 使用精确的关键词减少无关结果

---

## 🆘 技术支持

### 📧 获取帮助
- **Elsevier技术支持**: [Contact Elsevier API Support](https://service.elsevier.com/)
- **APPA项目问题**: [GitHub Issues](https://github.com/your-repo/issues)

### 📋 支持清单
在寻求帮助前，请准备以下信息：
- [ ] API密钥状态（已申请/已激活/过期）
- [ ] 错误信息完整内容
- [ ] 搜索查询和参数
- [ ] APPA版本和配置文件
- [ ] 网络环境信息（是否使用代理）

---

**🎯 配置完成后，您将能够访问Elsevier ScienceDirect的海量高质量PHM文献资源！**

*📅 更新日期: 2025-08-23 | 🔧 配置版本: v2.0 | 📊 支持API版本: ScienceDirect v2.0*