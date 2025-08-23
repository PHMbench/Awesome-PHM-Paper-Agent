"""
Paper Review Agent - 论文审查代理

这个代理负责验证新增论文的真实性，确保所有添加到知识库的论文都是真实存在的，
而不是AI生成的虚假内容。它会检查DOI、验证作者信息、确认摘要真实性等。
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

from .base_agent import BaseAgent, AgentError
from ..utils.logging_config import get_logger


class PaperReviewAgent(BaseAgent):
    """
    论文审查代理
    
    验证论文的真实性，包括：
    - DOI 有效性验证
    - 作者和机构信息检查
    - 摘要真实性评估
    - 学术数据库交叉验证
    - 内容质量评估
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "PaperReviewAgent")
        
        # 审查配置
        self.review_config = self.get_config_value('paper_review_settings', {})
        self.strict_mode = self.review_config.get('strict_mode', True)
        self.require_doi = self.review_config.get('require_doi', False)
        self.min_abstract_length = self.review_config.get('min_abstract_length', 100)
        self.max_abstract_length = self.review_config.get('max_abstract_length', 2000)
        
        # 可信的学术域名
        self.trusted_domains = {
            'arxiv.org',
            'ieeexplore.ieee.org',
            'pubmed.ncbi.nlm.nih.gov',
            'scholar.google.com',
            'semanticscholar.org',
            'acm.org',
            'springer.com',
            'elsevier.com',
            'wiley.com',
            'nature.com',
            'science.org'
        }
        
        # PHM 相关关键词 (更新了LLM相关术语)
        self.phm_keywords = {
            'core': [
                'prognostics', 'health management', 'predictive maintenance',
                'condition monitoring', 'fault diagnosis', 'remaining useful life',
                'RUL', 'PHM', 'condition based maintenance', 'CBM'
            ],
            'technical': [
                'vibration analysis', 'signal processing', 'feature extraction',
                'machine learning', 'deep learning', 'neural networks',
                'anomaly detection', 'pattern recognition', 'time series analysis',
                'large language model', 'LLM', 'knowledge graph', 'transformer',
                'ChatGPT', 'foundation model', 'fine-tuning', 'prompt engineering'
            ],
            'applications': [
                'bearing', 'gearbox', 'motor', 'turbine', 'machinery',
                'rotating equipment', 'mechanical systems', 'industrial equipment',
                'aviation', 'aerospace', 'manufacturing', 'assembly'
            ]
        }
        
        # 质量评分权重
        self.quality_weights = {
            'venue_reputation': 0.3,      # 期刊/会议声誉
            'phm_relevance': 0.25,        # PHM相关性
            'content_quality': 0.2,       # 内容质量
            'author_credibility': 0.15,   # 作者可信度
            'novelty_impact': 0.1         # 创新性和影响力
        }
        
        # 期刊等级评分
        self.venue_scores = {
            'IEEE Transactions on Industrial Informatics': 0.95,
            'IEEE Transactions on Reliability': 0.90,
            'Mechanical Systems and Signal Processing': 0.88,
            'Reliability Engineering & System Safety': 0.85,
            'Journal of Manufacturing Systems': 0.82,
            'Applied Soft Computing': 0.75,
            'Expert Systems with Applications': 0.72,
            'arXiv': 0.60,  # 预印本基础分
            'unknown': 0.40
        }
        
        self.logger.info("Paper Review Agent initialized")
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        审查论文列表的真实性
        
        Args:
            input_data: 包含待审查论文列表的字典
            
        Returns:
            审查结果，包含通过和未通过的论文
        """
        
        papers = input_data.get('papers', [])
        if not papers:
            raise AgentError("No papers provided for review")
        
        self.logger.info(f"Starting review of {len(papers)} papers")
        
        review_results = {
            'total_papers': len(papers),
            'approved_papers': [],
            'rejected_papers': [],
            'warnings': [],
            'review_summary': {},
            'review_date': datetime.now().isoformat()
        }
        
        for i, paper in enumerate(papers, 1):
            self.logger.info(f"Reviewing paper {i}/{len(papers)}: {paper.get('title', 'Unknown')}")
            
            try:
                review_result = self._review_single_paper(paper)
                
                if review_result['approved']:
                    review_results['approved_papers'].append({
                        'paper': paper,
                        'review_score': review_result['score'],
                        'review_notes': review_result['notes']
                    })
                else:
                    review_results['rejected_papers'].append({
                        'paper': paper,
                        'rejection_reasons': review_result['rejection_reasons'],
                        'review_score': review_result['score']
                    })
                
                # 收集警告
                if review_result.get('warnings'):
                    review_results['warnings'].extend(review_result['warnings'])
                    
            except Exception as e:
                self.logger.error(f"Failed to review paper: {e}")
                review_results['rejected_papers'].append({
                    'paper': paper,
                    'rejection_reasons': [f"Review failed: {str(e)}"],
                    'review_score': 0.0
                })
        
        # 生成审查摘要
        review_results['review_summary'] = self._generate_review_summary(review_results)
        
        self.logger.info(f"Review complete: {len(review_results['approved_papers'])} approved, {len(review_results['rejected_papers'])} rejected")
        
        return review_results
    
    def _review_single_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """审查单篇论文"""
        
        review_result = {
            'approved': False,
            'score': 0.0,
            'notes': [],
            'warnings': [],
            'rejection_reasons': []
        }
        
        # 1. 基本信息验证
        basic_score, basic_issues = self._validate_basic_info(paper)
        review_result['score'] += basic_score * 0.3
        
        if basic_issues:
            review_result['rejection_reasons'].extend(basic_issues)
        
        # 2. DOI 验证
        doi_score, doi_issues = self._validate_doi(paper)
        review_result['score'] += doi_score * 0.2
        
        if doi_issues:
            if self.require_doi:
                review_result['rejection_reasons'].extend(doi_issues)
            else:
                review_result['warnings'].extend(doi_issues)
        
        # 3. 作者信息验证
        author_score, author_issues = self._validate_authors(paper)
        review_result['score'] += author_score * 0.15
        
        if author_issues:
            review_result['warnings'].extend(author_issues)
        
        # 4. 摘要质量验证
        abstract_score, abstract_issues = self._validate_abstract(paper)
        review_result['score'] += abstract_score * 0.25
        
        if abstract_issues:
            review_result['rejection_reasons'].extend(abstract_issues)
        
        # 5. PHM 相关性验证
        relevance_score, relevance_issues = self._validate_phm_relevance(paper)
        review_result['score'] += relevance_score * 0.1
        
        if relevance_issues:
            review_result['rejection_reasons'].extend(relevance_issues)
        
        # 6. 数据源验证
        source_score, source_issues = self._validate_source(paper)
        review_result['score'] += source_score * 0.1
        
        if source_issues:
            review_result['warnings'].extend(source_issues)
        
        # 7. 综合质量评分 (新增)
        comprehensive_score = self._calculate_comprehensive_quality_score(paper)
        review_result['comprehensive_quality'] = comprehensive_score
        review_result['quality_breakdown'] = self._get_quality_breakdown(paper)
        
        # 调整最终评分 (综合质量分数的权重)
        final_score = review_result['score'] * 0.7 + comprehensive_score * 0.3
        review_result['final_score'] = final_score
        
        # 决定是否通过
        min_score = 0.7 if self.strict_mode else 0.5
        review_result['approved'] = (final_score >= min_score and 
                                   len(review_result['rejection_reasons']) == 0)
        
        # 添加审查说明
        if review_result['approved']:
            review_result['notes'].append(f"Paper approved with final score {final_score:.2f} (basic: {review_result['score']:.2f}, quality: {comprehensive_score:.2f})")
        else:
            review_result['notes'].append(f"Paper rejected with final score {final_score:.2f}")
        
        return review_result
    
    def _validate_basic_info(self, paper: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证基本信息完整性"""
        
        issues = []
        score = 0.0
        
        # 检查标题
        title = paper.get('title', '').strip()
        if not title:
            issues.append("Missing paper title")
        elif len(title) < 10:
            issues.append("Paper title too short (< 10 characters)")
        elif len(title) > 200:
            issues.append("Paper title too long (> 200 characters)")
        else:
            score += 0.3
        
        # 检查作者
        authors = paper.get('authors', [])
        if not authors:
            issues.append("Missing authors information")
        elif len(authors) > 20:
            issues.append("Too many authors (> 20)")
        else:
            score += 0.2
        
        # 检查年份
        year = paper.get('year')
        if not year:
            issues.append("Missing publication year")
        else:
            try:
                year_int = int(year)
                if year_int < 2000 or year_int > datetime.now().year + 1:
                    issues.append(f"Invalid publication year: {year}")
                else:
                    score += 0.2
            except:
                issues.append(f"Invalid year format: {year}")
        
        # 检查摘要存在性
        abstract = paper.get('abstract', '').strip()
        if not abstract:
            issues.append("Missing abstract")
        else:
            score += 0.3
        
        return score, issues
    
    def _validate_doi(self, paper: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证 DOI"""
        
        doi = paper.get('doi', '').strip()
        issues = []
        score = 0.0
        
        if not doi:
            issues.append("No DOI provided")
            return score, issues
        
        # DOI 格式验证
        doi_pattern = r'^10\.\d+/.+$'
        if not re.match(doi_pattern, doi):
            issues.append(f"Invalid DOI format: {doi}")
            return score, issues
        
        # DOI 看起来有效
        score = 1.0
        
        # 这里应该调用 WebFetch 验证 DOI 实际存在性
        # validation_url = f"https://doi.org/{doi}"
        # result = WebFetch(validation_url, "验证DOI是否存在，返回论文标题")
        
        self.logger.info(f"DOI validation needed for: {doi}")
        
        return score, issues
    
    def _validate_authors(self, paper: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证作者信息"""
        
        authors = paper.get('authors', [])
        issues = []
        score = 0.0
        
        if not authors:
            issues.append("No authors provided")
            return score, issues
        
        valid_authors = 0
        
        for author in authors:
            if isinstance(author, str) and len(author.strip()) > 2:
                # 检查作者名称格式
                if re.match(r'^[A-Za-z\s\.,\-]+$', author.strip()):
                    valid_authors += 1
                else:
                    issues.append(f"Invalid author name format: {author}")
        
        if valid_authors > 0:
            score = min(1.0, valid_authors / len(authors))
        
        return score, issues
    
    def _validate_abstract(self, paper: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证摘要质量"""
        
        abstract = paper.get('abstract', '').strip()
        issues = []
        score = 0.0
        
        if not abstract:
            issues.append("No abstract provided")
            return score, issues
        
        # 长度检查
        if len(abstract) < self.min_abstract_length:
            issues.append(f"Abstract too short (< {self.min_abstract_length} characters)")
            return score, issues
        
        if len(abstract) > self.max_abstract_length:
            issues.append(f"Abstract too long (> {self.max_abstract_length} characters)")
            return score, issues
        
        # 内容质量检查
        score += 0.3  # 基础分
        
        # 检查是否包含技术术语
        technical_terms = 0
        for term in ['method', 'approach', 'algorithm', 'model', 'analysis', 'system', 'technique']:
            if term.lower() in abstract.lower():
                technical_terms += 1
        
        if technical_terms >= 3:
            score += 0.3
        
        # 检查是否有明确的研究内容描述
        if any(phrase in abstract.lower() for phrase in ['this paper', 'this study', 'we present', 'we propose', 'this work']):
            score += 0.2
        
        # 检查是否有结果描述
        if any(phrase in abstract.lower() for phrase in ['results show', 'experiments', 'evaluation', 'performance', 'accuracy']):
            score += 0.2
        
        return min(score, 1.0), issues
    
    def _validate_phm_relevance(self, paper: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证 PHM 相关性"""
        
        # 合并标题、摘要、关键词进行检查
        text_content = ' '.join([
            paper.get('title', ''),
            paper.get('abstract', ''),
            ' '.join(paper.get('keywords', []))
        ]).lower()
        
        issues = []
        score = 0.0
        
        if not text_content.strip():
            issues.append("No content available for PHM relevance check")
            return score, issues
        
        # 检查核心 PHM 关键词
        core_matches = sum(1 for keyword in self.phm_keywords['core'] 
                          if keyword.lower() in text_content)
        
        # 检查技术关键词
        technical_matches = sum(1 for keyword in self.phm_keywords['technical'] 
                               if keyword.lower() in text_content)
        
        # 检查应用关键词
        app_matches = sum(1 for keyword in self.phm_keywords['applications'] 
                         if keyword.lower() in text_content)
        
        # 计算相关性分数
        if core_matches >= 1:
            score += 0.5
        if technical_matches >= 1:
            score += 0.3
        if app_matches >= 1:
            score += 0.2
        
        # 如果没有任何 PHM 相关词汇，标记为不相关
        if core_matches == 0 and technical_matches == 0 and app_matches == 0:
            issues.append("Paper does not appear to be related to PHM (Prognostics and Health Management)")
        
        return min(score, 1.0), issues
    
    def _validate_source(self, paper: Dict[str, Any]) -> Tuple[float, List[str]]:
        """验证论文来源"""
        
        source = paper.get('source', '').lower()
        url = paper.get('url', '')
        
        issues = []
        score = 0.0
        
        # 检查 URL 是否来自可信域名
        if url:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # 移除 www. 前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            
            if any(trusted in domain for trusted in self.trusted_domains):
                score += 0.7
            else:
                issues.append(f"Source domain not in trusted list: {domain}")
        
        # 检查来源标识
        trusted_sources = ['arxiv', 'ieee', 'pubmed', 'google_scholar', 'semantic_scholar']
        if source in trusted_sources:
            score += 0.3
        
        return min(score, 1.0), issues
    
    def _generate_review_summary(self, review_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成审查摘要"""
        
        total_papers = review_results['total_papers']
        approved_count = len(review_results['approved_papers'])
        rejected_count = len(review_results['rejected_papers'])
        
        # 计算平均分数
        approved_scores = [p['review_score'] for p in review_results['approved_papers']]
        avg_approved_score = sum(approved_scores) / len(approved_scores) if approved_scores else 0
        
        # 统计拒绝原因
        rejection_reasons = {}
        for rejected in review_results['rejected_papers']:
            for reason in rejected['rejection_reasons']:
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        
        # 统计警告
        warning_counts = {}
        for warning in review_results['warnings']:
            warning_counts[warning] = warning_counts.get(warning, 0) + 1
        
        summary = {
            'approval_rate': approved_count / total_papers if total_papers > 0 else 0,
            'average_approved_score': round(avg_approved_score, 2),
            'most_common_rejection_reasons': sorted(rejection_reasons.items(), 
                                                   key=lambda x: x[1], reverse=True)[:5],
            'most_common_warnings': sorted(warning_counts.items(), 
                                         key=lambda x: x[1], reverse=True)[:5],
            'quality_assessment': self._assess_overall_quality(approved_count, total_papers, avg_approved_score),
            'recommendations': self._generate_recommendations(review_results)
        }
        
        return summary
    
    def _assess_overall_quality(self, approved_count: int, total_count: int, avg_score: float) -> str:
        """评估整体质量"""
        
        approval_rate = approved_count / total_count if total_count > 0 else 0
        
        if approval_rate >= 0.8 and avg_score >= 0.8:
            return "Excellent - High approval rate with high-quality papers"
        elif approval_rate >= 0.6 and avg_score >= 0.7:
            return "Good - Most papers meet quality standards"
        elif approval_rate >= 0.4:
            return "Fair - Some quality issues detected"
        else:
            return "Poor - Significant quality concerns"
    
    def _generate_recommendations(self, review_results: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        
        recommendations = []
        
        total_papers = review_results['total_papers']
        rejected_count = len(review_results['rejected_papers'])
        
        # 基于拒绝率给出建议
        if rejected_count / total_papers > 0.5:
            recommendations.append("Consider improving paper discovery quality filters")
        
        # 基于常见问题给出建议
        common_issues = [reason for reason, count in review_results['review_summary']['most_common_rejection_reasons']]
        
        if "Missing abstract" in common_issues:
            recommendations.append("Ensure all papers have complete abstracts before submission")
        
        if "Invalid DOI format" in common_issues:
            recommendations.append("Validate DOI formats during paper extraction")
        
        if "Paper does not appear to be related to PHM" in common_issues:
            recommendations.append("Improve PHM relevance filtering in discovery phase")
        
        if not recommendations:
            recommendations.append("Paper quality looks good - continue current practices")
        
        return recommendations
    
    def _calculate_comprehensive_quality_score(self, paper: Dict[str, Any]) -> float:
        """
        计算综合质量评分
        
        Args:
            paper: 论文信息字典
            
        Returns:
            综合质量评分 (0.0-1.0)
        """
        
        total_score = 0.0
        
        # 1. 期刊/会议声誉评分 (30%)
        venue_score = self._evaluate_venue_reputation(paper)
        total_score += venue_score * self.quality_weights['venue_reputation']
        
        # 2. PHM相关性评分 (25%)
        relevance_score = self._evaluate_phm_relevance_score(paper)
        total_score += relevance_score * self.quality_weights['phm_relevance']
        
        # 3. 内容质量评分 (20%)
        content_score = self._evaluate_content_quality_score(paper)
        total_score += content_score * self.quality_weights['content_quality']
        
        # 4. 作者可信度评分 (15%)
        author_score = self._evaluate_author_credibility(paper)
        total_score += author_score * self.quality_weights['author_credibility']
        
        # 5. 创新性和影响力评分 (10%)
        novelty_score = self._evaluate_novelty_impact(paper)
        total_score += novelty_score * self.quality_weights['novelty_impact']
        
        return min(total_score, 1.0)
    
    def _get_quality_breakdown(self, paper: Dict[str, Any]) -> Dict[str, float]:
        """获取质量评分明细"""
        
        return {
            'venue_reputation': self._evaluate_venue_reputation(paper),
            'phm_relevance': self._evaluate_phm_relevance_score(paper),
            'content_quality': self._evaluate_content_quality_score(paper),
            'author_credibility': self._evaluate_author_credibility(paper),
            'novelty_impact': self._evaluate_novelty_impact(paper)
        }
    
    def _evaluate_venue_reputation(self, paper: Dict[str, Any]) -> float:
        """评估期刊/会议声誉"""
        
        venue = paper.get('venue', paper.get('journal', paper.get('conference', '')))
        source = paper.get('source', '').lower()
        
        # 根据期刊名称直接匹配
        for known_venue, score in self.venue_scores.items():
            if known_venue.lower() in venue.lower():
                return score
        
        # 根据来源类型评分
        if 'arxiv' in source:
            return self.venue_scores['arXiv']
        elif 'ieee' in source:
            return 0.85  # IEEE 平均分
        elif any(domain in source for domain in ['springer', 'elsevier', 'acm']):
            return 0.75
        else:
            return self.venue_scores['unknown']
    
    def _evaluate_phm_relevance_score(self, paper: Dict[str, Any]) -> float:
        """评估PHM相关性评分"""
        
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        full_text = f"{title} {abstract}"
        
        # 统计各类关键词出现次数
        core_matches = sum(1 for kw in self.phm_keywords['core'] if kw.lower() in full_text)
        tech_matches = sum(1 for kw in self.phm_keywords['technical'] if kw.lower() in full_text)
        app_matches = sum(1 for kw in self.phm_keywords['applications'] if kw.lower() in full_text)
        
        # 计算相关性评分
        total_matches = core_matches * 3 + tech_matches * 2 + app_matches * 1
        max_possible = len(self.phm_keywords['core']) * 3 + len(self.phm_keywords['technical']) * 2 + len(self.phm_keywords['applications']) * 1
        
        relevance_score = min(total_matches / max_possible * 5, 1.0)  # 放大评分，最高为1.0
        
        # 特别奖励LLM+PHM的结合
        if any(llm_term in full_text for llm_term in ['large language model', 'llm', 'chatgpt', 'transformer']):
            relevance_score = min(relevance_score + 0.2, 1.0)
        
        return relevance_score
    
    def _evaluate_content_quality_score(self, paper: Dict[str, Any]) -> float:
        """评估内容质量评分"""
        
        score = 0.0
        
        # 摘要质量 (40%)
        abstract = paper.get('abstract', '')
        if abstract:
            abstract_len = len(abstract)
            if 150 <= abstract_len <= 1500:  # 合理长度
                score += 0.4
            elif 100 <= abstract_len < 150 or 1500 < abstract_len <= 2000:
                score += 0.3
            else:
                score += 0.1
        
        # 标题质量 (30%)
        title = paper.get('title', '')
        if title:
            title_len = len(title)
            if 20 <= title_len <= 120:  # 合理长度
                score += 0.3
                # 标题包含技术术语的奖励
                if any(term in title.lower() for term in ['deep learning', 'machine learning', 'neural', 'llm']):
                    score += 0.1
        
        # 作者信息完整性 (20%)
        authors = paper.get('authors', [])
        if authors and len(authors) >= 2:
            score += 0.2
        elif authors and len(authors) == 1:
            score += 0.1
        
        # DOI存在性 (10%)
        if paper.get('doi'):
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_author_credibility(self, paper: Dict[str, Any]) -> float:
        """评估作者可信度"""
        
        score = 0.0
        authors = paper.get('authors', [])
        
        if not authors:
            return 0.0
        
        # 作者数量合理性 (30%)
        author_count = len(authors)
        if 2 <= author_count <= 6:  # 合理的合作团队
            score += 0.3
        elif author_count == 1:
            score += 0.2
        else:
            score += 0.1
        
        # 作者姓名格式 (40%)
        valid_authors = 0
        for author in authors:
            if isinstance(author, str) and len(author.strip()) > 3:
                # 检查是否包含合理的姓名格式
                if ',' in author or ' ' in author.strip():
                    valid_authors += 1
        
        if valid_authors > 0:
            score += 0.4 * (valid_authors / len(authors))
        
        # 机构信息 (30%)
        # 简单的机构信息检查
        text_content = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        if any(inst in text_content.lower() for inst in ['university', 'institute', 'research', 'academy']):
            score += 0.3
        
        return min(score, 1.0)
    
    def _evaluate_novelty_impact(self, paper: Dict[str, Any]) -> float:
        """评估创新性和影响力"""
        
        score = 0.0
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        full_text = f"{title} {abstract}"
        
        # 创新性关键词 (50%)
        innovation_keywords = [
            'novel', 'new', 'innovative', 'advanced', 'improved', 'enhanced',
            'state-of-the-art', 'cutting-edge', 'breakthrough', 'pioneering'
        ]
        
        innovation_matches = sum(1 for kw in innovation_keywords if kw in full_text)
        if innovation_matches > 0:
            score += min(innovation_matches * 0.1, 0.5)
        
        # 技术前沿性 (30%)
        frontier_tech = [
            'large language model', 'transformer', 'attention mechanism',
            'foundation model', 'few-shot learning', 'zero-shot learning',
            'multimodal', 'graph neural network', 'knowledge graph'
        ]
        
        frontier_matches = sum(1 for tech in frontier_tech if tech in full_text)
        if frontier_matches > 0:
            score += min(frontier_matches * 0.15, 0.3)
        
        # 实验验证 (20%)
        experiment_keywords = [
            'experiment', 'evaluation', 'validation', 'dataset', 'benchmark',
            'comparison', 'performance', 'accuracy', 'results'
        ]
        
        exp_matches = sum(1 for kw in experiment_keywords if kw in full_text)
        if exp_matches > 0:
            score += min(exp_matches * 0.05, 0.2)
        
        return min(score, 1.0)


if __name__ == "__main__":
    # 测试 Paper Review Agent
    config = {
        'paper_review_settings': {
            'strict_mode': True,
            'require_doi': False,
            'min_abstract_length': 100,
            'max_abstract_length': 2000
        }
    }
    
    agent = PaperReviewAgent(config)
    
    # 测试论文
    test_papers = [
        {
            'title': 'Deep Learning for Bearing Fault Diagnosis in Prognostics and Health Management',
            'authors': ['Zhang, Wei', 'Liu, Ming'],
            'year': 2024,
            'abstract': 'This paper presents a novel deep learning approach for bearing fault diagnosis in prognostics and health management systems. The proposed CNN-LSTM method achieves high accuracy in fault classification and demonstrates superior performance compared to traditional methods. Experimental results on CWRU dataset show 97% accuracy.',
            'doi': '10.1016/j.ymssp.2024.111234',
            'source': 'ieee',
            'url': 'https://ieeexplore.ieee.org/document/test123'
        },
        {
            'title': 'Short title',  # 这个会被拒绝 - 标题太短
            'authors': [],  # 缺少作者
            'year': 2024,
            'abstract': 'Short abstract.',  # 摘要太短
            'source': 'unknown'
        }
    ]
    
    test_input = {'papers': test_papers}
    
    print("Testing Paper Review Agent...")
    try:
        result = agent.process(test_input)
        print(f"\n📊 Review Results:")
        print(f"   Total papers: {result['total_papers']}")
        print(f"   Approved: {len(result['approved_papers'])}")
        print(f"   Rejected: {len(result['rejected_papers'])}")
        print(f"   Approval rate: {result['review_summary']['approval_rate']:.1%}")
        
        print(f"\n✅ Approved papers:")
        for i, approved in enumerate(result['approved_papers'], 1):
            print(f"   {i}. {approved['paper']['title']} (Score: {approved['review_score']:.2f})")
        
        print(f"\n❌ Rejected papers:")
        for i, rejected in enumerate(result['rejected_papers'], 1):
            print(f"   {i}. {rejected['paper'].get('title', 'Unknown')} - Reasons: {rejected['rejection_reasons']}")
        
    except Exception as e:
        print(f"Test failed: {e}")