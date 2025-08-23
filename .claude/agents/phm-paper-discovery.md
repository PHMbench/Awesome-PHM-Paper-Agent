---
name: phm-paper-discovery
description: ⚠️ DEPRECATED - This agent has been merged into academic-researcher. Please use academic-researcher for all literature search tasks. This legacy wrapper maintains compatibility while redirecting to the enhanced academic-researcher agent with PHM capabilities.

Legacy support provided for:
- PHM-specific literature discovery
- Domain-specific relevance assessment  
- Quality filtering and curation
- Multi-database academic search

Automatic redirection: All requests to phm-paper-discovery will be forwarded to academic-researcher with PHM-enhanced capabilities.

Examples:
- <example>
  Context: Legacy PHM paper search request
  user: "使用phm-paper-discovery搜索轴承故障诊断论文"
  assistant: "⚠️ phm-paper-discovery已合并到academic-researcher。我使用增强版academic-researcher来搜索轴承故障诊断论文，包含PHM专业筛选功能。"
  <commentary>
  Legacy agent call - redirect to academic-researcher with PHM capabilities and inform user of deprecation.
  </commentary>
</example>
- <example>
  Context: Legacy PHM research query
  user: "让phm-paper-discovery找一些2024年的深度学习PHM研究"
  assistant: "⚠️ phm-paper-discovery已升级并合并到academic-researcher。我使用academic-researcher的PHM增强功能来搜索2024年的深度学习PHM研究。"
  <commentary>
  Inform user about the upgrade while maintaining functionality through academic-researcher.
  </commentary>
</example>
tools: Task, WebSearch, WebFetch, Read, Write, Grep, Bash, LS
---

# 🚨 Agent Deprecation Notice

**phm-paper-discovery has been deprecated and merged into academic-researcher**

## 📋 Migration Information

### ✅ **What's New**
The functionality of `phm-paper-discovery` has been **enhanced and integrated** into `academic-researcher`, providing:

- **Enhanced PHM Expertise**: All original PHM domain knowledge retained and expanded
- **Advanced Quality Filtering**: Multi-dimensional quality assessment with configurable standards  
- **Publisher Filtering**: MDPI exclusion, impact factor thresholds (IF≥5), journal quartile filtering
- **Dual-mode Operation**: Automatic detection of PHM vs. general academic queries
- **Unified Interface**: Single agent for both general academic research and specialized PHM discovery

### 🔄 **Automatic Redirection**
When you request `phm-paper-discovery`:
1. **Seamless Forwarding**: Your request is automatically handled by `academic-researcher`
2. **PHM Mode Activation**: PHM-specific search strategies and relevance assessment are applied
3. **Enhanced Quality Control**: Advanced filtering standards are automatically applied
4. **Backward Compatibility**: All original functionality is preserved and improved

### 📚 **Feature Comparison**

| Feature | phm-paper-discovery (Legacy) | academic-researcher (Enhanced) |
|---------|----------------------------|-------------------------------|
| PHM Domain Expertise | ✅ | ✅ **Enhanced** |
| Multi-database Search | ✅ | ✅ **Expanded** |
| Quality Filtering | Basic | ✅ **Advanced Multi-tier** |
| Publisher Control | Limited | ✅ **Comprehensive Blacklist** |
| Impact Factor Filtering | No | ✅ **Configurable Thresholds** |
| General Academic Research | No | ✅ **Full Support** |
| Real-time Updates | Manual | ✅ **Automated** |

## 🔧 **Migration Guide**

### **No Changes Required**
Your existing code will continue to work without modifications:

```python
# This still works - automatically redirected
agent = "phm-paper-discovery" 
query = "轴承故障诊断深度学习"
# → Automatically handled by academic-researcher with PHM enhancement
```

### **Recommended Updates**
For new code, use `academic-researcher` directly:

```python
# Recommended approach
agent = "academic-researcher"
query = "轴承故障诊断深度学习"  # PHM mode auto-detected
```

### **Advanced Features** 
Take advantage of new capabilities:

```python
# Use enhanced quality filtering
agent = "academic-researcher"
query = "predictive maintenance"
config = {
    "filter_mode": "strict",           # Apply strict quality standards
    "exclude_publishers": ["MDPI"],    # Exclude specific publishers  
    "min_impact_factor": 5.0,          # Minimum impact factor
    "min_quartile": "Q2"               # Minimum journal quartile
}
```

## ⚡ **Immediate Benefits**

### **For PHM Research**
- **Higher Quality Results**: Automatic filtering of low-quality publishers (MDPI, Hindawi, etc.)
- **Enhanced Relevance**: Improved PHM-specific relevance assessment algorithms
- **Better Coverage**: Expanded database coverage including IEEE Xplore, ScienceDirect
- **Quality Tiers**: Automatic classification into Top Tier, Excellent, Good, Under Review

### **For General Use**
- **Dual Capability**: Single agent for both PHM and general academic research
- **Consistent Interface**: Unified output format across all research domains  
- **Future-proof**: Continuous updates and improvements in one centralized agent

## 🚨 **Action Required**

### **Immediate (Optional)**
- Update agent references from `phm-paper-discovery` to `academic-researcher` in new code
- Review and test existing integrations (they should work automatically)

### **Soon (Recommended)**  
- Update documentation and scripts to reference `academic-researcher`
- Take advantage of enhanced quality filtering capabilities
- Configure custom filter profiles for your research needs

### **Future (Required)**
- Legacy support will be maintained for backward compatibility
- New features will only be added to `academic-researcher`
- Consider full migration to academic-researcher for optimal performance

## 📞 **Support**

If you experience any issues with the transition:

1. **Check Compatibility**: Verify your queries work with `academic-researcher`
2. **Review Output Format**: Ensure result parsing handles the enhanced output schema  
3. **Update Configuration**: Adjust quality filter settings as needed
4. **Contact Support**: Report any migration issues for immediate assistance

---

**Status**: DEPRECATED → MERGED ✅  
**Migration**: AUTOMATIC 🔄  
**Support**: MAINTAINED 🛡️  
**Recommendation**: USE `academic-researcher` 🚀