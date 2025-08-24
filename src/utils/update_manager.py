#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Update Manager - 用户确认更新机制
Update Manager - User Confirmation Mechanism for Updates

核心功能：
- 生成论文更新提案供用户确认
- 管理Awesome列表的增量更新
- 确保用户对所有内容更新有完全控制权
"""

import os
import json
import difflib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from .logging_config import get_logger


class UpdateProposal:
    """更新提案类"""
    
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.new_papers: List[Dict[str, Any]] = []
        self.readme_changes: Dict[str, Any] = {}
        self.data_changes: Dict[str, Any] = {}
        self.quality_summary: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'timestamp': self.timestamp,
            'new_papers': self.new_papers,
            'readme_changes': self.readme_changes,
            'data_changes': self.data_changes,
            'quality_summary': self.quality_summary
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateProposal':
        """从字典创建提案"""
        proposal = cls()
        proposal.timestamp = data.get('timestamp', proposal.timestamp)
        proposal.new_papers = data.get('new_papers', [])
        proposal.readme_changes = data.get('readme_changes', {})
        proposal.data_changes = data.get('data_changes', {})
        proposal.quality_summary = data.get('quality_summary', {})
        return proposal


class UpdateManager:
    """
    更新管理器 - 核心用户确认机制
    
    职责：
    1. 分析新发现的论文
    2. 生成结构化更新提案
    3. 提供用户友好的确认界面
    4. 仅应用用户确认的更新
    """
    
    def __init__(self, project_root: str = "."):
        """
        初始化更新管理器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data"
        self.logger = get_logger(__name__)
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            self.data_dir / "papers",
            self.data_dir / "bibtex",
            self.data_dir / "abstracts",
            self.data_dir / "statistics",
            self.data_dir / "quality_scores",
            self.data_dir / "proposals"  # 存储未决提案
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def generate_proposal(self, 
                         new_papers: List[Dict[str, Any]], 
                         search_context: Optional[Dict[str, Any]] = None) -> UpdateProposal:
        """
        生成更新提案
        
        Args:
            new_papers: 新发现的论文列表
            search_context: 搜索上下文信息
        
        Returns:
            UpdateProposal: 结构化的更新提案
        """
        self.logger.info(f"生成更新提案，包含 {len(new_papers)} 篇新论文")
        
        proposal = UpdateProposal()
        proposal.new_papers = new_papers
        
        # 分析论文质量分布
        proposal.quality_summary = self._analyze_quality_distribution(new_papers)
        
        # 生成README变更预览
        proposal.readme_changes = self._generate_readme_changes(new_papers)
        
        # 生成数据文件变更预览
        proposal.data_changes = self._generate_data_changes(new_papers)
        
        # 保存提案以备后续处理
        self._save_proposal(proposal, search_context)
        
        return proposal
    
    def _analyze_quality_distribution(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析论文质量分布"""
        quality_stats = {
            'total_papers': len(papers),
            'by_tier': {'top_tier': 0, 'excellent': 0, 'good': 0, 'under_review': 0},
            'by_venue_type': {'journal': 0, 'conference': 0, 'preprint': 0},
            'by_year': {},
            'excluded_publishers': [],
            'high_impact_journals': []
        }
        
        for paper in papers:
            # 质量分级统计
            tier = paper.get('quality_tier', 'under_review')
            if tier in quality_stats['by_tier']:
                quality_stats['by_tier'][tier] += 1
            
            # 发表类型统计
            venue_type = paper.get('venue_type', 'unknown')
            if venue_type in quality_stats['by_venue_type']:
                quality_stats['by_venue_type'][venue_type] += 1
            
            # 年份统计
            year = paper.get('year', 'unknown')
            quality_stats['by_year'][str(year)] = quality_stats['by_year'].get(str(year), 0) + 1
            
            # 高影响期刊
            if paper.get('quality_indicators', {}).get('impact_factor', 0) >= 8.0:
                journal = paper.get('venue', '')
                if journal and journal not in quality_stats['high_impact_journals']:
                    quality_stats['high_impact_journals'].append(journal)
        
        return quality_stats
    
    def _generate_readme_changes(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成README变更预览"""
        changes = {
            'sections_to_add': [],
            'papers_by_category': {},
            'new_categories': [],
            'toc_updates': []
        }
        
        # 按主题和年份分组论文
        for paper in papers:
            year = str(paper.get('year', '2025'))
            categories = self._classify_paper(paper)
            
            for category in categories:
                if category not in changes['papers_by_category']:
                    changes['papers_by_category'][category] = {}
                
                if year not in changes['papers_by_category'][category]:
                    changes['papers_by_category'][category][year] = []
                
                changes['papers_by_category'][category][year].append(self._format_paper_entry(paper))
        
        # 识别新分类
        existing_categories = self._get_existing_categories()
        new_categories = set(changes['papers_by_category'].keys()) - existing_categories
        changes['new_categories'] = list(new_categories)
        
        return changes
    
    def _classify_paper(self, paper: Dict[str, Any]) -> List[str]:
        """分类论文到合适的主题"""
        categories = []
        
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        keywords = [kw.lower() for kw in paper.get('keywords', [])]
        
        text_content = f"{title} {abstract} {' '.join(keywords)}"
        
        # 基于关键词的分类规则
        classification_rules = {
            'explainability': [
                'explainable', 'interpretable', 'interpretability', 'xai', 
                'explainable ai', 'shap', 'lime', 'attention'
            ],
            'llm-applications': [
                'large language model', 'llm', 'gpt', 'bert', 'transformer',
                'natural language', 'chatgpt', 'language model'
            ],
            'knowledge-graph': [
                'knowledge graph', 'kg', 'ontology', 'semantic network',
                'graph neural network', 'graph embedding'
            ],
            'fault-diagnosis': [
                'fault diagnosis', 'fault detection', 'failure diagnosis',
                'anomaly detection', 'fault classification'
            ],
            'predictive-maintenance': [
                'predictive maintenance', 'prognostics', 'remaining useful life',
                'rul', 'health monitoring', 'condition monitoring'
            ],
            'deep-learning': [
                'deep learning', 'neural network', 'cnn', 'lstm', 'rnn',
                'autoencoder', 'generative adversarial'
            ]
        }
        
        for category, keywords_list in classification_rules.items():
            if any(keyword in text_content for keyword in keywords_list):
                categories.append(category)
        
        # 至少分配一个通用类别
        if not categories:
            categories.append('general-phm')
        
        return categories
    
    def _format_paper_entry(self, paper: Dict[str, Any]) -> str:
        """格式化论文条目为Awesome列表格式"""
        title = paper.get('title', 'Unknown Title')
        authors = paper.get('authors', [])
        venue = paper.get('venue', 'Unknown Venue')
        year = paper.get('year', '')
        doi = paper.get('doi', '')
        
        # 格式化作者
        if len(authors) > 3:
            author_str = f"{authors[0]} et al."
        else:
            author_str = ", ".join(authors)
        
        # 构建基本条目
        entry = f"- **[{title}]"
        
        # 添加链接
        if doi:
            entry += f"(https://doi.org/{doi})"
        else:
            entry += "(#)"  # 占位符
        
        # 添加元数据
        entry += f"** - {author_str} ({venue}, {year})"
        
        # 添加质量指标
        quality_tier = paper.get('quality_tier', '')
        if quality_tier == 'top_tier':
            entry += " 🏆"
        elif quality_tier == 'excellent':
            entry += " ⭐"
        
        # 添加PDF和代码链接占位符
        entry += " [[PDF](#)] [[Code](#)] [[BibTeX](#)]"
        
        # 添加简短描述
        abstract = paper.get('abstract', '')
        if abstract:
            # 提取第一句作为简短描述
            first_sentence = abstract.split('.')[0]
            if len(first_sentence) > 100:
                first_sentence = first_sentence[:97] + "..."
            entry += f"\n  - {first_sentence}"
        
        return entry
    
    def _get_existing_categories(self) -> set:
        """获取现有的论文分类"""
        # 从当前README或配置中读取现有分类
        existing_categories = {
            'fault-diagnosis', 'predictive-maintenance', 'deep-learning',
            'digital-twin', 'rul-prediction'
        }
        return existing_categories
    
    def _generate_data_changes(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成数据文件变更预览"""
        changes = {
            'new_files': [],
            'updated_files': [],
            'bibtex_entries': len(papers),
            'abstract_files': len([p for p in papers if p.get('abstract')]),
            'quality_records': len(papers)
        }
        
        for paper in papers:
            paper_id = paper.get('id', '')
            if paper_id:
                # 新增的数据文件
                changes['new_files'].extend([
                    f"data/papers/{paper_id}.json",
                    f"data/bibtex/{paper_id}.bib"
                ])
                
                if paper.get('abstract'):
                    changes['new_files'].append(f"data/abstracts/{paper_id}.txt")
        
        return changes
    
    def _save_proposal(self, proposal: UpdateProposal, context: Optional[Dict[str, Any]] = None):
        """保存提案到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proposal_{timestamp}.json"
        filepath = self.data_dir / "proposals" / filename
        
        proposal_data = proposal.to_dict()
        if context:
            proposal_data['search_context'] = context
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(proposal_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"提案已保存到: {filepath}")
    
    def display_proposal(self, proposal: UpdateProposal) -> None:
        """显示更新提案给用户"""
        print("\n" + "="*80)
        print("📋 APPA更新提案 - 新发现的论文")
        print("="*80)
        
        # 总体统计
        stats = proposal.quality_summary
        print(f"\n📊 发现论文: {stats['total_papers']} 篇")
        print(f"🏆 质量分布: "
              f"顶级({stats['by_tier']['top_tier']}) | "
              f"优秀({stats['by_tier']['excellent']}) | "
              f"良好({stats['by_tier']['good']}) | "
              f"待评估({stats['by_tier']['under_review']})")
        
        # 按分类显示论文
        print(f"\n📚 论文分类预览:")
        for category, years_data in proposal.readme_changes['papers_by_category'].items():
            print(f"\n### {category.replace('-', ' ').title()}")
            for year, papers in years_data.items():
                print(f"  📅 {year} ({len(papers)} 篇):")
                for paper_entry in papers[:3]:  # 只显示前3篇
                    # 简化显示
                    title_line = paper_entry.split('\n')[0]
                    title = title_line.split('**[')[1].split(']')[0] if '**[' in title_line else "Unknown"
                    print(f"    - {title[:60]}{'...' if len(title) > 60 else ''}")
                
                if len(papers) > 3:
                    print(f"    - ... 还有 {len(papers) - 3} 篇")
        
        # 数据文件变更
        data_changes = proposal.data_changes
        print(f"\n💾 数据文件变更:")
        print(f"  - 新增JSON文件: {len(data_changes['new_files'])} 个")
        print(f"  - BibTeX条目: {data_changes['bibtex_entries']} 个")
        print(f"  - 摘要文件: {data_changes['abstract_files']} 个")
        
        print("\n" + "="*80)
    
    def get_user_confirmation(self, proposal: UpdateProposal) -> Tuple[bool, List[str]]:
        """
        获取用户确认
        
        Returns:
            Tuple[bool, List[str]]: (是否确认, 选择的论文ID列表)
        """
        self.display_proposal(proposal)
        
        print("\n❓ 确认操作:")
        print("1. 全部添加到Awesome列表")
        print("2. 选择性添加")
        print("3. 暂不添加，保存提案")
        print("4. 取消")
        
        while True:
            choice = input("\n请选择 (1-4): ").strip()
            
            if choice == "1":
                # 全部添加
                paper_ids = [paper.get('id') for paper in proposal.new_papers if paper.get('id')]
                return True, paper_ids
            
            elif choice == "2":
                # 选择性添加
                print("\n📋 可选论文列表:")
                for i, paper in enumerate(proposal.new_papers):
                    title = paper.get('title', 'Unknown')[:50]
                    quality = paper.get('quality_tier', 'unknown')
                    print(f"{i+1:2d}. {title}{'...' if len(paper.get('title', '')) > 50 else ''} ({quality})")
                
                selected_indices = input("\n请输入论文序号 (用逗号分隔, 如: 1,3,5): ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in selected_indices.split(',') if x.strip()]
                    selected_papers = [proposal.new_papers[i].get('id') for i in indices 
                                     if 0 <= i < len(proposal.new_papers)]
                    return True, [pid for pid in selected_papers if pid]
                except (ValueError, IndexError):
                    print("❌ 无效的序号格式，请重新输入")
                    continue
            
            elif choice == "3":
                # 保存但不应用
                print("💾 提案已保存，稍后可通过 scripts/awesome_tools.sh 管理")
                return False, []
            
            elif choice == "4":
                # 取消
                print("❌ 操作已取消")
                return False, []
            
            else:
                print("❌ 无效选择，请重新输入")
    
    def apply_updates(self, proposal: UpdateProposal, selected_paper_ids: List[str]) -> Dict[str, Any]:
        """
        应用用户确认的更新
        
        Args:
            proposal: 更新提案
            selected_paper_ids: 用户选择的论文ID列表
        
        Returns:
            Dict: 应用结果
        """
        if not selected_paper_ids:
            return {'success': False, 'message': '没有选择任何论文'}
        
        self.logger.info(f"应用更新，包含 {len(selected_paper_ids)} 篇论文")
        
        # 过滤选中的论文
        selected_papers = [
            paper for paper in proposal.new_papers 
            if paper.get('id') in selected_paper_ids
        ]
        
        results = {
            'success': True,
            'papers_added': len(selected_papers),
            'files_created': [],
            'readme_updated': False,
            'errors': []
        }
        
        try:
            # 1. 保存论文详细数据到data/
            self._save_paper_data(selected_papers, results)
            
            # 2. 更新README.md
            self._update_readme(selected_papers, results)
            
            # 3. 更新统计文件
            self._update_statistics(selected_papers, results)
            
            self.logger.info(f"更新应用成功: {results['papers_added']} 篇论文")
            
        except Exception as e:
            self.logger.error(f"应用更新时出错: {e}")
            results['success'] = False
            results['errors'].append(str(e))
        
        return results
    
    def _save_paper_data(self, papers: List[Dict[str, Any]], results: Dict[str, Any]) -> None:
        """保存论文详细数据"""
        for paper in papers:
            paper_id = paper.get('id')
            if not paper_id:
                continue
            
            # 保存JSON格式的论文详情
            json_path = self.data_dir / "papers" / f"{paper_id}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(paper, f, indent=2, ensure_ascii=False)
            results['files_created'].append(str(json_path))
            
            # 保存BibTeX
            bibtex_content = paper.get('bibtex', '')
            if bibtex_content:
                bib_path = self.data_dir / "bibtex" / f"{paper_id}.bib"
                with open(bib_path, 'w', encoding='utf-8') as f:
                    f.write(bibtex_content)
                results['files_created'].append(str(bib_path))
            
            # 保存摘要
            abstract = paper.get('abstract', '')
            if abstract:
                abstract_path = self.data_dir / "abstracts" / f"{paper_id}.txt"
                with open(abstract_path, 'w', encoding='utf-8') as f:
                    f.write(abstract)
                results['files_created'].append(str(abstract_path))
    
    def _update_readme(self, papers: List[Dict[str, Any]], results: Dict[str, Any]) -> None:
        """更新README.md为Awesome格式"""
        readme_path = self.project_root / "README.md"
        
        if not readme_path.exists():
            # 创建新的Awesome格式README
            self._create_awesome_readme(papers)
        else:
            # 更新现有README
            self._append_to_awesome_readme(papers)
        
        results['readme_updated'] = True
    
    def _create_awesome_readme(self, papers: List[Dict[str, Any]]) -> None:
        """创建新的Awesome格式README"""
        content = self._generate_awesome_readme_content(papers)
        
        readme_path = self.project_root / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _append_to_awesome_readme(self, papers: List[Dict[str, Any]]) -> None:
        """向现有README添加新论文"""
        readme_path = self.project_root / "README.md"
        
        # 读取现有内容
        with open(readme_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # 生成新条目
        new_entries = self._generate_paper_entries(papers)
        
        # 插入到合适位置（这里简化处理，追加到文件末尾）
        updated_content = current_content + "\n\n" + new_entries
        
        # 写回文件
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    
    def _generate_awesome_readme_content(self, papers: List[Dict[str, Any]]) -> str:
        """生成Awesome格式的README内容"""
        current_year = datetime.now().year
        
        content = f"""# Awesome PHM Papers [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> 精选的PHM(Prognostics and Health Management)领域高质量学术论文列表

## Contents

- [2025](#2025)
  - [可解释性与故障诊断](#explainability-and-fault-diagnosis)
  - [大语言模型应用](#llm-applications)
- [2024](#2024)
  - [知识图谱融合](#knowledge-graph-fusion)
  - [深度学习方法](#deep-learning-methods)
- [按主题分类](#topics)
- [贡献指南](#contributing)
- [许可证](#license)

---

## {current_year}

### Explainability and Fault Diagnosis

"""
        
        # 添加论文条目
        content += self._generate_paper_entries(papers)
        
        content += """

---

## Topics

### Deep Learning for PHM
- [深度学习在PHM中的应用](data/topics/deep-learning.md)

### Fault Diagnosis
- [故障诊断方法](data/topics/fault-diagnosis.md)

### Predictive Maintenance
- [预测性维护技术](data/topics/predictive-maintenance.md)

---

## Contributing

欢迎贡献! 请阅读 [贡献指南](CONTRIBUTING.md) 了解如何添加新论文。

### 论文质量要求
- 发表在知名期刊或会议 (影响因子 ≥ 5.0)
- 与PHM领域高度相关
- 排除MDPI等低质量出版商

### 添加论文步骤
1. Fork本仓库
2. 添加论文到对应分类
3. 更新相关数据文件
4. 提交Pull Request

---

## License

[![CC0](https://mirrors.creativecommons.org/presskit/buttons/88x31/svg/cc-zero.svg)](https://creativecommons.org/publicdomain/zero/1.0)

This work is licensed under a [Creative Commons Zero v1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0) License.
"""
        
        return content
    
    def _generate_paper_entries(self, papers: List[Dict[str, Any]]) -> str:
        """生成论文条目"""
        entries_by_category = {}
        
        for paper in papers:
            categories = self._classify_paper(paper)
            for category in categories:
                if category not in entries_by_category:
                    entries_by_category[category] = []
                entries_by_category[category].append(self._format_paper_entry(paper))
        
        content = ""
        for category, entries in entries_by_category.items():
            category_title = category.replace('-', ' ').title()
            content += f"\n#### {category_title}\n\n"
            for entry in entries:
                content += entry + "\n"
        
        return content
    
    def _update_statistics(self, papers: List[Dict[str, Any]], results: Dict[str, Any]) -> None:
        """更新统计信息"""
        stats_path = self.data_dir / "statistics" / "overview.json"
        
        # 读取现有统计
        if stats_path.exists():
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
        else:
            stats = {
                'total_papers': 0,
                'by_year': {},
                'by_category': {},
                'by_quality_tier': {},
                'last_updated': datetime.now().isoformat()
            }
        
        # 更新统计
        stats['total_papers'] += len(papers)
        stats['last_updated'] = datetime.now().isoformat()
        
        for paper in papers:
            year = str(paper.get('year', '2025'))
            quality_tier = paper.get('quality_tier', 'under_review')
            categories = self._classify_paper(paper)
            
            # 年份统计
            stats['by_year'][year] = stats['by_year'].get(year, 0) + 1
            
            # 质量分级统计
            stats['by_quality_tier'][quality_tier] = stats['by_quality_tier'].get(quality_tier, 0) + 1
            
            # 分类统计
            for category in categories:
                stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        # 保存统计
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        results['files_created'].append(str(stats_path))


def main():
    """测试用例"""
    # 示例论文数据
    sample_papers = [
        {
            'id': '2025-MSSP-Zhang-Explainable',
            'title': 'Explainable Fault Diagnosis Using Attention-based Deep Learning',
            'authors': ['Zhang Wei', 'Liu Ming'],
            'year': 2025,
            'venue': 'Mechanical Systems and Signal Processing',
            'doi': '10.1016/j.ymssp.2025.001',
            'abstract': 'This paper proposes an explainable fault diagnosis method using attention mechanisms.',
            'quality_tier': 'excellent',
            'quality_indicators': {'impact_factor': 8.4}
        }
    ]
    
    # 创建更新管理器
    update_manager = UpdateManager()
    
    # 生成提案
    proposal = update_manager.generate_proposal(sample_papers)
    
    # 显示提案
    update_manager.display_proposal(proposal)
    
    # 模拟用户确认
    confirmed, selected_ids = update_manager.get_user_confirmation(proposal)
    
    if confirmed and selected_ids:
        results = update_manager.apply_updates(proposal, selected_ids)
        print(f"\n✅ 更新完成: {results}")


if __name__ == "__main__":
    main()