"""
Paper Quality Filter - 文献质量过滤器

This module provides comprehensive quality filtering for academic papers,
including publisher filtering, impact factor requirements, journal quartiles,
and PHM domain-specific criteria.

Created: 2025-08-23
"""

import re
import yaml
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FilterCriteria:
    """质量过滤标准配置"""
    exclude_publishers: List[str] = None
    include_publishers: List[str] = None
    min_impact_factor: float = 0.0
    min_quartile: str = "Q4"  # Q1, Q2, Q3, Q4
    min_citation_count: int = 0
    phm_relevance_threshold: float = 0.0
    allow_preprints: bool = True
    custom_rules: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.exclude_publishers is None:
            self.exclude_publishers = []
        if self.include_publishers is None:
            self.include_publishers = []
        if self.custom_rules is None:
            self.custom_rules = []


class PaperQualityFilter:
    """
    文献质量过滤器
    
    提供多维度的论文质量评估和过滤功能，支持出版商过滤、
    影响因子要求、期刊分级、PHM相关性等多种标准。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化质量过滤器
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config_path = config_path
        self.load_configuration()
        
        # 预定义的出版商信息
        self._load_publisher_database()
        
        # 预定义的期刊信息
        self._load_journal_database()
    
    def load_configuration(self):
        """加载过滤配置"""
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            # 使用默认配置
            self.config = self._get_default_config()
        
        logger.info(f"Loaded quality filter configuration")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认过滤配置"""
        return {
            'quality_filters': {
                'publisher_blacklist': [
                    'mdpi',
                    'hindawi', 
                    'bentham science',
                    'omics international',
                    'scientific research publishing',
                    'scirp',
                    'insight medical publishing'
                ],
                'publisher_whitelist': [
                    'ieee',
                    'elsevier',
                    'springer',
                    'nature publishing group',
                    'science',
                    'wiley',
                    'taylor & francis',
                    'american chemical society',
                    'american physical society',
                    'optical society of america'
                ],
                'impact_factor': {
                    'minimum': 3.0,
                    'preferred': 5.0,
                    'excellent': 8.0
                },
                'quartile': {
                    'minimum': 'Q3',
                    'preferred': 'Q2',
                    'excellent': 'Q1'
                },
                'phm_specific': {
                    'relevance_threshold': 0.6,
                    'core_venues': [
                        'Mechanical Systems and Signal Processing',
                        'IEEE Transactions on Industrial Electronics',
                        'Reliability Engineering & System Safety',
                        'Expert Systems with Applications',
                        'Applied Soft Computing',
                        'Knowledge-Based Systems',
                        'IEEE Transactions on Reliability',
                        'ISA Transactions',
                        'Measurement',
                        'Sensors',
                        'Neurocomputing'
                    ]
                }
            }
        }
    
    def _load_publisher_database(self):
        """加载出版商数据库"""
        self.publisher_info = {
            # 知名出版商及其评级
            'ieee': {'rating': 'excellent', 'type': 'technical_society'},
            'elsevier': {'rating': 'excellent', 'type': 'commercial'},
            'springer': {'rating': 'excellent', 'type': 'commercial'},
            'nature publishing group': {'rating': 'excellent', 'type': 'commercial'},
            'wiley': {'rating': 'excellent', 'type': 'commercial'},
            'taylor & francis': {'rating': 'good', 'type': 'commercial'},
            
            # 质量有争议的出版商
            'mdpi': {'rating': 'questionable', 'type': 'open_access', 'note': 'Quality varies by journal'},
            'hindawi': {'rating': 'questionable', 'type': 'open_access', 'note': 'Some quality concerns'},
            'bentham science': {'rating': 'poor', 'type': 'commercial', 'note': 'Known predatory practices'},
            'omics international': {'rating': 'poor', 'type': 'commercial', 'note': 'Predatory publisher'},
        }
    
    def _load_journal_database(self):
        """加载期刊数据库"""
        self.journal_info = {
            # PHM核心期刊
            'mechanical systems and signal processing': {
                'impact_factor': 8.4, 'quartile': 'Q1', 'category': 'engineering',
                'phm_relevance': 1.0, 'publisher': 'elsevier'
            },
            'ieee transactions on industrial electronics': {
                'impact_factor': 8.2, 'quartile': 'Q1', 'category': 'engineering',
                'phm_relevance': 0.9, 'publisher': 'ieee'
            },
            'reliability engineering & system safety': {
                'impact_factor': 7.6, 'quartile': 'Q1', 'category': 'engineering',
                'phm_relevance': 1.0, 'publisher': 'elsevier'
            },
            'expert systems with applications': {
                'impact_factor': 8.5, 'quartile': 'Q1', 'category': 'computer_science',
                'phm_relevance': 0.7, 'publisher': 'elsevier'
            },
            'applied soft computing': {
                'impact_factor': 8.7, 'quartile': 'Q1', 'category': 'computer_science',
                'phm_relevance': 0.6, 'publisher': 'elsevier'
            },
            'knowledge-based systems': {
                'impact_factor': 8.8, 'quartile': 'Q1', 'category': 'computer_science',
                'phm_relevance': 0.6, 'publisher': 'elsevier'
            },
            'ieee transactions on reliability': {
                'impact_factor': 5.9, 'quartile': 'Q1', 'category': 'engineering',
                'phm_relevance': 1.0, 'publisher': 'ieee'
            },
            'isa transactions': {
                'impact_factor': 7.3, 'quartile': 'Q1', 'category': 'engineering',
                'phm_relevance': 0.8, 'publisher': 'elsevier'
            },
            'measurement': {
                'impact_factor': 5.6, 'quartile': 'Q1', 'category': 'engineering',
                'phm_relevance': 0.7, 'publisher': 'elsevier'
            },
            'sensors': {
                'impact_factor': 3.9, 'quartile': 'Q2', 'category': 'engineering',
                'phm_relevance': 0.8, 'publisher': 'mdpi'
            },
            'neurocomputing': {
                'impact_factor': 6.0, 'quartile': 'Q1', 'category': 'computer_science',
                'phm_relevance': 0.5, 'publisher': 'elsevier'
            }
        }
    
    def filter_papers(self, papers: List[Dict[str, Any]], 
                     criteria: Optional[FilterCriteria] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        过滤论文列表
        
        Args:
            papers: 论文元数据列表
            criteria: 过滤标准，如果为None则使用默认配置
            
        Returns:
            (filtered_papers, filter_report) 过滤后的论文列表和过滤报告
        """
        if criteria is None:
            criteria = self._get_default_filter_criteria()
        
        filtered_papers = []
        filter_report = {
            'total_papers': len(papers),
            'filtered_papers': 0,
            'filter_reasons': {},
            'quality_distribution': {},
            'publisher_distribution': {},
            'statistics': {}
        }
        
        for paper in papers:
            # 评估论文质量
            quality_assessment = self.assess_paper_quality(paper)
            
            # 应用过滤标准
            filter_result = self._apply_filter_criteria(paper, quality_assessment, criteria)
            
            if filter_result['passed']:
                # 添加质量评估信息到论文元数据
                paper['quality_assessment'] = quality_assessment
                paper['filter_score'] = filter_result['score']
                filtered_papers.append(paper)
            else:
                # 记录过滤原因
                for reason in filter_result['reasons']:
                    filter_report['filter_reasons'][reason] = filter_report['filter_reasons'].get(reason, 0) + 1
        
        # 生成统计报告
        filter_report['filtered_papers'] = len(filtered_papers)
        filter_report['filter_rate'] = (len(papers) - len(filtered_papers)) / len(papers) if papers else 0
        
        # 按质量分数排序
        filtered_papers.sort(key=lambda x: x.get('filter_score', 0), reverse=True)
        
        logger.info(f"Filtered {len(papers)} papers to {len(filtered_papers)} papers ({filter_report['filter_rate']:.2%} filtered out)")
        
        return filtered_papers, filter_report
    
    def assess_paper_quality(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估单篇论文的质量
        
        Args:
            paper: 论文元数据
            
        Returns:
            质量评估结果
        """
        assessment = {
            'overall_score': 0.0,
            'venue_score': 0.0,
            'publisher_score': 0.0,
            'impact_score': 0.0,
            'citation_score': 0.0,
            'phm_relevance_score': 0.0,
            'quality_tier': 'unknown',
            'warnings': [],
            'strengths': []
        }
        
        # 获取基本信息
        venue = paper.get('venue', '').lower().strip()
        publisher = self._extract_publisher(paper)
        impact_factor = paper.get('impact_factor', 0.0)
        citation_count = paper.get('citation_count', 0)
        phm_relevance = paper.get('phm_relevance_score', 0.0)
        year = paper.get('year', 2024)
        
        # 1. 期刊/会议评分 (40%)
        venue_info = self.journal_info.get(venue, {})
        if venue_info:
            assessment['venue_score'] = self._calculate_venue_score(venue_info)
            if venue_info.get('quartile') == 'Q1':
                assessment['strengths'].append('Published in Q1 journal')
        else:
            assessment['warnings'].append('Unknown venue quality')
        
        # 2. 出版商评分 (20%)
        if publisher:
            publisher_info = self.publisher_info.get(publisher.lower(), {})
            assessment['publisher_score'] = self._calculate_publisher_score(publisher_info)
            if publisher_info.get('rating') == 'excellent':
                assessment['strengths'].append('Excellent publisher')
            elif publisher_info.get('rating') in ['questionable', 'poor']:
                assessment['warnings'].append(f'Publisher quality concern: {publisher_info.get("note", "")}')
        
        # 3. 影响因子评分 (15%)
        assessment['impact_score'] = self._calculate_impact_score(impact_factor)
        if impact_factor >= 8.0:
            assessment['strengths'].append('High impact factor')
        elif impact_factor < 3.0:
            assessment['warnings'].append('Low impact factor')
        
        # 4. 引用数评分 (15%)
        assessment['citation_score'] = self._calculate_citation_score(citation_count, year)
        if citation_count > 100:
            assessment['strengths'].append('High citation count')
        
        # 5. PHM相关性评分 (10%)
        assessment['phm_relevance_score'] = phm_relevance
        if phm_relevance >= 0.8:
            assessment['strengths'].append('High PHM relevance')
        elif phm_relevance < 0.5:
            assessment['warnings'].append('Low PHM relevance')
        
        # 计算总分
        assessment['overall_score'] = (
            assessment['venue_score'] * 0.4 +
            assessment['publisher_score'] * 0.2 +
            assessment['impact_score'] * 0.15 +
            assessment['citation_score'] * 0.15 +
            assessment['phm_relevance_score'] * 0.1
        )
        
        # 确定质量等级
        assessment['quality_tier'] = self._determine_quality_tier(assessment['overall_score'])
        
        return assessment
    
    def _calculate_venue_score(self, venue_info: Dict[str, Any]) -> float:
        """计算期刊/会议评分"""
        if not venue_info:
            return 0.2
        
        quartile = venue_info.get('quartile', 'Q4')
        if quartile == 'Q1':
            return 1.0
        elif quartile == 'Q2':
            return 0.8
        elif quartile == 'Q3':
            return 0.6
        else:
            return 0.4
    
    def _calculate_publisher_score(self, publisher_info: Dict[str, Any]) -> float:
        """计算出版商评分"""
        if not publisher_info:
            return 0.5
        
        rating = publisher_info.get('rating', 'unknown')
        if rating == 'excellent':
            return 1.0
        elif rating == 'good':
            return 0.8
        elif rating == 'questionable':
            return 0.4
        elif rating == 'poor':
            return 0.1
        else:
            return 0.5
    
    def _calculate_impact_score(self, impact_factor: float) -> float:
        """计算影响因子评分"""
        if impact_factor >= 8.0:
            return 1.0
        elif impact_factor >= 5.0:
            return 0.8
        elif impact_factor >= 3.0:
            return 0.6
        elif impact_factor >= 1.0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_citation_score(self, citation_count: int, year: int) -> float:
        """计算引用数评分（考虑时间因素）"""
        current_year = 2024
        age = current_year - year
        
        # 根据论文年龄调整期望引用数
        if age <= 1:
            expected_citations = 5
        elif age <= 2:
            expected_citations = 15
        elif age <= 5:
            expected_citations = 30
        else:
            expected_citations = 50
        
        ratio = citation_count / expected_citations
        return min(ratio, 1.0)
    
    def _determine_quality_tier(self, score: float) -> str:
        """确定质量等级"""
        if score >= 0.85:
            return 'excellent'
        elif score >= 0.70:
            return 'good'
        elif score >= 0.55:
            return 'acceptable'
        elif score >= 0.40:
            return 'questionable'
        else:
            return 'poor'
    
    def _extract_publisher(self, paper: Dict[str, Any]) -> Optional[str]:
        """从论文信息中提取出版商"""
        # 直接从元数据获取
        if 'publisher' in paper:
            return paper['publisher']
        
        # 从期刊名称推断
        venue = paper.get('venue', '').lower()
        
        if 'ieee' in venue:
            return 'ieee'
        elif any(keyword in venue for keyword in ['elsevier', 'science direct']):
            return 'elsevier'
        elif 'springer' in venue:
            return 'springer'
        elif 'nature' in venue:
            return 'nature publishing group'
        elif 'wiley' in venue:
            return 'wiley'
        elif 'mdpi' in venue:
            return 'mdpi'
        elif 'hindawi' in venue:
            return 'hindawi'
        
        # 从DOI推断
        doi = paper.get('doi', '')
        if doi:
            if '10.1109' in doi:
                return 'ieee'
            elif '10.1016' in doi:
                return 'elsevier'
            elif '10.1007' in doi:
                return 'springer'
            elif '10.1038' in doi:
                return 'nature publishing group'
            elif '10.3390' in doi:
                return 'mdpi'
        
        return None
    
    def _apply_filter_criteria(self, paper: Dict[str, Any], 
                              assessment: Dict[str, Any], 
                              criteria: FilterCriteria) -> Dict[str, Any]:
        """应用过滤标准"""
        result = {
            'passed': True,
            'reasons': [],
            'score': assessment['overall_score']
        }
        
        publisher = self._extract_publisher(paper)
        venue = paper.get('venue', '').lower()
        impact_factor = paper.get('impact_factor', 0.0)
        quartile = assessment.get('venue_score', 0.0)
        citation_count = paper.get('citation_count', 0)
        phm_relevance = paper.get('phm_relevance_score', 0.0)
        paper_type = paper.get('venue_type', paper.get('type', 'journal'))
        
        # 1. 出版商黑名单检查
        if publisher and publisher.lower() in [p.lower() for p in criteria.exclude_publishers]:
            result['passed'] = False
            result['reasons'].append(f'Excluded publisher: {publisher}')
        
        # 2. 出版商白名单检查（如果指定了白名单）
        if criteria.include_publishers and publisher:
            if publisher.lower() not in [p.lower() for p in criteria.include_publishers]:
                result['passed'] = False
                result['reasons'].append(f'Not in approved publisher list: {publisher}')
        
        # 3. 影响因子检查
        if impact_factor > 0 and impact_factor < criteria.min_impact_factor:
            result['passed'] = False
            result['reasons'].append(f'Impact factor {impact_factor} below minimum {criteria.min_impact_factor}')
        
        # 4. 期刊分级检查
        quartile_scores = {'Q1': 1.0, 'Q2': 0.8, 'Q3': 0.6, 'Q4': 0.4}
        min_quartile_score = quartile_scores.get(criteria.min_quartile, 0.0)
        if assessment['venue_score'] < min_quartile_score:
            result['passed'] = False
            result['reasons'].append(f'Journal quality below {criteria.min_quartile}')
        
        # 5. 引用数检查
        if citation_count < criteria.min_citation_count:
            result['passed'] = False
            result['reasons'].append(f'Citation count {citation_count} below minimum {criteria.min_citation_count}')
        
        # 6. PHM相关性检查
        if phm_relevance < criteria.phm_relevance_threshold:
            result['passed'] = False
            result['reasons'].append(f'PHM relevance {phm_relevance:.2f} below threshold {criteria.phm_relevance_threshold}')
        
        # 7. 预印本检查
        if not criteria.allow_preprints and paper_type in ['preprint', 'arxiv']:
            result['passed'] = False
            result['reasons'].append('Preprints not allowed')
        
        # 8. 自定义规则检查
        for rule in criteria.custom_rules:
            if self._evaluate_custom_rule(paper, assessment, rule):
                if rule.get('action') == 'exclude':
                    result['passed'] = False
                    result['reasons'].append(f'Custom rule: {rule.get("name", "unnamed rule")}')
                elif rule.get('action') == 'boost':
                    result['score'] += rule.get('boost_amount', 0.1)
        
        return result
    
    def _evaluate_custom_rule(self, paper: Dict[str, Any], 
                             assessment: Dict[str, Any], 
                             rule: Dict[str, Any]) -> bool:
        """评估自定义规则"""
        # 这里可以实现更复杂的规则逻辑
        # 目前简单实现基于条件字符串的评估
        condition = rule.get('condition', '')
        
        # 简化的条件评估（实际实现可以更复杂）
        if 'citation_count >' in condition:
            threshold = int(re.search(r'citation_count > (\d+)', condition).group(1))
            return paper.get('citation_count', 0) > threshold
        
        return False
    
    def _get_default_filter_criteria(self) -> FilterCriteria:
        """获取默认过滤标准"""
        config = self.config.get('quality_filters', {})
        
        return FilterCriteria(
            exclude_publishers=config.get('publisher_blacklist', []),
            include_publishers=config.get('publisher_whitelist', []),
            min_impact_factor=config.get('impact_factor', {}).get('minimum', 0.0),
            min_quartile=config.get('quartile', {}).get('minimum', 'Q4'),
            min_citation_count=0,
            phm_relevance_threshold=config.get('phm_specific', {}).get('relevance_threshold', 0.0),
            allow_preprints=True
        )
    
    def get_filter_summary(self, filter_report: Dict[str, Any]) -> str:
        """生成过滤摘要报告"""
        total = filter_report['total_papers']
        filtered = filter_report['filtered_papers']
        filter_rate = filter_report['filter_rate']
        
        summary = f"📊 质量过滤报告\n"
        summary += f"总论文数: {total}\n"
        summary += f"通过过滤: {filtered}\n"
        summary += f"过滤率: {filter_rate:.1%}\n\n"
        
        if filter_report['filter_reasons']:
            summary += "主要过滤原因:\n"
            for reason, count in sorted(filter_report['filter_reasons'].items(), 
                                      key=lambda x: x[1], reverse=True):
                summary += f"  - {reason}: {count}篇\n"
        
        return summary


def create_filter_with_config(**kwargs) -> PaperQualityFilter:
    """
    便捷函数：创建带有指定配置的过滤器
    
    Args:
        **kwargs: 过滤配置参数
        
    Returns:
        配置好的质量过滤器实例
    """
    filter_obj = PaperQualityFilter()
    
    # 更新配置
    if kwargs:
        config_updates = {'quality_filters': kwargs}
        filter_obj.config.update(config_updates)
    
    return filter_obj


# 便捷函数：常用过滤器配置
def create_strict_filter() -> PaperQualityFilter:
    """创建严格的质量过滤器"""
    return create_filter_with_config(
        publisher_blacklist=['mdpi', 'hindawi', 'bentham science'],
        impact_factor={'minimum': 5.0},
        quartile={'minimum': 'Q2'},
        phm_specific={'relevance_threshold': 0.7}
    )


def create_moderate_filter() -> PaperQualityFilter:
    """创建中等严格的质量过滤器"""
    return create_filter_with_config(
        publisher_blacklist=['bentham science', 'omics international'],
        impact_factor={'minimum': 3.0},
        quartile={'minimum': 'Q3'},
        phm_specific={'relevance_threshold': 0.5}
    )


def create_permissive_filter() -> PaperQualityFilter:
    """创建宽松的质量过滤器"""
    return create_filter_with_config(
        publisher_blacklist=['omics international'],
        impact_factor={'minimum': 1.0},
        quartile={'minimum': 'Q4'},
        phm_specific={'relevance_threshold': 0.3}
    )


if __name__ == "__main__":
    # 测试质量过滤器
    test_papers = [
        {
            'title': 'Deep Learning for Bearing Fault Diagnosis',
            'venue': 'Mechanical Systems and Signal Processing',
            'impact_factor': 8.4,
            'citation_count': 150,
            'phm_relevance_score': 0.95,
            'year': 2023
        },
        {
            'title': 'Some Random Study',
            'venue': 'Random MDPI Journal',
            'impact_factor': 2.1,
            'citation_count': 5,
            'phm_relevance_score': 0.3,
            'year': 2024,
            'publisher': 'mdpi'
        }
    ]
    
    # 测试不同严格程度的过滤器
    for filter_name, filter_func in [
        ('Strict', create_strict_filter),
        ('Moderate', create_moderate_filter), 
        ('Permissive', create_permissive_filter)
    ]:
        print(f"\n=== {filter_name} Filter Test ===")
        filter_obj = filter_func()
        filtered_papers, report = filter_obj.filter_papers(test_papers)
        print(f"Filtered {len(test_papers)} -> {len(filtered_papers)} papers")
        print(filter_obj.get_filter_summary(report))