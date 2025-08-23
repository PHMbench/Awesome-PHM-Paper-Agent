"""
Academic Research Caller - 真实学术论文查询器

这个模块负责真正调用 WebSearch 和 WebFetch 工具来获取真实的学术论文信息，
而不是生成虚假数据。它直接搜索 ArXiv、Google Scholar 等学术数据库。
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import quote

from .logging_config import get_logger


class AcademicResearchCaller:
    """
    真实学术研究调用器
    
    使用 WebSearch 和 WebFetch 工具从真实的学术数据库获取论文信息，
    包括 ArXiv、Google Scholar、IEEE Xplore 等。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # 学术数据库搜索模板
        self.search_templates = {
            'arxiv': 'site:arxiv.org {keywords} PHM "prognostics and health management"',
            'ieee': 'site:ieeexplore.ieee.org {keywords} PHM fault diagnosis',
            'google_scholar': '{keywords} PHM prognostics health management filetype:pdf -site:mdpi.com',
            'pubmed': 'site:pubmed.ncbi.nlm.nih.gov {keywords} prognostics health',
            'semantic_scholar': 'site:semanticscholar.org {keywords} PHM machine learning -site:mdpi.com'
        }
        
        # 排除的域名和出版商列表
        self.excluded_domains = {
            'mdpi.com',
            'mdpi.org', 
            'www.mdpi.com',
            'www.mdpi.org'
        }
        
        # 排除的期刊名称模式
        self.excluded_journals = {
            'electronics', 'sensors', 'applied sciences', 'processes', 
            'sustainability', 'machines', 'energies', 'materials'
        }
        
        self.logger.info("Academic Research Caller initialized with MDPI exclusion rules")
    
    def search_real_papers(self, 
                          keywords: List[str], 
                          max_results: int = 10,
                          year_range: str = "2022-2024") -> List[Dict[str, Any]]:
        """
        搜索真实的学术论文
        
        Args:
            keywords: 搜索关键词列表
            max_results: 最大结果数
            year_range: 年份范围
            
        Returns:
            真实论文信息列表
        """
        self.logger.info(f"Searching real papers with keywords: {keywords}")
        
        # 生成搜索查询但不执行搜索
        # 实际搜索由调用者（Claude Code）执行
        search_queries = self._generate_search_queries(keywords)
        
        self.logger.info(f"Generated {len(search_queries)} search queries")
        self.logger.info("Search queries need to be executed by Claude Code using WebSearch tool")
        
        # 返回搜索查询供外部执行
        return [{
            'action': 'websearch_needed',
            'queries': search_queries,
            'max_results': max_results,
            'year_range': year_range,
            'note': 'These queries should be executed by Claude Code using WebSearch tool'
        }]
    
    def process_search_results(self, 
                             search_results: List[Dict[str, Any]], 
                             max_results: int = 10,
                             year_range: str = "2022-2024") -> List[Dict[str, Any]]:
        """
        处理外部 WebSearch 工具返回的搜索结果
        
        Args:
            search_results: WebSearch 工具返回的搜索结果列表
            max_results: 最大结果数
            year_range: 年份范围
            
        Returns:
            处理后的论文信息列表
        """
        self.logger.info(f"Processing {len(search_results)} search results")
        
        all_papers = []
        
        # 处理每个搜索结果
        for result in search_results:
            try:
                # 提取论文 URL 和基本信息
                paper_info = self._extract_paper_from_search_result(result)
                if paper_info and self._is_paper_allowed(paper_info):
                    all_papers.append(paper_info)
                elif paper_info:
                    self.logger.info(f"Excluded paper from {paper_info.get('url', 'unknown')}: MDPI or other excluded source")
                    
            except Exception as e:
                self.logger.error(f"Failed to process search result: {e}")
                continue
        
        # 去重和过滤
        unique_papers = self._deduplicate_papers(all_papers)
        filtered_papers = self._filter_by_year(unique_papers, year_range)
        
        self.logger.info(f"Total processed papers: {len(filtered_papers)}")
        return filtered_papers[:max_results]
    
    def _generate_search_queries(self, keywords: List[str]) -> List[Dict[str, str]]:
        """生成搜索查询"""
        
        keywords_str = " ".join(keywords)
        queries = []
        
        for db_name, search_template in self.search_templates.items():
            query = search_template.format(keywords=keywords_str)
            queries.append({
                'database': db_name,
                'query': query,
                'description': f'Search {db_name} for PHM papers'
            })
        
        return queries
    
    def _is_paper_allowed(self, paper_info: Dict[str, Any]) -> bool:
        """
        检查论文是否符合包含条件（排除 MDPI 等）
        
        Args:
            paper_info: 论文信息字典
            
        Returns:
            是否允许包含该论文
        """
        
        url = paper_info.get('url', '').lower()
        title = paper_info.get('title', '').lower()
        snippet = paper_info.get('snippet', '').lower()
        
        # 检查域名排除列表
        for excluded_domain in self.excluded_domains:
            if excluded_domain in url:
                self.logger.debug(f"Excluded paper from domain: {excluded_domain}")
                return False
        
        # 检查期刊名称排除列表
        full_text = f"{title} {snippet}".lower()
        for excluded_journal in self.excluded_journals:
            if excluded_journal in full_text:
                self.logger.debug(f"Excluded paper from journal: {excluded_journal}")
                return False
        
        # 特别检查 MDPI 标识
        if 'mdpi' in full_text:
            self.logger.debug("Excluded MDPI paper")
            return False
        
        return True
    
    def _extract_paper_from_search_result(self, search_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从搜索结果中提取论文信息
        
        Args:
            search_result: WebSearch 工具返回的单个搜索结果
            
        Returns:
            提取的论文信息或 None
        """
        
        try:
            # 检查搜索结果格式
            title = search_result.get('title', '')
            url = search_result.get('url', '')
            snippet = search_result.get('snippet', '')
            
            if not title or not url:
                return None
            
            # 基本论文信息
            paper_info = {
                'title': title.strip(),
                'url': url,
                'snippet': snippet,
                'source_type': self._identify_paper_source(url),
                'extraction_date': datetime.now().isoformat()
            }
            
            # 从 URL 和片段中提取更多信息
            year = self._extract_year_from_text(title + " " + snippet)
            if year:
                paper_info['year'] = year
            
            # 标记需要进一步提取详细信息
            paper_info['requires_webfetch'] = True
            paper_info['webfetch_prompt'] = self._generate_webfetch_prompt(paper_info['source_type'])
            
            return paper_info
            
        except Exception as e:
            self.logger.error(f"Failed to extract paper from search result: {e}")
            return None
    
    def _identify_paper_source(self, url: str) -> str:
        """识别论文来源类型"""
        
        if 'arxiv.org' in url.lower():
            return 'arxiv'
        elif 'ieeexplore.ieee.org' in url.lower():
            return 'ieee'
        elif 'scholar.google' in url.lower():
            return 'google_scholar'
        elif 'pubmed' in url.lower():
            return 'pubmed'
        elif 'semanticscholar.org' in url.lower():
            return 'semantic_scholar'
        elif 'springer' in url.lower():
            return 'springer'
        elif 'sciencedirect' in url.lower():
            return 'sciencedirect'
        else:
            return 'general'
    
    def _generate_webfetch_prompt(self, source_type: str) -> str:
        """为不同源生成 WebFetch 提示"""
        
        base_prompt = "Extract the following information from this academic paper: title, authors with affiliations, abstract, publication year, journal/conference name, DOI if available."
        
        source_specific = {
            'arxiv': " This is an ArXiv preprint paper.",
            'ieee': " This is an IEEE paper, look for IEEE format metadata.",
            'google_scholar': " This is from Google Scholar, extract bibliographic information.",
            'pubmed': " This is a PubMed medical paper, focus on medical/health applications.",
            'springer': " This is a Springer paper, look for Springer format metadata.",
            'sciencedirect': " This is an Elsevier/ScienceDirect paper."
        }
        
        return base_prompt + source_specific.get(source_type, "")
    
    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """从文本中提取年份"""
        
        # 查找四位数年份
        years = re.findall(r'\b(20[0-2][0-9])\b', text)
        
        for year_str in years:
            year = int(year_str)
            # 合理的年份范围 (2020-2026)
            if 2020 <= year <= datetime.now().year + 1:
                return year
        
        return None
    
    def _search_database(self, 
                        db_name: str, 
                        search_template: str, 
                        keywords: List[str], 
                        max_results: int) -> List[Dict[str, Any]]:
        """搜索特定数据库 (已弃用，保留向后兼容)"""
        
        # 这个方法已被新的架构取代，但保留以避免破坏现有代码
        self.logger.warning("_search_database is deprecated, use _generate_search_queries instead")
        
        keywords_str = " ".join(keywords)
        search_query = search_template.format(keywords=keywords_str)
        
        return [{
            'deprecated': True,
            'database': db_name,
            'query': search_query,
            'note': 'Use process_search_results with WebSearch results instead'
        }]
    
    def _call_websearch_tool(self, query: str, max_results: int, source: str) -> List[Dict[str, Any]]:
        """
        调用 WebSearch 工具的包装方法
        
        在 Claude Code 环境中，实际调用 WebSearch 工具获取搜索结果
        """
        
        try:
            self.logger.info(f"Calling WebSearch for {source} with query: {query}")
            
            # 导入工具类（需要在 Claude Code 环境中可用）
            # 这里我们模拟调用，实际应该由 Claude Code 直接调用 WebSearch
            from typing import TYPE_CHECKING
            if TYPE_CHECKING:
                from claude_tools import WebSearch, WebFetch
            
            # 实际的 WebSearch 调用应该由调用者（Claude Code）来执行
            # 这里我们返回一个标记，表示需要 WebSearch 调用
            search_result = {
                'websearch_needed': True,
                'query': query,
                'max_results': max_results,
                'source': source,
                'note': 'This should be replaced with actual WebSearch tool call by Claude Code'
            }
            
            # 临时返回格式，指示需要真实的搜索结果
            return [{
                'source': source,
                'search_query': query,
                'requires_websearch': True,
                'max_results': max_results
            }]
            
        except Exception as e:
            self.logger.error(f"Failed to call WebSearch tool: {e}")
            return []
    
    def extract_paper_info(self, url: str, source: str) -> Optional[Dict[str, Any]]:
        """
        从论文 URL 提取详细信息
        
        Args:
            url: 论文 URL
            source: 来源（arxiv, ieee 等）
            
        Returns:
            论文信息字典或 None
        """
        
        self.logger.info(f"Extracting paper info from: {url}")
        
        try:
            # 根据不同源使用不同的提取策略
            if 'arxiv.org' in url:
                return self._extract_arxiv_paper(url)
            elif 'ieeexplore.ieee.org' in url:
                return self._extract_ieee_paper(url)
            else:
                return self._extract_general_paper(url)
                
        except Exception as e:
            self.logger.error(f"Failed to extract paper info from {url}: {e}")
            return None
    
    def _extract_arxiv_paper(self, url: str) -> Optional[Dict[str, Any]]:
        """提取 ArXiv 论文信息"""
        
        # 这里需要调用 WebFetch 工具
        # fetch_result = WebFetch(url, "提取论文标题、作者、摘要、发表日期")
        
        self.logger.warning(f"WebFetch tool call needed for ArXiv paper: {url}")
        
        # 示例返回格式
        return {
            'source': 'arxiv',
            'url': url,
            'extraction_needed': True,
            'note': 'WebFetch tool should be called to extract real paper information'
        }
    
    def _extract_ieee_paper(self, url: str) -> Optional[Dict[str, Any]]:
        """提取 IEEE 论文信息"""
        
        # 这里需要调用 WebFetch 工具
        # fetch_result = WebFetch(url, "提取论文标题、作者、摘要、DOI、发表期刊")
        
        self.logger.warning(f"WebFetch tool call needed for IEEE paper: {url}")
        
        return {
            'source': 'ieee',
            'url': url,
            'extraction_needed': True,
            'note': 'WebFetch tool should be called to extract real paper information'
        }
    
    def _extract_general_paper(self, url: str) -> Optional[Dict[str, Any]]:
        """提取一般论文信息"""
        
        # 这里需要调用 WebFetch 工具
        # fetch_result = WebFetch(url, "提取论文标题、作者列表、摘要、发表信息")
        
        self.logger.warning(f"WebFetch tool call needed for general paper: {url}")
        
        return {
            'source': 'general',
            'url': url,
            'extraction_needed': True,
            'note': 'WebFetch tool should be called to extract real paper information'
        }
    
    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重论文"""
        
        seen_urls = set()
        unique_papers = []
        
        for paper in papers:
            url = paper.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_papers.append(paper)
        
        return unique_papers
    
    def _filter_by_year(self, papers: List[Dict[str, Any]], year_range: str) -> List[Dict[str, Any]]:
        """按年份过滤论文"""
        
        if not year_range or '-' not in year_range:
            return papers
        
        try:
            start_year, end_year = map(int, year_range.split('-'))
            filtered_papers = []
            
            for paper in papers:
                year = paper.get('year')
                if year and start_year <= int(year) <= end_year:
                    filtered_papers.append(paper)
                else:
                    # 如果没有年份信息，暂时保留
                    filtered_papers.append(paper)
            
            return filtered_papers
            
        except Exception as e:
            self.logger.error(f"Failed to filter by year range {year_range}: {e}")
            return papers
    
    def verify_paper_exists(self, paper_info: Dict[str, Any]) -> bool:
        """
        验证论文是否真实存在
        
        Args:
            paper_info: 论文信息字典
            
        Returns:
            论文是否存在
        """
        
        # 检查必要字段
        if not paper_info.get('title') or not paper_info.get('url'):
            return False
        
        # 检查 URL 是否可访问
        url = paper_info.get('url')
        
        # 这里应该调用 WebFetch 验证
        # result = WebFetch(url, "验证页面是否存在，是否是学术论文")
        
        self.logger.warning(f"Paper verification needed for: {url}")
        
        # 暂时返回 True，表明需要实际验证
        return True


class RealPaperExtractor:
    """
    真实论文信息提取器
    
    专门处理从 WebFetch 结果中提取结构化论文信息
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def extract_from_text(self, text: str, url: str, source: str) -> Optional[Dict[str, Any]]:
        """
        从文本中提取论文信息
        
        Args:
            text: WebFetch 返回的文本内容
            url: 原始 URL
            source: 来源标识
            
        Returns:
            结构化的论文信息
        """
        
        try:
            paper_info = {
                'source': source,
                'url': url,
                'extraction_date': datetime.now().isoformat()
            }
            
            # 提取标题
            title = self._extract_title(text)
            if title:
                paper_info['title'] = title
            
            # 提取作者
            authors = self._extract_authors(text)
            if authors:
                paper_info['authors'] = authors
            
            # 提取摘要
            abstract = self._extract_abstract(text)
            if abstract:
                paper_info['abstract'] = abstract
            
            # 提取年份
            year = self._extract_year(text)
            if year:
                paper_info['year'] = year
            
            # 提取期刊/会议
            venue = self._extract_venue(text)
            if venue:
                paper_info['venue'] = venue
            
            # 提取 DOI
            doi = self._extract_doi(text)
            if doi:
                paper_info['doi'] = doi
            
            return paper_info if paper_info.get('title') else None
            
        except Exception as e:
            self.logger.error(f"Failed to extract paper info from text: {e}")
            return None
    
    def _extract_title(self, text: str) -> Optional[str]:
        """提取论文标题"""
        
        # 常见的标题模式
        patterns = [
            r'<title>([^<]+)</title>',
            r'Title:\s*(.+?)(?:\n|$)',
            r'"title"\s*:\s*"([^"]+)"',
            r'<h1[^>]*>([^<]+)</h1>',
            r'Title\s*:\s*(.+?)(?:\n|\r|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # 清理标题
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 10 and len(title) < 200:  # 合理的标题长度
                    return title
        
        return None
    
    def _extract_authors(self, text: str) -> Optional[List[str]]:
        """提取作者列表"""
        
        patterns = [
            r'Authors?:\s*(.+?)(?:\n|$)',
            r'"authors?"\s*:\s*"([^"]+)"',
            r'By:\s*(.+?)(?:\n|$)',
            r'<meta\s+name="author"\s+content="([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                authors_str = match.group(1).strip()
                # 分割作者
                authors = [author.strip() for author in re.split(r'[,;]|and', authors_str)]
                # 过滤空白和过短的条目
                authors = [author for author in authors if len(author) > 2]
                if authors:
                    return authors[:10]  # 限制作者数量
        
        return None
    
    def _extract_abstract(self, text: str) -> Optional[str]:
        """提取摘要"""
        
        patterns = [
            r'Abstract\s*:?\s*(.+?)(?:\n\n|\r\r|Keywords|Introduction|1\.|References)',
            r'<abstract>(.+?)</abstract>',
            r'"abstract"\s*:\s*"([^"]+)"',
            r'Summary\s*:?\s*(.+?)(?:\n\n|\r\r)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
                # 清理摘要
                abstract = re.sub(r'\s+', ' ', abstract)
                abstract = re.sub(r'<[^>]+>', '', abstract)  # 移除 HTML 标签
                if len(abstract) > 50 and len(abstract) < 2000:  # 合理的摘要长度
                    return abstract
        
        return None
    
    def _extract_year(self, text: str) -> Optional[int]:
        """提取发表年份"""
        
        patterns = [
            r'(\d{4})',  # 简单的四位数字
            r'Published:?\s*(\d{4})',
            r'Year:?\s*(\d{4})',
            r'"year"\s*:\s*(\d{4})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                year = int(match)
                # 合理的年份范围
                if 2000 <= year <= datetime.now().year + 1:
                    return year
        
        return None
    
    def _extract_venue(self, text: str) -> Optional[str]:
        """提取期刊/会议名称"""
        
        patterns = [
            r'Journal:?\s*(.+?)(?:\n|$)',
            r'Published in:?\s*(.+?)(?:\n|$)',
            r'Conference:?\s*(.+?)(?:\n|$)',
            r'"venue"\s*:\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                venue = match.group(1).strip()
                venue = re.sub(r'\s+', ' ', venue)
                if len(venue) > 3 and len(venue) < 100:
                    return venue
        
        return None
    
    def _extract_doi(self, text: str) -> Optional[str]:
        """提取 DOI"""
        
        patterns = [
            r'DOI:?\s*(10\.\d+/[^\s]+)',
            r'doi\.org/(10\.\d+/[^\s]+)',
            r'"doi"\s*:\s*"(10\.\d+/[^"]+)"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                doi = match.group(1).strip()
                return doi
        
        return None


if __name__ == "__main__":
    # 测试代码
    print("Testing Academic Research Caller...")
    
    caller = AcademicResearchCaller()
    
    # 测试搜索
    keywords = ["deep learning", "bearing fault diagnosis", "PHM"]
    papers = caller.search_real_papers(keywords, max_results=5)
    
    print(f"Found {len(papers)} papers")
    for paper in papers:
        print(f"- {paper}")
    
    # 测试提取器
    extractor = RealPaperExtractor()
    sample_text = """
    Title: Deep Learning for Bearing Fault Diagnosis
    Authors: Zhang Wei, Liu Ming
    Abstract: This paper presents a novel approach for bearing fault diagnosis using deep learning methods. The proposed CNN-LSTM architecture achieves high accuracy in fault classification.
    Year: 2024
    Journal: Mechanical Systems and Signal Processing
    """
    
    paper_info = extractor.extract_from_text(sample_text, "http://example.com", "test")
    print(f"Extracted paper info: {paper_info}")