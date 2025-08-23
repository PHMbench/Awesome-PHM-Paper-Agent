#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试用例：论文质量过滤功能验证
Test Cases: Paper Quality Filter Functionality Validation

测试覆盖范围：
- 基础质量过滤功能
- 出版商黑名单/白名单过滤
- 影响因子和期刊分区过滤
- PHM相关性评分
- 多维度质量评估
- 配置文件加载和应用
"""

import pytest
import os
import sys
import tempfile
import yaml
from typing import Dict, List, Any, Optional
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.paper_quality_filter import PaperQualityFilter, FilterCriteria


class TestPaperQualityFilter:
    """论文质量过滤器测试类"""
    
    @pytest.fixture
    def sample_config(self) -> Dict[str, Any]:
        """示例配置数据"""
        return {
            'basic_filters': {
                'impact_factor_threshold': 5.0,
                'min_quartile': 'Q2',
                'min_year': 2020,
                'min_citations': 0,
                'require_peer_reviewed': True
            },
            'publishers': {
                'blacklist': ['MDPI', 'Hindawi', 'Scientific Research Publishing'],
                'suspicious': ['Frontiers Media'],
                'whitelist': ['IEEE', 'Elsevier', 'Springer Nature', 'Wiley']
            },
            'phm_specific': {
                'min_relevance_score': 0.6,
                'top_tier_venues': [
                    'Mechanical Systems and Signal Processing',
                    'IEEE Transactions on Industrial Electronics'
                ],
                'keyword_weights': {
                    'prognostics': 1.0,
                    'fault diagnosis': 0.9,
                    'deep learning': 0.7
                }
            },
            'quality_tiers': {
                'top_tier': {
                    'min_impact_factor': 8.0,
                    'min_citations': 100,
                    'max_quartile': 'Q1'
                },
                'excellent': {
                    'min_impact_factor': 5.0,
                    'min_citations': 50,
                    'max_quartile': 'Q1'
                }
            }
        }
    
    @pytest.fixture
    def sample_papers(self) -> List[Dict[str, Any]]:
        """示例论文数据"""
        return [
            {
                'id': '2024-MSSP-Zhang-DeepLearning',
                'title': 'Deep Learning for Bearing Fault Diagnosis',
                'authors': ['Zhang Wei', 'Liu Ming'],
                'year': 2024,
                'venue': 'Mechanical Systems and Signal Processing',
                'publisher': 'Elsevier',
                'doi': '10.1016/j.ymssp.2024.001',
                'abstract': 'This paper presents a novel deep learning approach for prognostics and fault diagnosis of bearings.',
                'keywords': ['prognostics', 'fault diagnosis', 'deep learning', 'bearings'],
                'quality_indicators': {
                    'impact_factor': 8.4,
                    'quartile': 'Q1',
                    'citations': 156,
                    'peer_reviewed': True,
                    'open_access': True
                }
            },
            {
                'id': '2024-MDPI-Smith-BasicCNN',
                'title': 'Basic CNN for Fault Classification',
                'authors': ['Smith John'],
                'year': 2024,
                'venue': 'Sensors',
                'publisher': 'MDPI',
                'doi': '10.3390/s24001234',
                'abstract': 'A simple CNN approach for fault classification.',
                'keywords': ['CNN', 'classification'],
                'quality_indicators': {
                    'impact_factor': 3.8,
                    'quartile': 'Q2',
                    'citations': 12,
                    'peer_reviewed': True,
                    'open_access': True
                }
            },
            {
                'id': '2023-IEEE-Wang-Prognostics',
                'title': 'Advanced Prognostics for Health Management',
                'authors': ['Wang Lei', 'Chen Hui'],
                'year': 2023,
                'venue': 'IEEE Transactions on Industrial Electronics',
                'publisher': 'IEEE',
                'doi': '10.1109/TIE.2023.001',
                'abstract': 'This work focuses on health management and predictive maintenance using prognostics.',
                'keywords': ['prognostics', 'health management', 'predictive maintenance'],
                'quality_indicators': {
                    'impact_factor': 8.2,
                    'quartile': 'Q1',
                    'citations': 89,
                    'peer_reviewed': True,
                    'open_access': False
                }
            },
            {
                'id': '2019-Hindawi-Old-Paper',
                'title': 'Outdated Method for Fault Detection',
                'authors': ['Old Author'],
                'year': 2019,
                'venue': 'Mathematical Problems in Engineering',
                'publisher': 'Hindawi',
                'doi': '10.1155/2019/1234567',
                'abstract': 'An old paper with outdated methods.',
                'keywords': ['fault detection'],
                'quality_indicators': {
                    'impact_factor': 1.2,
                    'quartile': 'Q3',
                    'citations': 5,
                    'peer_reviewed': True,
                    'open_access': True
                }
            }
        ]
    
    @pytest.fixture
    def temp_config_file(self, sample_config) -> str:
        """创建临时配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config, f)
            return f.name
    
    @pytest.fixture
    def quality_filter(self, temp_config_file) -> PaperQualityFilter:
        """创建质量过滤器实例"""
        return PaperQualityFilter(temp_config_file)
    
    def test_filter_initialization(self, temp_config_file):
        """测试过滤器初始化"""
        filter_instance = PaperQualityFilter(temp_config_file)
        assert filter_instance.config is not None
        assert 'basic_filters' in filter_instance.config
        assert 'publishers' in filter_instance.config
    
    def test_publisher_blacklist_filtering(self, quality_filter, sample_papers):
        """测试出版商黑名单过滤"""
        criteria = FilterCriteria(exclude_publishers=['MDPI', 'Hindawi'])
        
        filtered_papers, stats = quality_filter.filter_papers(sample_papers, criteria)
        
        # 验证MDPI和Hindawi的论文被过滤掉
        publishers = [paper.get('publisher') for paper in filtered_papers]
        assert 'MDPI' not in publishers
        assert 'Hindawi' not in publishers
        
        # 验证统计信息
        assert stats['total_papers'] == len(sample_papers)
        assert stats['filtered_count'] >= 2  # 至少过滤掉MDPI和Hindawi的论文
    
    def test_impact_factor_filtering(self, quality_filter, sample_papers):
        """测试影响因子过滤"""
        criteria = FilterCriteria(min_impact_factor=5.0)
        
        filtered_papers, stats = quality_filter.filter_papers(sample_papers, criteria)
        
        # 验证所有保留的论文影响因子>=5.0
        for paper in filtered_papers:
            if_score = paper.get('quality_indicators', {}).get('impact_factor', 0)
            assert if_score >= 5.0
    
    def test_quartile_filtering(self, quality_filter, sample_papers):
        """测试期刊分区过滤"""
        criteria = FilterCriteria(max_quartile='Q1')
        
        filtered_papers, stats = quality_filter.filter_papers(sample_papers, criteria)
        
        # 验证所有保留的论文都是Q1期刊
        for paper in filtered_papers:
            quartile = paper.get('quality_indicators', {}).get('quartile', 'Q4')
            assert quartile == 'Q1'
    
    def test_year_filtering(self, quality_filter, sample_papers):
        """测试年份过滤"""
        criteria = FilterCriteria(min_year=2020)
        
        filtered_papers, stats = quality_filter.filter_papers(sample_papers, criteria)
        
        # 验证所有保留的论文年份>=2020
        for paper in filtered_papers:
            assert paper.get('year', 0) >= 2020
    
    def test_citation_filtering(self, quality_filter, sample_papers):
        """测试引用数过滤"""
        criteria = FilterCriteria(min_citations=50)
        
        filtered_papers, stats = quality_filter.filter_papers(sample_papers, criteria)
        
        # 验证所有保留的论文引用数>=50
        for paper in filtered_papers:
            citations = paper.get('quality_indicators', {}).get('citations', 0)
            assert citations >= 50
    
    def test_phm_relevance_assessment(self, quality_filter, sample_papers):
        """测试PHM相关性评估"""
        for paper in sample_papers:
            relevance_score = quality_filter._assess_phm_relevance(paper)
            
            # 验证相关性分数在合理范围内
            assert 0.0 <= relevance_score <= 1.0
            
            # 验证包含PHM关键词的论文获得更高分数
            abstract = paper.get('abstract', '').lower()
            keywords = [kw.lower() for kw in paper.get('keywords', [])]
            
            if 'prognostics' in abstract or 'prognostics' in keywords:
                assert relevance_score >= 0.8  # 应该获得高分
    
    def test_quality_tier_classification(self, quality_filter, sample_papers):
        """测试质量分级分类"""
        for paper in sample_papers:
            quality_assessment = quality_filter.assess_paper_quality(paper)
            
            # 验证质量评估结构
            assert 'overall_score' in quality_assessment
            assert 'tier' in quality_assessment
            assert 'breakdown' in quality_assessment
            
            # 验证分数范围
            assert 0.0 <= quality_assessment['overall_score'] <= 1.0
            
            # 验证分级逻辑
            score = quality_assessment['overall_score']
            tier = quality_assessment['tier']
            
            if score >= 0.85:
                assert tier == 'top_tier'
            elif score >= 0.70:
                assert tier == 'excellent'
            elif score >= 0.55:
                assert tier == 'good'
    
    def test_combined_filtering(self, quality_filter, sample_papers):
        """测试组合过滤条件"""
        criteria = FilterCriteria(
            exclude_publishers=['MDPI', 'Hindawi'],
            min_impact_factor=5.0,
            max_quartile='Q1',
            min_year=2020,
            min_citations=50
        )
        
        filtered_papers, stats = quality_filter.filter_papers(sample_papers, criteria)
        
        # 验证所有过滤条件都被应用
        for paper in filtered_papers:
            # 出版商检查
            publisher = paper.get('publisher')
            assert publisher not in ['MDPI', 'Hindawi']
            
            # 影响因子检查
            if_score = paper.get('quality_indicators', {}).get('impact_factor', 0)
            assert if_score >= 5.0
            
            # 分区检查
            quartile = paper.get('quality_indicators', {}).get('quartile', 'Q4')
            assert quartile == 'Q1'
            
            # 年份检查
            assert paper.get('year', 0) >= 2020
            
            # 引用数检查
            citations = paper.get('quality_indicators', {}).get('citations', 0)
            assert citations >= 50
    
    def test_empty_paper_list(self, quality_filter):
        """测试空论文列表处理"""
        filtered_papers, stats = quality_filter.filter_papers([])
        
        assert len(filtered_papers) == 0
        assert stats['total_papers'] == 0
        assert stats['filtered_count'] == 0
    
    def test_missing_quality_indicators(self, quality_filter):
        """测试缺失质量指标的处理"""
        incomplete_paper = {
            'id': 'incomplete-paper',
            'title': 'Paper Without Quality Indicators',
            'authors': ['Unknown Author'],
            'year': 2024
        }
        
        # 应该能够处理缺失数据而不报错
        quality_assessment = quality_filter.assess_paper_quality(incomplete_paper)
        assert 'overall_score' in quality_assessment
        assert quality_assessment['overall_score'] >= 0.0
    
    def test_config_file_loading_error(self):
        """测试配置文件加载错误处理"""
        with pytest.raises(FileNotFoundError):
            PaperQualityFilter('/nonexistent/config.yaml')
    
    def test_statistics_calculation(self, quality_filter, sample_papers):
        """测试统计信息计算"""
        filtered_papers, stats = quality_filter.filter_papers(sample_papers)
        
        # 验证统计信息结构
        required_keys = [
            'total_papers', 'filtered_count', 'passed_count',
            'filter_reasons', 'quality_distribution'
        ]
        for key in required_keys:
            assert key in stats
        
        # 验证数量一致性
        assert stats['total_papers'] == len(sample_papers)
        assert stats['passed_count'] == len(filtered_papers)
        assert stats['filtered_count'] == stats['total_papers'] - stats['passed_count']
    
    def test_filter_criteria_validation(self, quality_filter):
        """测试过滤条件验证"""
        # 测试无效的分区设置
        invalid_criteria = FilterCriteria(max_quartile='Q5')  # 无效分区
        
        # 应该处理无效输入而不崩溃
        papers = [{'id': 'test', 'quality_indicators': {'quartile': 'Q1'}}]
        filtered_papers, stats = quality_filter.filter_papers(papers, invalid_criteria)
        
        # 验证能够正常执行
        assert isinstance(filtered_papers, list)
        assert isinstance(stats, dict)
    
    def test_phm_keyword_scoring(self, quality_filter):
        """测试PHM关键词评分逻辑"""
        # 高PHM相关性论文
        high_phm_paper = {
            'abstract': 'This paper focuses on prognostics and health management for predictive maintenance.',
            'keywords': ['prognostics', 'health management', 'fault diagnosis']
        }
        
        # 低PHM相关性论文
        low_phm_paper = {
            'abstract': 'A general machine learning approach for classification tasks.',
            'keywords': ['machine learning', 'classification', 'neural networks']
        }
        
        high_score = quality_filter._assess_phm_relevance(high_phm_paper)
        low_score = quality_filter._assess_phm_relevance(low_phm_paper)
        
        # 验证PHM相关论文获得更高分数
        assert high_score > low_score
        assert high_score >= 0.8
        assert low_score <= 0.5

    def test_performance_with_large_dataset(self, quality_filter):
        """测试大数据集性能"""
        # 创建大量论文数据
        large_dataset = []
        for i in range(1000):
            paper = {
                'id': f'paper-{i:04d}',
                'title': f'Paper {i}',
                'authors': [f'Author {i}'],
                'year': 2024,
                'publisher': 'IEEE' if i % 2 == 0 else 'MDPI',
                'quality_indicators': {
                    'impact_factor': 5.0 + (i % 5),
                    'quartile': 'Q1' if i % 3 == 0 else 'Q2',
                    'citations': i * 2,
                    'peer_reviewed': True
                }
            }
            large_dataset.append(paper)
        
        import time
        start_time = time.time()
        
        filtered_papers, stats = quality_filter.filter_papers(
            large_dataset, 
            FilterCriteria(exclude_publishers=['MDPI'])
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # 验证性能要求（应在合理时间内完成）
        assert processing_time < 5.0  # 5秒内处理1000篇论文
        assert len(filtered_papers) > 0
        assert stats['total_papers'] == 1000


class TestFilterCriteria:
    """过滤条件测试类"""
    
    def test_default_initialization(self):
        """测试默认初始化"""
        criteria = FilterCriteria()
        
        assert criteria.min_impact_factor is None
        assert criteria.max_quartile is None
        assert criteria.exclude_publishers is None
        assert criteria.include_publishers is None
        assert criteria.min_year is None
        assert criteria.min_citations is None
    
    def test_custom_initialization(self):
        """测试自定义初始化"""
        criteria = FilterCriteria(
            min_impact_factor=5.0,
            max_quartile='Q1',
            exclude_publishers=['MDPI'],
            min_year=2020
        )
        
        assert criteria.min_impact_factor == 5.0
        assert criteria.max_quartile == 'Q1'
        assert criteria.exclude_publishers == ['MDPI']
        assert criteria.min_year == 2020


class TestIntegration:
    """集成测试类"""
    
    def test_config_and_filter_integration(self, sample_config, sample_papers):
        """测试配置文件与过滤器的集成"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config, f)
            config_path = f.name
        
        try:
            # 初始化过滤器
            quality_filter = PaperQualityFilter(config_path)
            
            # 应用配置中的默认过滤标准
            filtered_papers, stats = quality_filter.filter_papers(sample_papers)
            
            # 验证过滤结果符合配置要求
            assert len(filtered_papers) <= len(sample_papers)
            assert stats['total_papers'] == len(sample_papers)
            
            # 验证过滤后的论文质量符合要求
            for paper in filtered_papers:
                publisher = paper.get('publisher')
                if publisher:
                    # 不应包含黑名单出版商
                    assert publisher not in sample_config['publishers']['blacklist']
                
                # 年份应符合要求
                year = paper.get('year', 0)
                min_year = sample_config['basic_filters']['min_year']
                assert year >= min_year
        
        finally:
            # 清理临时文件
            os.unlink(config_path)


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])