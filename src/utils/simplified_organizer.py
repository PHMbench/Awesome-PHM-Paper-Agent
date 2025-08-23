"""
Simplified Knowledge Organizer

这个模块创建精简版的论文知识库，只包含核心信息：
- 标题
- 作者和单位
- 摘要
- BibTeX 引用

不包含冗余的统计信息、复杂的导航或过多的元数据。
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict

from .logging_config import get_logger


class SimplifiedPaperOrganizer:
    """
    简化的论文组织器
    
    只生成必要的文件和信息，专注于核心内容：
    - 简洁的论文页面（标题、作者、单位、摘要）
    - 基本的分类索引
    - 清晰的 BibTeX 引用
    """
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.logger = get_logger(__name__)
        
        # 简化的 PHM 分类
        self.categories = {
            'deep-learning': {
                'title': 'Deep Learning in PHM',
                'keywords': ['deep learning', 'neural network', 'CNN', 'LSTM', 'transformer']
            },
            'fault-diagnosis': {
                'title': 'Fault Diagnosis & Detection', 
                'keywords': ['fault diagnosis', 'fault detection', 'anomaly detection', 'bearing fault']
            },
            'rul-prediction': {
                'title': 'Remaining Useful Life Prediction',
                'keywords': ['RUL', 'remaining useful life', 'prognostics', 'degradation']
            },
            'digital-twin': {
                'title': 'Digital Twin for PHM',
                'keywords': ['digital twin', 'cyber-physical', 'virtual sensor']
            },
            'predictive-maintenance': {
                'title': 'Predictive Maintenance',
                'keywords': ['predictive maintenance', 'condition monitoring', 'maintenance']
            }
        }
        
        # 初始化目录结构
        self._init_directories()
        
        self.logger.info("Simplified Paper Organizer initialized")
    
    def _init_directories(self):
        """初始化简化的目录结构"""
        
        directories = [
            'categories',
            'papers',
            'by-year'
        ]
        
        for category in self.categories:
            directories.append(f'categories/{category}')
        
        for dir_path in directories:
            (self.base_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    def organize_papers(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        组织论文到简化的知识库结构
        
        Args:
            papers: 论文信息列表
            
        Returns:
            组织结果摘要
        """
        
        self.logger.info(f"Organizing {len(papers)} papers with simplified structure")
        
        if not papers:
            self.logger.warning("No papers to organize")
            return {'status': 'no_papers'}
        
        # 分类论文
        categorized = self._categorize_papers(papers)
        
        # 生成论文页面
        paper_files = self._generate_paper_pages(papers)
        
        # 生成分类页面
        category_files = self._generate_category_pages(categorized)
        
        # 生成主页
        main_readme = self._generate_main_readme(papers, categorized)
        
        # 生成年份索引
        year_index = self._generate_year_index(papers)
        
        summary = {
            'status': 'completed',
            'total_papers': len(papers),
            'categories': len(categorized),
            'files_created': len(paper_files) + len(category_files) + 2,  # +2 for main README and year index
            'organization_date': datetime.now().isoformat(),
            'simplified_structure': True
        }
        
        self.logger.info(f"Organization complete: {summary}")
        return summary
    
    def _categorize_papers(self, papers: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """简化的论文分类"""
        
        categorized = defaultdict(list)
        
        for paper in papers:
            # 分析论文内容确定分类
            paper_categories = self._analyze_paper_category(paper)
            primary_category = paper_categories[0] if paper_categories else 'predictive-maintenance'
            
            categorized[primary_category].append(paper)
            paper['primary_category'] = primary_category
        
        return dict(categorized)
    
    def _analyze_paper_category(self, paper: Dict[str, Any]) -> List[str]:
        """分析论文应属于哪个类别"""
        
        # 合并标题和摘要进行分析
        content = (
            paper.get('title', '') + ' ' + 
            paper.get('abstract', '')
        ).lower()
        
        category_scores = {}
        
        for cat_id, cat_info in self.categories.items():
            score = 0
            for keyword in cat_info['keywords']:
                if keyword.lower() in content:
                    score += 1
            
            if score > 0:
                category_scores[cat_id] = score
        
        # 按分数排序返回
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        return [cat for cat, score in sorted_categories]
    
    def _generate_paper_pages(self, papers: List[Dict[str, Any]]) -> List[str]:
        """生成简化的论文页面"""
        
        created_files = []
        
        for paper in papers:
            # 创建论文文件名
            paper_filename = self._create_paper_filename(paper)
            paper_path = self.base_path / 'papers' / f"{paper_filename}.md"
            
            # 生成简化的论文内容
            content = self._generate_simplified_paper_content(paper)
            
            with open(paper_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(str(paper_path))
        
        return created_files
    
    def _create_paper_filename(self, paper: Dict[str, Any]) -> str:
        """创建论文文件名"""
        
        year = paper.get('year', 'unknown')
        
        # 获取第一作者姓氏
        authors = paper.get('authors', [])
        first_author = authors[0] if authors else 'Unknown'
        
        # 提取姓氏
        if ',' in first_author:
            # 格式：姓, 名
            surname = first_author.split(',')[0].strip()
        else:
            # 格式：名 姓
            parts = first_author.split()
            surname = parts[-1] if parts else 'Unknown'
        
        # 清理标题获取关键词
        title = paper.get('title', 'Unknown')
        title_words = re.findall(r'\b\w+\b', title)[:3]  # 前3个关键词
        title_key = ''.join(word.capitalize() for word in title_words)
        
        # 创建文件名
        filename = f"{year}-{surname}-{title_key}"
        
        # 清理特殊字符
        filename = re.sub(r'[^\w\-_]', '', filename)
        
        return filename[:50]  # 限制长度
    
    def _generate_simplified_paper_content(self, paper: Dict[str, Any]) -> str:
        """生成简化的论文页面内容"""
        
        title = paper.get('title', 'Unknown Title')
        authors = paper.get('authors', [])
        year = paper.get('year', 'Unknown')
        venue = paper.get('venue', 'Unknown Venue')
        abstract = paper.get('abstract', 'No abstract available')
        
        # 格式化作者和单位
        authors_formatted = self._format_authors_with_affiliations(authors)
        
        content = f"""# {title}

**作者**: {authors_formatted}

**发表年份**: {year}

**期刊/会议**: {venue}

## 摘要

{abstract}

## 引用

```bibtex
{self._generate_bibtex(paper)}
```

---

*论文页面生成时间: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        return content
    
    def _format_authors_with_affiliations(self, authors: List[str]) -> str:
        """格式化作者列表（尝试包含单位信息）"""
        
        if not authors:
            return "未知作者"
        
        # 简化处理：直接列出作者
        # 在实际应用中，可能需要从原始数据中提取单位信息
        if len(authors) <= 5:
            return ', '.join(authors)
        else:
            return ', '.join(authors[:5]) + ' 等'
    
    def _generate_bibtex(self, paper: Dict[str, Any]) -> str:
        """生成 BibTeX 引用"""
        
        # 创建引用键
        authors = paper.get('authors', ['Unknown'])
        first_author_lastname = authors[0].split()[-1] if authors else 'Unknown'
        year = paper.get('year', datetime.now().year)
        title_words = re.findall(r'\w+', paper.get('title', ''))[:2]
        title_key = ''.join(word.capitalize() for word in title_words)
        
        cite_key = f"{first_author_lastname}{year}{title_key}"
        
        # 确定类型
        venue = paper.get('venue', '').lower()
        entry_type = 'article' if any(word in venue for word in ['journal', 'transactions']) else 'inproceedings'
        
        # 构建 BibTeX
        bibtex = f"@{entry_type}{{{cite_key},\n"
        bibtex += f'  title = {{{paper.get("title", "Unknown Title")}}},\n'
        
        if paper.get('authors'):
            author_str = ' and '.join(paper['authors'][:5])  # 限制作者数量
            bibtex += f"  author = {{{author_str}}},\n"
        
        if paper.get('year'):
            bibtex += f"  year = {{{paper['year']}}},\n"
        
        if paper.get('venue'):
            venue_field = 'journal' if entry_type == 'article' else 'booktitle'
            bibtex += f"  {venue_field} = {{{paper['venue']}}},\n"
        
        if paper.get('doi'):
            bibtex += f"  doi = {{{paper['doi']}}},\n"
        
        bibtex += "}\n"
        
        return bibtex
    
    def _generate_category_pages(self, categorized: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """生成简化的分类页面"""
        
        created_files = []
        
        for category_id, papers in categorized.items():
            if category_id not in self.categories:
                continue
                
            category_info = self.categories[category_id]
            category_path = self.base_path / 'categories' / category_id / 'README.md'
            
            content = f"""# {category_info['title']}

共 {len(papers)} 篇论文

## 论文列表

"""
            
            # 按年份降序排列
            sorted_papers = sorted(papers, key=lambda p: p.get('year', 0), reverse=True)
            
            for i, paper in enumerate(sorted_papers, 1):
                title = paper.get('title', 'Unknown Title')
                authors = paper.get('authors', [])
                year = paper.get('year', 'Unknown')
                
                # 作者格式化
                if len(authors) > 2:
                    author_str = f"{authors[0]} 等"
                else:
                    author_str = ', '.join(authors)
                
                # 创建论文链接
                paper_filename = self._create_paper_filename(paper)
                paper_link = f"../../papers/{paper_filename}.md"
                
                content += f"{i}. **[{title}]({paper_link})**\n"
                content += f"   - *{author_str}* ({year})\n\n"
            
            content += f"""
---

*分类页面更新时间: {datetime.now().strftime('%Y-%m-%d')}*
"""
            
            with open(category_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(str(category_path))
        
        return created_files
    
    def _generate_main_readme(self, 
                            papers: List[Dict[str, Any]], 
                            categorized: Dict[str, List[Dict[str, Any]]]) -> str:
        """生成简化的主页 README"""
        
        # 统计信息
        total_papers = len(papers)
        years = [p.get('year') for p in papers if p.get('year')]
        year_range = f"{min(years)}-{max(years)}" if years else "未知"
        
        content = f"""# Awesome PHM Papers

> 精选的 PHM (预测性健康管理) 学术论文集合

本知识库收集了 PHM 领域的重要学术论文，所有论文信息均来自真实的学术数据库。

## 📊 统计信息

- **论文总数**: {total_papers}
- **分类数量**: {len(categorized)}
- **年份范围**: {year_range}
- **最后更新**: {datetime.now().strftime('%Y-%m-%d')}

## 📚 按类别浏览

"""
        
        for category_id, papers_in_cat in categorized.items():
            if category_id in self.categories:
                cat_title = self.categories[category_id]['title']
                content += f"- **[{cat_title}](categories/{category_id}/README.md)** ({len(papers_in_cat)} 篇论文)\n"
        
        content += f"""

## 📅 按年份浏览

- [按年份查看论文](by-year/README.md)

## 🔍 最新论文

"""
        
        # 显示最新的5篇论文
        recent_papers = sorted(papers, key=lambda p: p.get('year', 0), reverse=True)[:5]
        
        for i, paper in enumerate(recent_papers, 1):
            title = paper.get('title', 'Unknown Title')
            authors = paper.get('authors', [])
            year = paper.get('year', 'Unknown')
            
            author_str = authors[0] if authors else 'Unknown Author'
            if len(authors) > 1:
                author_str += ' 等'
            
            paper_filename = self._create_paper_filename(paper)
            paper_link = f"papers/{paper_filename}.md"
            
            content += f"{i}. **[{title}]({paper_link})**\n"
            content += f"   - *{author_str}* ({year})\n\n"
        
        content += f"""
## 🤝 贡献

欢迎贡献新的 PHM 相关论文！请确保：

1. **真实论文**: 必须是已发表或预印本的真实学术论文
2. **PHM 相关**: 与预测性健康管理相关
3. **完整信息**: 包含标题、作者、摘要等基本信息

## 📄 许可

本项目采用 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 许可协议。

---

*由 APPA (Awesome PHM Paper Agent) 自动生成和维护*
"""
        
        # 写入主 README
        main_readme_path = self.base_path / 'README.md'
        with open(main_readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(main_readme_path)
    
    def _generate_year_index(self, papers: List[Dict[str, Any]]) -> str:
        """生成按年份的索引"""
        
        # 按年份分组
        papers_by_year = defaultdict(list)
        for paper in papers:
            year = paper.get('year', 'Unknown')
            papers_by_year[year].append(paper)
        
        content = """# 按年份浏览论文

"""
        
        # 按年份降序排列
        for year in sorted(papers_by_year.keys(), reverse=True):
            year_papers = papers_by_year[year]
            content += f"\n## {year} ({len(year_papers)} 篇论文)\n\n"
            
            for paper in year_papers:
                title = paper.get('title', 'Unknown Title')
                authors = paper.get('authors', [])
                
                author_str = authors[0] if authors else 'Unknown Author'
                if len(authors) > 1:
                    author_str += ' 等'
                
                paper_filename = self._create_paper_filename(paper)
                paper_link = f"../papers/{paper_filename}.md"
                
                content += f"- **[{title}]({paper_link})** - *{author_str}*\n"
        
        content += f"""

---

*年份索引更新时间: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        # 写入年份索引
        year_index_path = self.base_path / 'by-year' / 'README.md'
        with open(year_index_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(year_index_path)


if __name__ == "__main__":
    # 测试简化组织器
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp()
    print(f"Testing in: {test_dir}")
    
    try:
        organizer = SimplifiedPaperOrganizer(test_dir)
        
        # 测试论文
        test_papers = [
            {
                'title': 'Deep Learning for Bearing Fault Diagnosis',
                'authors': ['Zhang, Wei', 'Liu, Ming'],
                'year': 2024,
                'venue': 'Mechanical Systems and Signal Processing',
                'abstract': 'This paper presents a deep learning approach for bearing fault diagnosis using CNN-LSTM networks. The method achieves high accuracy in fault classification.',
                'doi': '10.1016/j.ymssp.2024.123456'
            },
            {
                'title': 'RUL Prediction Using LSTM Networks',
                'authors': ['Chen, Li', 'Wang, Jun'],
                'year': 2023,
                'venue': 'IEEE Transactions on Industrial Electronics',
                'abstract': 'A novel LSTM-based method for remaining useful life prediction of mechanical components is proposed and validated on real datasets.',
                'doi': '10.1109/TIE.2023.654321'
            }
        ]
        
        # 执行组织
        result = organizer.organize_papers(test_papers)
        
        print(f"✅ Organization successful!")
        print(f"   Papers: {result['total_papers']}")
        print(f"   Categories: {result['categories']}")
        print(f"   Files created: {result['files_created']}")
        
        # 列出创建的文件
        print(f"\n📁 Created files:")
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), test_dir)
                print(f"   {rel_path}")
        
    finally:
        shutil.rmtree(test_dir)
        print(f"\n🧹 Cleaned up: {test_dir}")