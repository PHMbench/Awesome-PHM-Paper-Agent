"""
Crossref API Client for APPA System

Crossref provides comprehensive DOI-based metadata for scholarly publications.
Excellent for accessing journal articles with strong DOI consistency.
Some records include abstracts.

Documentation: https://api.crossref.org/
No authentication required, but custom User-Agent recommended.
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .logging_config import get_logger
from .paper_quality_filter import PaperQualityFilter


class CrossrefClient:
    """
    Crossref API client for DOI-based paper discovery and metadata retrieval.
    
    Features:
    - Free access (no API key required)
    - Strong DOI consistency and metadata quality
    - Journal and publisher filtering
    - Some abstracts available
    - Rate limiting with polite requests
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # API Configuration
        self.base_url = "https://api.crossref.org"
        self.user_agent = os.environ.get(
            'CROSSREF_USER_AGENT',
            'APPA/1.0 (Awesome-PHM-Paper-Agent; academic-research)'
        )
        self.rate_limit = 5  # requests per second (be polite)
        
        # Request headers
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json'
        }
        
        # Quality filter
        self.quality_filter = PaperQualityFilter(config)
        
        # PHM-specific search terms
        self.phm_search_terms = [
            'prognostics', 'health management', 'condition monitoring',
            'predictive maintenance', 'fault diagnosis', 'anomaly detection',
            'remaining useful life', 'RUL', 'degradation modeling',
            'failure prediction', 'reliability', 'digital twin'
        ]
        
        # High-quality PHM journals (with approximate impact factors)
        self.target_journals = {
            'Mechanical Systems and Signal Processing': {'if': 8.4, 'q': 'Q1'},
            'Reliability Engineering & System Safety': {'if': 7.6, 'q': 'Q1'},
            'IEEE Transactions on Reliability': {'if': 5.9, 'q': 'Q1'},
            'IEEE Transactions on Industrial Electronics': {'if': 8.2, 'q': 'Q1'},
            'IEEE Transactions on Instrumentation and Measurement': {'if': 5.6, 'q': 'Q1'},
            'Journal of Sound and Vibration': {'if': 4.7, 'q': 'Q1'},
            'Expert Systems with Applications': {'if': 8.5, 'q': 'Q1'},
            'Engineering Applications of Artificial Intelligence': {'if': 8.0, 'q': 'Q1'},
            'Computers & Industrial Engineering': {'if': 7.9, 'q': 'Q1'},
            'ISA Transactions': {'if': 7.3, 'q': 'Q1'},
            'Sensors': {'if': 3.9, 'q': 'Q2'},  # Note: This is MDPI, usually filtered
            'Applied Sciences': {'if': 2.8, 'q': 'Q2'}  # Note: This is MDPI, usually filtered
        }
        
        # Publishers to exclude (MDPI, predatory)
        self.excluded_publishers = {
            'mdpi', 'mdpi ag', 'multidisciplinary digital publishing institute',
            'scirp', 'scientific research publishing', 'hindawi limited',
            'bentham science', 'omics international', 'frontiers media'
        }
        
        self.logger.info("Crossref client initialized")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make rate-limited request to Crossref API."""
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            # Rate limiting - be polite to Crossref
            time.sleep(1.0 / self.rate_limit)
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Crossref API request failed: {e}")
            return None
    
    def search_papers(self,
                     query: str,
                     filters: Optional[Dict[str, Any]] = None,
                     max_results: int = 50,
                     year_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
        """
        Search for PHM papers in Crossref.
        
        Args:
            query: Search query string
            filters: Additional filters (journal, publisher, etc.)
            max_results: Maximum number of results
            year_range: Tuple of (start_year, end_year)
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Searching Crossref for: {query}")
        
        # Build search parameters
        params = {
            'query': query,
            'rows': min(max_results, 1000),  # Crossref allows up to 1000
            'sort': 'score',  # Relevance by default
            'order': 'desc',
            'select': ','.join([
                'DOI', 'title', 'author', 'published-print', 'published-online',
                'container-title', 'publisher', 'abstract', 'subject',
                'is-referenced-by-count', 'type', 'ISSN', 'ISBN',
                'journal-issue', 'page', 'volume', 'issue'
            ])
        }
        
        # Build filter string
        filter_parts = []
        
        # Year range filter
        if year_range:
            start_year, end_year = year_range
            filter_parts.append(f'from-pub-date:{start_year}')
            filter_parts.append(f'until-pub-date:{end_year}')
        
        # Content type filter (only journal articles and conference papers)
        filter_parts.append('type:journal-article')
        
        # Apply additional filters
        if filters:
            # Journal filter
            if 'journals' in filters:
                for journal in filters['journals']:
                    # Note: Crossref uses exact match for container-title
                    params['query.container-title'] = journal
                    break  # Can only filter by one journal at a time
            
            # Publisher filter (exclusions)
            if 'exclude_publishers' in filters:
                # Crossref doesn't support negative filtering directly
                # We'll filter in post-processing
                pass
        
        # Apply filters
        if filter_parts:
            params['filter'] = ','.join(filter_parts)
        
        # Make request
        response_data = self._make_request('works', params)
        if not response_data:
            return []
        
        papers = []
        items = response_data.get('message', {}).get('items', [])
        
        for work in items:
            try:
                paper = self._convert_work_to_paper(work)
                if paper and self._is_phm_relevant(paper) and not self._is_excluded_publisher(paper):
                    papers.append(paper)
                    
            except Exception as e:
                self.logger.warning(f"Failed to process Crossref work: {e}")
                continue
        
        # Apply quality filters and sort
        filtered_papers = self._apply_quality_filters(papers)
        filtered_papers.sort(key=lambda x: x.get('cited_by_count', 0), reverse=True)
        
        self.logger.info(f"Found {len(filtered_papers)} PHM-relevant papers from Crossref")
        return filtered_papers[:max_results]
    
    def _convert_work_to_paper(self, work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Crossref work object to standard paper format."""
        
        try:
            # Basic metadata
            paper = {
                'doi': work.get('DOI', ''),
                'title': self._extract_title(work.get('title', [])),
                'cited_by_count': work.get('is-referenced-by-count', 0),
                'source': 'crossref'
            }
            
            # Authors
            authors = []
            for author in work.get('author', []):
                given = author.get('given', '')
                family = author.get('family', '')
                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)
            paper['authors'] = authors
            
            # Publication date and year
            pub_date = self._extract_publication_date(work)
            if pub_date:
                paper['publication_date'] = pub_date.isoformat()
                paper['year'] = pub_date.year
            
            # Venue information
            container_title = work.get('container-title', [])
            if container_title:
                paper['venue'] = container_title[0] if isinstance(container_title, list) else container_title
            
            paper['publisher'] = work.get('publisher', '')
            paper['venue_type'] = 'journal'  # Crossref mostly has journals
            
            # ISSN
            issn_list = work.get('ISSN', [])
            if issn_list:
                paper['issn'] = issn_list[0]
            
            # Volume, issue, pages
            paper['volume'] = work.get('volume', '')
            paper['issue'] = work.get('issue', '')
            paper['pages'] = work.get('page', '')
            
            # Abstract (if available)
            paper['abstract'] = work.get('abstract', '')
            if paper['abstract']:
                # Clean up HTML tags sometimes present in Crossref abstracts
                paper['abstract'] = re.sub(r'<[^>]+>', '', paper['abstract'])
                paper['abstract'] = paper['abstract'].strip()
            
            # Subject categories as keywords
            subjects = work.get('subject', [])
            paper['keywords'] = subjects[:10] if subjects else []
            
            # PHM relevance scoring
            paper['phm_relevance_score'] = self._calculate_phm_relevance(paper)
            
            # Quality indicators
            paper['quality_indicators'] = {
                'has_doi': bool(paper['doi']),
                'has_abstract': bool(paper['abstract']),
                'citations': paper['cited_by_count'],
                'data_completeness': self._assess_data_completeness(paper),
                'venue_quality': self._assess_venue_quality(paper.get('venue', ''))
            }
            
            return paper
            
        except Exception as e:
            self.logger.error(f"Error converting Crossref work: {e}")
            return None
    
    def _extract_title(self, title_list: List[str]) -> str:
        """Extract title from Crossref title array."""
        if not title_list:
            return ''
        
        # Take the first (and usually only) title
        title = title_list[0] if isinstance(title_list, list) else str(title_list)
        
        # Clean up title
        title = re.sub(r'<[^>]+>', '', title)  # Remove HTML tags
        title = title.strip()
        
        return title
    
    def _extract_publication_date(self, work: Dict[str, Any]) -> Optional[date]:
        """Extract publication date from Crossref work."""
        
        # Try published-print first, then published-online
        for date_field in ['published-print', 'published-online']:
            date_parts = work.get(date_field, {}).get('date-parts', [])
            if date_parts and date_parts[0]:
                year = date_parts[0][0] if len(date_parts[0]) > 0 else None
                month = date_parts[0][1] if len(date_parts[0]) > 1 else 1
                day = date_parts[0][2] if len(date_parts[0]) > 2 else 1
                
                if year:
                    try:
                        return date(year, month, day)
                    except ValueError:
                        return date(year, 1, 1)
        
        return None
    
    def _calculate_phm_relevance(self, paper: Dict[str, Any]) -> float:
        """Calculate PHM relevance score based on content analysis."""
        
        # Combine text fields for analysis
        text_fields = [
            paper.get('title', ''),
            paper.get('abstract', ''),
            ' '.join(paper.get('keywords', [])),
            paper.get('venue', '')
        ]
        combined_text = ' '.join(text_fields).lower()
        
        if not combined_text.strip():
            return 0.0
        
        # Count PHM-related terms
        phm_matches = 0
        total_terms = len(self.phm_search_terms)
        
        for term in self.phm_search_terms:
            if term.lower() in combined_text:
                phm_matches += 1
        
        base_score = phm_matches / total_terms if total_terms > 0 else 0.0
        
        # Boost for papers in known PHM journals
        venue = paper.get('venue', '')
        if any(journal.lower() in venue.lower() for journal in self.target_journals.keys()):
            base_score = min(1.0, base_score * 1.5)
        
        # Boost for highly cited papers
        citations = paper.get('cited_by_count', 0)
        if citations > 50 and base_score > 0.3:
            base_score = min(1.0, base_score * 1.2)
        
        return base_score
    
    def _is_phm_relevant(self, paper: Dict[str, Any]) -> bool:
        """Check if paper meets minimum PHM relevance threshold."""
        
        relevance_score = paper.get('phm_relevance_score', 0.0)
        min_threshold = 0.2
        
        return relevance_score >= min_threshold
    
    def _is_excluded_publisher(self, paper: Dict[str, Any]) -> bool:
        """Check if paper is from an excluded publisher."""
        
        publisher = paper.get('publisher', '').lower()
        return any(excluded in publisher for excluded in self.excluded_publishers)
    
    def _assess_venue_quality(self, venue: str) -> str:
        """Assess venue quality based on known journal rankings."""
        
        venue_lower = venue.lower()
        
        for journal, info in self.target_journals.items():
            if journal.lower() in venue_lower:
                impact_factor = info.get('if', 0)
                if impact_factor >= 8.0:
                    return 'excellent'
                elif impact_factor >= 5.0:
                    return 'good'
                else:
                    return 'fair'
        
        return 'unknown'
    
    def _apply_quality_filters(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply quality filters to remove low-quality papers."""
        
        filtered_papers = []
        
        for paper in papers:
            # Basic quality checks
            if not paper.get('title') or len(paper['title']) < 10:
                continue
            
            if not paper.get('authors'):
                continue
            
            if not paper.get('doi'):  # DOI is crucial for Crossref
                continue
            
            # Year filter
            year = paper.get('year')
            if year and (year < 2015 or year > datetime.now().year):
                continue
            
            # Minimum citation threshold for older papers
            if year and datetime.now().year - year > 3:
                citations = paper.get('cited_by_count', 0)
                if citations < 10:  # Higher threshold for older papers
                    continue
            
            filtered_papers.append(paper)
        
        return filtered_papers
    
    def _assess_data_completeness(self, paper: Dict[str, Any]) -> float:
        """Assess how complete the paper metadata is."""
        
        completeness_score = 0.0
        
        # Check important fields
        checks = [
            ('doi', 0.2),
            ('title', 0.2),
            ('authors', 0.2),
            ('venue', 0.1),
            ('year', 0.1),
            ('abstract', 0.1),
            ('publisher', 0.05),
            ('pages', 0.05)
        ]
        
        for field, weight in checks:
            if paper.get(field):
                if isinstance(paper[field], (str, int)) and paper[field]:
                    completeness_score += weight
                elif isinstance(paper[field], list) and paper[field]:
                    completeness_score += weight
        
        return min(1.0, completeness_score)
    
    def search_by_journal(self, 
                         journal_name: str,
                         query: str = '',
                         max_results: int = 50,
                         year_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
        """Search for papers in a specific journal."""
        
        params = {
            'query.container-title': journal_name,
            'rows': min(max_results, 1000),
            'sort': 'score',
            'order': 'desc'
        }
        
        if query:
            params['query'] = query
        
        # Add year filter
        filter_parts = ['type:journal-article']
        if year_range:
            filter_parts.append(f'from-pub-date:{year_range[0]}')
            filter_parts.append(f'until-pub-date:{year_range[1]}')
        
        params['filter'] = ','.join(filter_parts)
        
        response_data = self._make_request('works', params)
        if not response_data:
            return []
        
        papers = []
        for work in response_data.get('message', {}).get('items', []):
            paper = self._convert_work_to_paper(work)
            if paper and self._is_phm_relevant(paper):
                papers.append(paper)
        
        return papers[:max_results]
    
    def get_paper_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a paper by DOI."""
        
        clean_doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
        endpoint = f'works/{clean_doi}'
        
        response_data = self._make_request(endpoint, {})
        if response_data and 'message' in response_data:
            return self._convert_work_to_paper(response_data['message'])
        
        return None
    
    def get_api_status(self) -> Dict[str, Any]:
        """Check API status and configuration."""
        
        try:
            response = requests.get(
                f"{self.base_url}/works",
                headers=self.headers,
                params={'rows': 1},
                timeout=10
            )
            
            return {
                'available': response.status_code == 200,
                'rate_limit': self.rate_limit,
                'user_agent': self.user_agent,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # Test the Crossref client
    client = CrossrefClient()
    
    print("Testing Crossref client...")
    
    # Test API status
    status = client.get_api_status()
    print(f"API Status: {json.dumps(status, indent=2)}")
    
    # Test search
    papers = client.search_papers(
        query="prognostics health management",
        max_results=5,
        year_range=(2020, 2024)
    )
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.get('title', 'No title')}")
        print(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"   Venue: {paper.get('venue', 'Unknown')}")
        print(f"   Year: {paper.get('year', 'Unknown')}")
        print(f"   DOI: {paper.get('doi', 'No DOI')}")
        print(f"   Citations: {paper.get('cited_by_count', 0)}")
        print(f"   PHM Relevance: {paper.get('phm_relevance_score', 0):.2f}")
        if paper.get('abstract'):
            print(f"   Abstract: {paper['abstract'][:150]}...")