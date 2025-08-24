#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Elsevier ScienceDirect API客户端
Elsevier ScienceDirect API Client

提供Elsevier ScienceDirect API的完整接入功能，支持：
- 论文搜索和检索
- 元数据提取
- 引用数据获取
- 质量指标评估
"""

import requests
import json
import time
from typing import Dict, List, Any, Optional, Union
from urllib.parse import quote
from datetime import datetime

from .logging_config import get_logger
from .config import load_config


class ElsevierAPIError(Exception):
    """Elsevier API专用异常"""
    pass


class ElsevierClient:
    """
    Elsevier ScienceDirect API客户端
    
    提供对Elsevier ScienceDirect数据库的程序化访问，
    支持论文搜索、元数据提取和质量评估。
    """
    
    def __init__(self, config_path: str = "config.yaml", debug: bool = False):
        """
        初始化Elsevier客户端
        
        Args:
            config_path: 配置文件路径
            debug: 是否启用调试模式
        """
        self.config = load_config(config_path)
        self.debug = debug
        self.logger = get_logger(__name__)
        
        # Elsevier配置
        elsevier_config = self.config.get('data_sources', {}).get('elsevier', {})
        self.api_key = elsevier_config.get('api_key', '')
        self.base_url = elsevier_config.get('base_url', 'https://api.elsevier.com')
        self.enabled = elsevier_config.get('enabled', False) and bool(self.api_key)
        
        if not self.enabled:
            self.logger.warning("Elsevier API未启用或API密钥未配置")
            if debug:
                print("⚠️ Elsevier API未启用。请在config.yaml中配置API密钥。")
                print("   获取API密钥: https://dev.elsevier.com/apikey/create")
        
        # API设置
        self.settings = elsevier_config.get('settings', {})
        self.search_filters = elsevier_config.get('search_filters', {})
        
        # 速率限制配置
        api_config = self.config.get('api_configuration', {})
        self.rate_limit = api_config.get('rate_limits', {}).get('elsevier', 2)  # 2 req/sec
        self.timeout = api_config.get('timeout_seconds', 30)
        self.max_retries = api_config.get('max_retries', 3)
        self.retry_delay = api_config.get('retry_delay', 2)
        
        # 请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'X-ELS-APIKey': self.api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'User-Agent': api_config.get('user_agent', 'APPA/1.0')
        })
        
        # 速率控制
        self._last_request_time = 0
        self._request_interval = 1.0 / self.rate_limit if self.rate_limit > 0 else 0
        
        if debug and self.enabled:
            print(f"✅ Elsevier API客户端初始化成功")
            print(f"   Base URL: {self.base_url}")
            print(f"   Rate Limit: {self.rate_limit} req/sec")
    
    def _rate_limit_wait(self):
        """执行速率限制等待"""
        if self._request_interval > 0:
            time_since_last = time.time() - self._last_request_time
            if time_since_last < self._request_interval:
                sleep_time = self._request_interval - time_since_last
                time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            Dict: API响应数据
            
        Raises:
            ElsevierAPIError: API请求失败
        """
        if not self.enabled:
            raise ElsevierAPIError("Elsevier API未启用或API密钥未配置")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = params or {}
        
        for attempt in range(self.max_retries + 1):
            try:
                # 速率限制
                self._rate_limit_wait()
                
                if self.debug:
                    print(f"🔍 请求Elsevier API: {url}")
                    print(f"   参数: {params}")
                
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                # 检查响应状态
                if response.status_code == 200:
                    data = response.json()
                    if self.debug:
                        print(f"✅ API请求成功: {response.status_code}")
                    return data
                
                elif response.status_code == 401:
                    raise ElsevierAPIError(f"API密钥无效或已过期: {response.status_code}")
                
                elif response.status_code == 403:
                    raise ElsevierAPIError(f"访问被拒绝，检查权限: {response.status_code}")
                
                elif response.status_code == 429:
                    # 速率限制，等待更长时间
                    wait_time = self.retry_delay * (2 ** attempt)
                    self.logger.warning(f"速率限制，等待 {wait_time} 秒")
                    if attempt < self.max_retries:
                        time.sleep(wait_time)
                        continue
                    else:
                        raise ElsevierAPIError(f"超出速率限制: {response.status_code}")
                
                else:
                    self.logger.warning(f"API请求失败: {response.status_code}")
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise ElsevierAPIError(f"API请求失败: {response.status_code}")
                
            except requests.RequestException as e:
                self.logger.error(f"网络请求错误: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    raise ElsevierAPIError(f"网络请求失败: {e}")
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        if not self.enabled:
            return False
        
        try:
            # 使用简单的搜索测试连接
            result = self._make_request('/content/search/sciencedirect', {
                'query': 'prognostics',
                'count': 1
            })
            return 'search-results' in result
        
        except Exception as e:
            self.logger.error(f"Elsevier API连接测试失败: {e}")
            return False
    
    def search_papers(self, 
                     query: str,
                     max_results: int = 25,
                     year_range: Optional[tuple] = None,
                     subject_areas: Optional[List[str]] = None,
                     content_types: Optional[List[str]] = None,
                     open_access_only: bool = False) -> List[Dict[str, Any]]:
        """
        搜索论文
        
        Args:
            query: 搜索查询
            max_results: 最大结果数
            year_range: 年份范围 (start_year, end_year)
            subject_areas: 学科领域过滤
            content_types: 内容类型过滤
            open_access_only: 仅开放获取论文
            
        Returns:
            List[Dict]: 论文列表
        """
        if not self.enabled:
            self.logger.warning("Elsevier API未启用，跳过搜索")
            return []
        
        self.logger.info(f"搜索Elsevier论文: '{query}' (最大 {max_results} 篇)")
        
        # 构建搜索参数
        params = {
            'query': query,
            'count': min(max_results, self.settings.get('max_results_per_request', 100)),
            'start': 0
        }
        
        # 添加过滤条件
        filters = []
        
        # 年份过滤
        if year_range:
            start_year, end_year = year_range
            filters.append(f'pub-date > {start_year - 1} AND pub-date < {end_year + 1}')
        
        # 学科领域过滤
        if subject_areas or self.search_filters.get('subject_areas'):
            areas = subject_areas or self.search_filters.get('subject_areas', [])
            area_filter = ' OR '.join([f'SUBJAREA({area})' for area in areas])
            filters.append(f'({area_filter})')
        
        # 内容类型过滤
        if content_types or self.search_filters.get('content_types'):
            types = content_types or self.search_filters.get('content_types', [])
            if 'journal' in types:
                filters.append('SRCTYPE(j)')
        
        # 开放获取过滤
        if open_access_only or self.search_filters.get('open_access_only', False):
            filters.append('OPENACCESS(1)')
        
        # 应用过滤条件
        if filters:
            params['query'] += ' AND ' + ' AND '.join(filters)
        
        papers = []
        processed_results = 0
        
        try:
            while processed_results < max_results:
                # 更新起始位置
                params['start'] = processed_results
                params['count'] = min(100, max_results - processed_results)
                
                # 发送请求
                response = self._make_request('/content/search/sciencedirect', params)
                
                # 解析结果
                search_results = response.get('search-results', {})
                entries = search_results.get('entry', [])
                
                if not entries:
                    break
                
                # 处理每个结果
                for entry in entries:
                    if len(papers) >= max_results:
                        break
                    
                    paper = self._parse_paper_entry(entry)
                    if paper:
                        papers.append(paper)
                
                processed_results += len(entries)
                
                # 检查是否有更多结果
                total_results = int(search_results.get('opensearch:totalResults', 0))
                if processed_results >= total_results:
                    break
        
        except Exception as e:
            self.logger.error(f"Elsevier搜索失败: {e}")
            raise ElsevierAPIError(f"搜索失败: {e}")
        
        self.logger.info(f"Elsevier搜索完成: 找到 {len(papers)} 篇论文")
        return papers
    
    def _parse_paper_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析论文条目
        
        Args:
            entry: Elsevier API返回的论文条目
            
        Returns:
            Dict: 标准化的论文信息，如果解析失败返回None
        """
        try:
            # 提取基本信息
            title = entry.get('dc:title', '')
            if not title:
                return None
            
            # DOI信息
            doi = ''
            identifier = entry.get('dc:identifier', '')
            if identifier and identifier.startswith('DOI:'):
                doi = identifier.replace('DOI:', '')
            
            # 作者信息
            authors = []
            creator_info = entry.get('dc:creator', '')
            if creator_info:
                # 解析作者字符串 "Author1; Author2; Author3"
                author_parts = creator_info.split(';')
                for author in author_parts:
                    author = author.strip()
                    if author:
                        authors.append(author)
            
            # 期刊信息
            venue = entry.get('prism:publicationName', '')
            
            # 发表年份
            year = None
            cover_date = entry.get('prism:coverDate', '')
            if cover_date:
                try:
                    year = int(cover_date.split('-')[0])
                except ValueError:
                    pass
            
            # URL信息
            urls = {}
            links = entry.get('link', [])
            if isinstance(links, list):
                for link in links:
                    if isinstance(link, dict):
                        rel = link.get('@rel', '')
                        href = link.get('@href', '')
                        if rel == 'scidir' and href:
                            urls['sciencedirect'] = href
                        elif rel == 'self' and href:
                            urls['api'] = href
            
            # 摘要（如果可用）
            abstract = entry.get('dc:description', '')
            
            # 引用次数（如果可用）
            citations = 0
            cited_by = entry.get('citedby-count', '0')
            if cited_by and cited_by.isdigit():
                citations = int(cited_by)
            
            # 构建论文对象
            paper = {
                'id': self._generate_paper_id(title, authors, year),
                'title': title,
                'authors': authors,
                'year': year or datetime.now().year,
                'venue': venue,
                'venue_type': 'journal',  # Elsevier主要是期刊
                'doi': doi,
                'abstract': abstract,
                'urls': urls,
                'quality_indicators': {
                    'citations': citations,
                    'peer_reviewed': True,  # Elsevier期刊都是同行评审
                    'publisher': 'Elsevier',
                    'source': 'ScienceDirect'
                },
                'source_info': {
                    'database': 'Elsevier ScienceDirect',
                    'retrieved_at': datetime.now().isoformat(),
                    'api_entry': entry
                }
            }
            
            # PHM相关性评估
            paper['phm_relevance_score'] = self._assess_phm_relevance(paper)
            
            return paper
        
        except Exception as e:
            self.logger.error(f"解析Elsevier论文条目失败: {e}")
            return None
    
    def _generate_paper_id(self, title: str, authors: List[str], year: Optional[int]) -> str:
        """生成论文ID"""
        # 获取第一作者姓氏
        first_author = "Unknown"
        if authors:
            author_parts = authors[0].split(',')
            if author_parts:
                first_author = author_parts[0].strip()
        
        # 获取标题关键词
        title_words = title.lower().split()
        key_words = [w for w in title_words if len(w) > 3 and w.isalpha()][:2]
        title_part = '-'.join(key_words) if key_words else 'Paper'
        
        # 生成ID
        year_str = str(year) if year else str(datetime.now().year)
        paper_id = f"{year_str}-Elsevier-{first_author}-{title_part}"
        
        # 清理无效字符
        import re
        paper_id = re.sub(r'[^\w\-]', '', paper_id)
        
        return paper_id
    
    def _assess_phm_relevance(self, paper: Dict[str, Any]) -> float:
        """
        评估论文的PHM相关性
        
        Args:
            paper: 论文信息
            
        Returns:
            float: 相关性得分 (0.0-1.0)
        """
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        venue = paper.get('venue', '').lower()
        
        text_content = f"{title} {abstract} {venue}"
        
        # PHM关键词权重
        phm_keywords = {
            # 核心概念 (高权重)
            'prognostics': 1.0,
            'health management': 1.0,
            'fault diagnosis': 0.9,
            'predictive maintenance': 0.9,
            'remaining useful life': 1.0,
            'rul': 0.9,
            'condition monitoring': 0.8,
            'health monitoring': 0.8,
            
            # 技术方法 (中等权重)
            'anomaly detection': 0.7,
            'failure prediction': 0.8,
            'degradation modeling': 0.7,
            'system reliability': 0.6,
            'sensor fusion': 0.6,
            
            # 应用领域 (中等权重)
            'bearing fault': 0.8,
            'gear fault': 0.7,
            'motor fault': 0.7,
            'turbine monitoring': 0.7,
            'machinery health': 0.8,
            
            # 相关概念 (低权重)
            'machine learning': 0.4,
            'deep learning': 0.5,
            'artificial intelligence': 0.4,
            'signal processing': 0.5
        }
        
        # 计算加权相关性分数
        total_score = 0.0
        max_possible_score = 0.0
        
        for keyword, weight in phm_keywords.items():
            if keyword in text_content:
                total_score += weight
            max_possible_score += weight
        
        # 标准化到0-1范围
        if max_possible_score > 0:
            relevance_score = min(total_score / max_possible_score * 2, 1.0)
        else:
            relevance_score = 0.0
        
        return round(relevance_score, 2)
    
    def get_article_details(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        获取文章详细信息
        
        Args:
            doi: 文章DOI
            
        Returns:
            Dict: 详细的文章信息
        """
        if not self.enabled or not doi:
            return None
        
        try:
            # 使用Article Retrieval API获取详细信息
            endpoint = f'/content/article/doi/{doi}'
            response = self._make_request(endpoint)
            
            # 解析响应
            if 'full-text-retrieval-response' in response:
                article_data = response['full-text-retrieval-response']
                return self._parse_article_details(article_data)
            
            return None
        
        except Exception as e:
            self.logger.error(f"获取文章详情失败 (DOI: {doi}): {e}")
            return None
    
    def _parse_article_details(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析文章详细信息"""
        try:
            core_data = article_data.get('coredata', {})
            
            return {
                'title': core_data.get('dc:title', ''),
                'abstract': core_data.get('dc:description', ''),
                'keywords': core_data.get('dc:subject', []),
                'doi': core_data.get('prism:doi', ''),
                'publication_name': core_data.get('prism:publicationName', ''),
                'cover_date': core_data.get('prism:coverDate', ''),
                'page_range': core_data.get('prism:pageRange', ''),
                'volume': core_data.get('prism:volume', ''),
                'issue': core_data.get('prism:issueIdentifier', ''),
                'cited_by_count': int(core_data.get('citedby-count', 0)),
                'source_url': core_data.get('link', [{}])[0].get('@href', '')
            }
        
        except Exception as e:
            self.logger.error(f"解析文章详情失败: {e}")
            return {}
    
    def get_api_usage_stats(self) -> Dict[str, Any]:
        """
        获取API使用统计（如果支持）
        
        Returns:
            Dict: API使用统计信息
        """
        # Elsevier API通常不提供使用统计，这里返回基本信息
        return {
            'api_enabled': self.enabled,
            'api_key_configured': bool(self.api_key),
            'rate_limit': self.rate_limit,
            'base_url': self.base_url,
            'last_request_time': self._last_request_time
        }


def main():
    """测试用例"""
    import sys
    
    # 创建客户端
    client = ElsevierClient(debug=True)
    
    # 测试连接
    print("🔍 测试Elsevier API连接...")
    if client.test_connection():
        print("✅ API连接成功！")
        
        # 测试搜索
        print("\n🔍 测试论文搜索...")
        papers = client.search_papers(
            query="prognostics health management",
            max_results=5
        )
        
        print(f"✅ 搜索完成: 找到 {len(papers)} 篇论文")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper['title'][:60]}...")
            print(f"   作者: {', '.join(paper['authors'][:2])}{'...' if len(paper['authors']) > 2 else ''}")
            print(f"   期刊: {paper['venue']}")
            print(f"   年份: {paper['year']}")
            print(f"   PHM相关性: {paper['phm_relevance_score']}")
    
    else:
        print("❌ API连接失败")
        print("请检查:")
        print("1. config.yaml中的API密钥配置")
        print("2. 网络连接")
        print("3. API密钥是否有效")
        
        # 显示配置信息
        stats = client.get_api_usage_stats()
        print(f"\n配置状态:")
        for key, value in stats.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    main()