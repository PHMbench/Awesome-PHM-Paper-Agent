"""
Lens.org Scholarly API Client for APPA System

Lens.org provides comprehensive scholarly data with excellent metadata coverage,
multi-identifier search, and strong patent integration capabilities.

Documentation: https://docs.api.lens.org/
Requires API key registration (free tier available).
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .logging_config import get_logger


class LensClient:
    """
    Lens.org API client for comprehensive scholarly search.
    
    Features:
    - Multi-identifier search (DOI, PMID, etc.)
    - Excellent metadata completeness
    - Patent and scholarly integration
    - Strong filtering capabilities
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # API Configuration
        self.base_url = "https://api.lens.org"
        self.api_key = os.environ.get('LENS_API_KEY', '')
        self.rate_limit = 2  # requests per second
        
        # Headers
        self.headers = {
            'Authorization': f'Bearer {self.api_key}' if self.api_key else '',
            'Content-Type': 'application/json',
            'User-Agent': 'APPA/1.0 (Awesome-PHM-Paper-Agent)'
        }
        
        # PHM search configuration
        self.phm_keywords = [
            'prognostics', 'health management', 'predictive maintenance',
            'condition monitoring', 'fault diagnosis', 'remaining useful life',
            'reliability', 'degradation', 'anomaly detection'
        ]
        
        self.logger.info(f"Lens.org client initialized {'with API key' if self.api_key else 'without API key'}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_request(self, endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Lens.org API."""
        
        if not self.api_key:
            self.logger.warning("Lens.org API key not configured")
            return None
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            time.sleep(1.0 / self.rate_limit)
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Lens.org API request failed: {e}")
            return None
    
    def search_papers(self,
                     query: str,
                     filters: Optional[Dict[str, Any]] = None,
                     max_results: int = 50,
                     year_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
        """Search for PHM papers using Lens.org API."""
        
        if not self.api_key:
            self.logger.warning("Skipping Lens.org search - API key not configured")
            return []
        
        self.logger.info(f"Searching Lens.org for: {query}")
        
        # Build search payload
        payload = {
            'query': {
                'bool': {
                    'must': [
                        {
                            'multi_match': {
                                'query': query,
                                'fields': ['title^2', 'abstract', 'keywords']
                            }
                        }
                    ],
                    'filter': []
                }
            },
            'size': min(max_results, 100),
            'sort': [{'cited_by_count': {'order': 'desc'}}],
            'include': [
                'lens_id', 'title', 'abstract', 'year_published',
                'author', 'source_title', 'doi', 'external_ids',
                'cited_by_count', 'references_count', 'open_access',
                'publication_type', 'source_country', 'fields_of_study'
            ]
        }
        
        # Add year filter
        if year_range:
            payload['query']['bool']['filter'].append({
                'range': {
                    'year_published': {
                        'gte': year_range[0],
                        'lte': year_range[1]
                    }
                }
            })
        
        # Add PHM relevance filter
        phm_terms = ' OR '.join(self.phm_keywords)
        payload['query']['bool']['must'].append({
            'multi_match': {
                'query': phm_terms,
                'fields': ['title', 'abstract'],
                'minimum_should_match': '30%'
            }
        })
        
        # Make request
        response_data = self._make_request('scholarly/search', payload)
        if not response_data:
            return []
        
        papers = []
        for hit in response_data.get('data', []):
            try:
                paper = self._convert_lens_result_to_paper(hit)
                if paper and self._is_phm_relevant(paper):
                    papers.append(paper)
            except Exception as e:
                self.logger.warning(f"Failed to process Lens.org result: {e}")
                continue
        
        self.logger.info(f"Found {len(papers)} PHM papers from Lens.org")
        return papers
    
    def _convert_lens_result_to_paper(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Lens.org result to standard format."""
        
        try:
            paper = {
                'id': result.get('lens_id', ''),
                'title': result.get('title', ''),
                'abstract': result.get('abstract', ''),
                'year': result.get('year_published'),
                'cited_by_count': result.get('cited_by_count', 0),
                'reference_count': result.get('references_count', 0),
                'is_open_access': result.get('open_access', {}).get('is_oa', False),
                'source': 'lens'
            }
            
            # Authors
            authors = []
            for author in result.get('author', []):
                if author.get('display_name'):
                    authors.append(author['display_name'])
            paper['authors'] = authors
            
            # Venue
            paper['venue'] = result.get('source_title', '')
            paper['venue_type'] = result.get('publication_type', '')
            
            # DOI and external IDs
            paper['doi'] = result.get('doi', '')
            external_ids = result.get('external_ids', {})
            if external_ids:
                paper['pmid'] = external_ids.get('pmid', '')
                paper['arxiv_id'] = external_ids.get('arxiv', '')
            
            # Keywords from fields of study
            fields = result.get('fields_of_study', [])
            paper['keywords'] = [field.get('name', '') for field in fields][:10]
            
            # Calculate PHM relevance
            paper['phm_relevance_score'] = self._calculate_phm_relevance(paper)
            
            return paper
            
        except Exception as e:
            self.logger.error(f"Error converting Lens.org result: {e}")
            return None
    
    def _calculate_phm_relevance(self, paper: Dict[str, Any]) -> float:
        """Calculate PHM relevance score."""
        
        text_content = ' '.join([
            paper.get('title', ''),
            paper.get('abstract', ''),
            ' '.join(paper.get('keywords', []))
        ]).lower()
        
        if not text_content.strip():
            return 0.0
        
        matches = sum(1 for kw in self.phm_keywords if kw.lower() in text_content)
        return min(1.0, matches / len(self.phm_keywords) * 2)  # Boost to 0-1 range
    
    def _is_phm_relevant(self, paper: Dict[str, Any]) -> bool:
        """Check PHM relevance threshold."""
        return paper.get('phm_relevance_score', 0.0) >= 0.3
    
    def get_api_status(self) -> Dict[str, Any]:
        """Check API status."""
        
        if not self.api_key:
            return {
                'available': False,
                'error': 'API key not configured'
            }
        
        try:
            # Test with minimal request
            payload = {'query': {'match_all': {}}, 'size': 1}
            response = requests.post(
                f"{self.base_url}/scholarly/search",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            return {
                'available': response.status_code == 200,
                'has_api_key': True,
                'rate_limit': self.rate_limit,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }


if __name__ == "__main__":
    client = LensClient()
    
    print("Testing Lens.org client...")
    status = client.get_api_status()
    print(f"API Status: {json.dumps(status, indent=2)}")
    
    if status.get('available'):
        papers = client.search_papers(
            query="prognostics health management",
            max_results=3,
            year_range=(2020, 2024)
        )
        
        print(f"\nFound {len(papers)} papers:")
        for i, paper in enumerate(papers, 1):
            print(f"\n{i}. {paper.get('title', 'No title')}")
            print(f"   Year: {paper.get('year', 'Unknown')}")
            print(f"   Citations: {paper.get('cited_by_count', 0)}")
            print(f"   PHM Relevance: {paper.get('phm_relevance_score', 0):.3f}")
    else:
        print("API not available or not configured")