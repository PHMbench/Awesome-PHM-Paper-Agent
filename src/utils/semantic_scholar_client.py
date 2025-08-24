"""
Semantic Scholar API Client for APPA System

Semantic Scholar provides AI-powered paper search with excellent abstracts,
citation graphs, and semantic relationships between papers.

Documentation: https://api.semanticscholar.org/
Requires API key registration (free tier available).
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .logging_config import get_logger


class SemanticScholarClient:
    """
    Semantic Scholar API client for intelligent paper discovery.
    
    Features:
    - AI-powered semantic search
    - Excellent abstract coverage
    - Citation graph traversal  
    - Paper embeddings and similarity
    - Author and venue information
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # API Configuration
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = os.environ.get('SEMANTIC_SCHOLAR_API_KEY', '')
        
        # Rate limits (with API key: 100 requests/5min, without: 100 requests/5min but lower priority)
        self.rate_limit = 1.0 if self.api_key else 0.5  # requests per second
        self.max_requests_per_batch = 100
        
        # Request headers
        self.headers = {
            'User-Agent': 'APPA/1.0 (Awesome-PHM-Paper-Agent)',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            self.headers['x-api-key'] = self.api_key
        
        # PHM-specific search configuration
        self.phm_fields = [
            'paperId', 'title', 'abstract', 'year', 'authors', 'venue',
            'publicationTypes', 'publicationDate', 'citationCount',
            'influentialCitationCount', 'openAccessPdf', 'fieldsOfStudy',
            'isOpenAccess', 'publicationVenue', 's2FieldsOfStudy', 'doi',
            'externalIds', 'url', 'referenceCount'
        ]
        
        # PHM keywords for relevance scoring
        self.phm_keywords = {
            'core': [
                'prognostics', 'health management', 'PHM', 'condition monitoring',
                'predictive maintenance', 'fault diagnosis', 'anomaly detection',
                'failure prediction', 'reliability engineering'
            ],
            'technical': [
                'remaining useful life', 'RUL', 'degradation modeling',
                'health assessment', 'system reliability', 'maintenance optimization',
                'sensor fusion', 'digital twin', 'signal processing', 'pattern recognition'
            ],
            'ml_methods': [
                'machine learning', 'deep learning', 'neural networks', 'CNN', 'RNN', 'LSTM',
                'support vector machine', 'random forest', 'ensemble learning',
                'transfer learning', 'unsupervised learning', 'reinforcement learning'
            ],
            'applications': [
                'bearing', 'gearbox', 'turbine', 'motor', 'pump', 'valve', 'battery',
                'aircraft', 'automotive', 'wind energy', 'manufacturing', 'industrial'
            ]
        }
        
        # Excluded publishers and venues
        self.excluded_publishers = {
            'mdpi', 'mdpi ag', 'multidisciplinary digital publishing institute',
            'hindawi', 'bentham', 'scirp', 'omics'
        }
        
        self.logger.info(f"Semantic Scholar client initialized {'with API key' if self.api_key else 'without API key'}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make rate-limited request to Semantic Scholar API."""
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            # Rate limiting
            time.sleep(1.0 / self.rate_limit)
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Semantic Scholar API request failed: {e}")
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                self.logger.warning("Rate limit exceeded, backing off...")
                time.sleep(60)  # Wait 1 minute before retry
            return None
    
    def search_papers(self,
                     query: str,
                     filters: Optional[Dict[str, Any]] = None,
                     max_results: int = 50,
                     year_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
        """
        Search for PHM papers using Semantic Scholar.
        
        Args:
            query: Search query string
            filters: Additional filters (venue, fields of study, etc.)
            max_results: Maximum number of results
            year_range: Tuple of (start_year, end_year)
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Searching Semantic Scholar for: {query}")
        
        # Enhance query with PHM context
        enhanced_query = self._enhance_query_for_phm(query)
        
        # Build search parameters
        params = {
            'query': enhanced_query,
            'limit': min(max_results, 100),  # API limit per request
            'fields': ','.join(self.phm_fields)
        }
        
        # Apply year filter
        if year_range:
            start_year, end_year = year_range
            params['year'] = f"{start_year}-{end_year}"
        
        # Apply additional filters
        if filters:
            if 'fields_of_study' in filters:
                params['fieldsOfStudy'] = ','.join(filters['fields_of_study'])
            
            if 'venue' in filters:
                params['venue'] = filters['venue']
            
            if 'min_citation_count' in filters:
                params['minCitationCount'] = filters['min_citation_count']
        
        # Make request
        response_data = self._make_request('paper/search', params)
        if not response_data:
            return []
        
        papers = []
        for paper_data in response_data.get('data', []):
            try:
                paper = self._convert_paper_to_standard_format(paper_data)
                if paper and self._is_phm_relevant(paper) and not self._is_excluded(paper):
                    papers.append(paper)
                    
            except Exception as e:
                self.logger.warning(f"Failed to process Semantic Scholar paper: {e}")
                continue
        
        # Apply quality filters and sort
        filtered_papers = self._apply_quality_filters(papers)
        
        # Sort by a combination of relevance, citations, and recency
        filtered_papers.sort(key=self._calculate_paper_score, reverse=True)
        
        self.logger.info(f"Found {len(filtered_papers)} PHM-relevant papers from Semantic Scholar")
        return filtered_papers[:max_results]
    
    def _enhance_query_for_phm(self, query: str) -> str:
        """Enhance search query with PHM-specific context."""
        
        # Add PHM context if not already present
        phm_terms = ['phm', 'prognostic', 'health management', 'predictive maintenance']
        if not any(term in query.lower() for term in phm_terms):
            # Add PHM context
            query = f"{query} prognostics health management"
        
        return query
    
    def _convert_paper_to_standard_format(self, paper_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Semantic Scholar paper to standard format."""
        
        try:
            paper = {
                'id': paper_data.get('paperId', ''),
                'title': paper_data.get('title', '').strip(),
                'abstract': paper_data.get('abstract', '').strip(),
                'year': paper_data.get('year'),
                'publication_date': paper_data.get('publicationDate'),
                'cited_by_count': paper_data.get('citationCount', 0),
                'influential_citation_count': paper_data.get('influentialCitationCount', 0),
                'reference_count': paper_data.get('referenceCount', 0),
                'is_open_access': paper_data.get('isOpenAccess', False),
                'source': 'semantic_scholar'
            }
            
            # DOI and external IDs
            external_ids = paper_data.get('externalIds', {})
            if external_ids:
                paper['doi'] = external_ids.get('DOI', '')
                paper['arxiv_id'] = external_ids.get('ArXiv', '')
                paper['pmid'] = external_ids.get('PubMed', '')
            
            # Authors
            authors = []
            for author_data in paper_data.get('authors', []):
                if author_data.get('name'):
                    authors.append(author_data['name'])
            paper['authors'] = authors
            
            # Venue information
            venue_info = paper_data.get('publicationVenue') or paper_data.get('venue')
            if venue_info:
                if isinstance(venue_info, dict):
                    paper['venue'] = venue_info.get('name', '')
                    paper['venue_type'] = venue_info.get('type', '')
                    paper['publisher'] = venue_info.get('publisher', '')
                else:
                    paper['venue'] = str(venue_info)
                    paper['venue_type'] = 'unknown'
                    paper['publisher'] = ''
            else:
                paper['venue'] = ''
                paper['venue_type'] = ''
                paper['publisher'] = ''
            
            # Publication types
            pub_types = paper_data.get('publicationTypes', [])
            paper['publication_types'] = pub_types
            
            # Fields of study (as keywords)
            fields_of_study = []
            
            # S2 Fields of Study (more detailed)
            for field in paper_data.get('s2FieldsOfStudy', []):
                if field.get('category'):
                    fields_of_study.append(field['category'])
            
            # Legacy fields of study
            for field in paper_data.get('fieldsOfStudy', []):
                if isinstance(field, str):
                    fields_of_study.append(field)
                elif isinstance(field, dict) and field.get('category'):
                    fields_of_study.append(field['category'])
            
            paper['keywords'] = list(set(fields_of_study))[:15]  # Limit and deduplicate
            
            # PDF URL
            open_access_pdf = paper_data.get('openAccessPdf')
            if open_access_pdf:
                paper['pdf_url'] = open_access_pdf.get('url', '')
            
            # Semantic Scholar URL
            paper['url'] = paper_data.get('url', '')
            
            # Calculate PHM relevance
            paper['phm_relevance_score'] = self._calculate_phm_relevance(paper)
            
            # Quality indicators
            paper['quality_indicators'] = {
                'has_abstract': bool(paper['abstract']),
                'has_doi': bool(paper.get('doi')),
                'citations': paper['cited_by_count'],
                'influential_citations': paper['influential_citation_count'],
                'open_access': paper['is_open_access'],
                'data_completeness': self._assess_data_completeness(paper)
            }
            
            return paper
            
        except Exception as e:
            self.logger.error(f"Error converting Semantic Scholar paper: {e}")
            return None
    
    def _calculate_phm_relevance(self, paper: Dict[str, Any]) -> float:
        """Calculate PHM relevance score using multiple factors."""
        
        # Combine text fields
        text_content = ' '.join([
            paper.get('title', ''),
            paper.get('abstract', ''),
            ' '.join(paper.get('keywords', [])),
            paper.get('venue', '')
        ]).lower()
        
        if not text_content.strip():
            return 0.0
        
        # Score different categories
        category_scores = {}
        total_weight = 0.0
        
        weights = {
            'core': 0.4,        # Core PHM concepts most important
            'technical': 0.3,   # Technical methods
            'ml_methods': 0.2,  # ML approaches
            'applications': 0.1 # Application domains
        }
        
        for category, keywords in self.phm_keywords.items():
            matches = sum(1 for kw in keywords if kw.lower() in text_content)
            max_possible = len(keywords)
            category_score = matches / max_possible if max_possible > 0 else 0.0
            
            weight = weights.get(category, 0.1)
            category_scores[category] = category_score * weight
            total_weight += weight
        
        # Combine scores
        base_score = sum(category_scores.values()) / total_weight if total_weight > 0 else 0.0
        
        # Boost for highly cited papers in relevant fields
        citations = paper.get('cited_by_count', 0)
        if citations > 30 and base_score > 0.3:
            base_score = min(1.0, base_score * 1.3)
        
        # Boost for papers with influential citations
        influential_citations = paper.get('influential_citation_count', 0)
        if influential_citations > 10 and base_score > 0.4:
            base_score = min(1.0, base_score * 1.2)
        
        return min(1.0, base_score)
    
    def _is_phm_relevant(self, paper: Dict[str, Any]) -> bool:
        """Check if paper meets PHM relevance threshold."""
        
        relevance_score = paper.get('phm_relevance_score', 0.0)
        min_threshold = 0.25  # Slightly higher threshold for quality
        
        return relevance_score >= min_threshold
    
    def _is_excluded(self, paper: Dict[str, Any]) -> bool:
        """Check if paper should be excluded based on publisher or venue."""
        
        # Check publisher
        publisher = paper.get('publisher', '').lower()
        if any(excluded in publisher for excluded in self.excluded_publishers):
            return True
        
        # Check venue name for MDPI journals
        venue = paper.get('venue', '').lower()
        mdpi_venues = ['sensors', 'electronics', 'applied sciences', 'processes', 'sustainability']
        if any(mdpi_venue in venue for mdpi_venue in mdpi_venues):
            return True
        
        return False
    
    def _apply_quality_filters(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply quality filters to papers."""
        
        filtered_papers = []
        current_year = datetime.now().year
        
        for paper in papers:
            # Basic quality checks
            if not paper.get('title') or len(paper['title']) < 10:
                continue
            
            if not paper.get('abstract') or len(paper['abstract']) < 50:
                continue
            
            if not paper.get('authors'):
                continue
            
            # Year filter
            year = paper.get('year')
            if year and (year < 2015 or year > current_year):
                continue
            
            # Citation threshold for older papers
            if year and current_year - year > 2:
                citations = paper.get('cited_by_count', 0)
                if citations < 5:
                    continue
            
            filtered_papers.append(paper)
        
        return filtered_papers
    
    def _calculate_paper_score(self, paper: Dict[str, Any]) -> float:
        """Calculate composite score for ranking papers."""
        
        # Components of the score
        relevance = paper.get('phm_relevance_score', 0.0)
        citations = paper.get('cited_by_count', 0)
        influential_citations = paper.get('influential_citation_count', 0)
        year = paper.get('year', 2000)
        
        # Normalize components
        citation_score = min(1.0, citations / 100.0)  # Normalize to 0-1
        influential_score = min(1.0, influential_citations / 20.0)  # Normalize to 0-1
        recency_score = max(0.0, (year - 2015) / (datetime.now().year - 2015))  # Newer papers get higher score
        
        # Weighted combination
        composite_score = (
            relevance * 0.4 +
            citation_score * 0.3 +
            influential_score * 0.2 +
            recency_score * 0.1
        )
        
        return composite_score
    
    def _assess_data_completeness(self, paper: Dict[str, Any]) -> float:
        """Assess completeness of paper metadata."""
        
        completeness_score = 0.0
        
        fields_to_check = [
            ('title', 0.15),
            ('abstract', 0.25),
            ('authors', 0.15),
            ('venue', 0.10),
            ('year', 0.10),
            ('doi', 0.10),
            ('keywords', 0.10),
            ('pdf_url', 0.05)
        ]
        
        for field, weight in fields_to_check:
            if paper.get(field):
                if isinstance(paper[field], str) and paper[field].strip():
                    completeness_score += weight
                elif isinstance(paper[field], list) and paper[field]:
                    completeness_score += weight
                elif isinstance(paper[field], int) and paper[field] > 0:
                    completeness_score += weight
        
        return min(1.0, completeness_score)
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific paper by Semantic Scholar ID."""
        
        params = {'fields': ','.join(self.phm_fields)}
        endpoint = f'paper/{paper_id}'
        
        response_data = self._make_request(endpoint, params)
        if response_data:
            return self._convert_paper_to_standard_format(response_data)
        
        return None
    
    def get_related_papers(self, paper_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Get papers related to a specific paper by ID."""
        
        endpoint = f'paper/{paper_id}/references'
        params = {
            'fields': ','.join(self.phm_fields),
            'limit': max_results
        }
        
        response_data = self._make_request(endpoint, params)
        if not response_data:
            return []
        
        related_papers = []
        for ref_data in response_data.get('data', []):
            cited_paper = ref_data.get('citedPaper', {})
            if cited_paper:
                paper = self._convert_paper_to_standard_format(cited_paper)
                if paper and self._is_phm_relevant(paper):
                    related_papers.append(paper)
        
        return related_papers
    
    def get_api_status(self) -> Dict[str, Any]:
        """Check API status and configuration."""
        
        try:
            # Make a minimal request to test API access
            response = requests.get(
                f"{self.base_url}/paper/search",
                headers=self.headers,
                params={'query': 'test', 'limit': 1},
                timeout=10
            )
            
            return {
                'available': response.status_code == 200,
                'has_api_key': bool(self.api_key),
                'rate_limit': self.rate_limit,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # Test the Semantic Scholar client
    client = SemanticScholarClient()
    
    print("Testing Semantic Scholar client...")
    
    # Test API status
    status = client.get_api_status()
    print(f"API Status: {json.dumps(status, indent=2)}")
    
    if status.get('available'):
        # Test search
        papers = client.search_papers(
            query="prognostics health management deep learning",
            max_results=5,
            year_range=(2020, 2024)
        )
        
        print(f"\nFound {len(papers)} papers:")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper.get('title', 'No title')}")
            print(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
            print(f"   Venue: {paper.get('venue', 'Unknown')}")
            print(f"   Year: {paper.get('year', 'Unknown')}")
            print(f"   Citations: {paper.get('cited_by_count', 0)} (Influential: {paper.get('influential_citation_count', 0)})")
            print(f"   PHM Relevance: {paper.get('phm_relevance_score', 0):.3f}")
            print(f"   Open Access: {paper.get('is_open_access', False)}")
            if paper.get('abstract'):
                print(f"   Abstract: {paper['abstract'][:200]}...")
    else:
        print("API not available or not configured properly")