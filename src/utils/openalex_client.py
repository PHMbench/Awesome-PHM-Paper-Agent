"""
OpenAlex API Client for APPA System

OpenAlex is a free, comprehensive academic database covering all disciplines.
This client handles abstract reconstruction from inverted indices and provides
PHM-specific filtering capabilities.

Documentation: https://docs.openalex.org/
No authentication required, but email recommended for "polite pool" access.
"""

import os
import re
import json
import time
import requests
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
from urllib.parse import quote

from .base_api_client import BaseAPIClient, APIClientError
from .paper_quality_filter import PaperQualityFilter


class OpenAlexClient(BaseAPIClient):
    """
    OpenAlex API client with PHM paper discovery capabilities.
    
    Features:
    - Free access (no API key required)
    - Comprehensive cross-disciplinary coverage
    - Abstract reconstruction from inverted indices
    - Publisher and venue filtering
    - Rate limiting with polite pool support
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # OpenAlex-specific configuration
        self.base_url = "https://api.openalex.org"
        self.email = os.environ.get('OPENALEX_EMAIL', '')
        self.rate_limit = 10  # requests per second (polite pool)
        
        # Update session headers for OpenAlex
        self.session.headers.update({
            'User-Agent': f'APPA/1.0 (Awesome-PHM-Paper-Agent; {self.email})'
        })
        
        # Quality filter
        self.quality_filter = PaperQualityFilter(config)
        
        self.logger.info(f"OpenAlex client initialized {'with email' if self.email else 'without email'}")
    
    def _make_openalex_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make request to OpenAlex API using base class method."""
        # Add polite pool email if available
        if self.email:
            params['mailto'] = self.email
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            return self._make_request(url, params=params)
        except APIClientError as e:
            self.logger.error(f"OpenAlex API request failed: {e}")
            return None
    
    def search_papers(self, 
                     query: str,
                     filters: Optional[Dict[str, Any]] = None,
                     max_results: int = 50,
                     year_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
        """
        Search for PHM papers in OpenAlex.
        
        Args:
            query: Search query string
            filters: Additional filters (venue, publisher, etc.)
            max_results: Maximum number of results
            year_range: Tuple of (start_year, end_year)
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Searching OpenAlex for: {query}")
        
        # Build search parameters
        params = {
            'search': query,
            'per-page': min(max_results, 200),  # OpenAlex limit per request
            'sort': 'cited_by_count:desc',  # Most cited first
            'select': ','.join([
                'id', 'title', 'display_name', 'doi', 'publication_year',
                'publication_date', 'primary_location', 'open_access',
                'authorships', 'concepts', 'abstract_inverted_index',
                'cited_by_count', 'biblio', 'is_retracted', 'is_paratext',
                'host_venue', 'primary_topic', 'keywords'
            ])
        }
        
        # Apply year range filter
        if year_range:
            params['filter'] = f'publication_year:{year_range[0]}-{year_range[1]}'
        
        # Apply additional filters
        if filters:
            filter_parts = []
            
            # Publisher filter (exclude MDPI, etc.)
            if 'exclude_publishers' in filters:
                for pub in filters['exclude_publishers']:
                    filter_parts.append(f'host_venue.publisher.display_name.search:!{pub}')
            
            # Venue type filter
            if 'venue_types' in filters:
                venue_types = ','.join(filters['venue_types'])
                filter_parts.append(f'primary_location.source.type:{venue_types}')
            
            # Impact factor filter (approximate using venue tier)
            if 'min_impact_factor' in filters:
                # OpenAlex doesn't have direct IF, but we can filter by venue prestige
                pass  # Will implement post-processing filter
            
            if filter_parts:
                existing_filter = params.get('filter', '')
                if existing_filter:
                    params['filter'] = f"{existing_filter},{','.join(filter_parts)}"
                else:
                    params['filter'] = ','.join(filter_parts)
        
        # Make request
        response_data = self._make_openalex_request('works', params)
        if not response_data:
            return []
        
        papers = []
        for work in response_data.get('results', []):
            try:
                paper = self._convert_work_to_paper(work)
                if paper and self.is_phm_relevant(paper):
                    papers.append(paper)
                    
            except Exception as e:
                self.logger.warning(f"Failed to process work {work.get('id', 'unknown')}: {e}")
                continue
        
        # Apply quality filters
        filtered_papers = self.apply_quality_filters(papers)
        
        self.logger.info(f"Found {len(filtered_papers)} PHM-relevant papers from OpenAlex")
        return filtered_papers[:max_results]
    
    def _convert_work_to_paper(self, work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert OpenAlex work object to standard paper format."""
        
        try:
            # Basic metadata
            paper = {
                'id': work.get('id', '').replace('https://openalex.org/', ''),
                'title': work.get('display_name', '').strip(),
                'doi': work.get('doi', '').replace('https://doi.org/', '') if work.get('doi') else '',
                'year': work.get('publication_year'),
                'publication_date': work.get('publication_date'),
                'cited_by_count': work.get('cited_by_count', 0),
                'is_open_access': work.get('open_access', {}).get('is_oa', False),
                'source': 'openalex'
            }
            
            # Authors
            authors = []
            for authorship in work.get('authorships', []):
                author = authorship.get('author', {})
                if author.get('display_name'):
                    authors.append(author['display_name'])
            paper['authors'] = authors
            
            # Venue information
            host_venue = work.get('host_venue') or work.get('primary_location', {}).get('source', {})
            if host_venue:
                paper['venue'] = host_venue.get('display_name', '')
                paper['venue_type'] = host_venue.get('type', '')
                paper['publisher'] = host_venue.get('publisher', '')
                paper['issn'] = host_venue.get('issn_l', '')
                paper['is_core'] = host_venue.get('is_core', False)
            
            # Abstract reconstruction from inverted index
            paper['abstract'] = self._reconstruct_abstract(work.get('abstract_inverted_index', {}))
            
            # Keywords and concepts
            keywords = []
            for concept in work.get('concepts', []):
                if concept.get('level', 0) <= 2:  # Top-level concepts only
                    keywords.append(concept.get('display_name', ''))
            paper['keywords'] = keywords[:10]  # Limit to top 10
            
            # PHM relevance scoring
            paper['phm_relevance_score'] = self.calculate_phm_relevance(paper)
            
            # Quality indicators
            paper['quality_indicators'] = {
                'citations': paper['cited_by_count'],
                'open_access': paper['is_open_access'],
                'venue_prestige': 'high' if paper.get('is_core') else 'medium',
                'data_completeness': self.assess_data_completeness(paper)
            }
            
            return paper
            
        except Exception as e:
            self.logger.error(f"Error converting OpenAlex work: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """
        Reconstruct abstract from OpenAlex inverted index format.
        
        OpenAlex stores abstracts as inverted indices for space efficiency.
        We need to reconstruct the original text.
        """
        if not inverted_index:
            return ''
        
        try:
            # Create position -> word mapping
            word_positions = {}
            for word, positions in inverted_index.items():
                for pos in positions:
                    word_positions[pos] = word
            
            # Sort by position and join
            sorted_positions = sorted(word_positions.keys())
            abstract_words = [word_positions[pos] for pos in sorted_positions]
            
            # Join with spaces and clean up
            abstract = ' '.join(abstract_words)
            
            # Basic text cleaning
            abstract = re.sub(r'\s+', ' ', abstract)  # Normalize whitespace
            abstract = abstract.strip()
            
            return abstract
            
        except Exception as e:
            self.logger.warning(f"Failed to reconstruct abstract: {e}")
            return ''
    
    
    
    def search_by_venue(self, 
                       venue_name: str,
                       query: str = '',
                       max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for papers in a specific venue."""
        
        params = {
            'filter': f'host_venue.display_name.search:{venue_name}',
            'per-page': min(max_results, 200),
            'sort': 'cited_by_count:desc'
        }
        
        if query:
            params['search'] = query
        
        response_data = self._make_openalex_request('works', params)
        if not response_data:
            return []
        
        papers = []
        for work in response_data.get('results', []):
            paper = self._convert_work_to_paper(work)
            if paper and self._is_phm_relevant(paper):
                papers.append(paper)
        
        return papers[:max_results]
    
    def get_paper_details(self, openalex_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific paper by OpenAlex ID."""
        
        endpoint = f'works/{openalex_id}'
        response_data = self._make_openalex_request(endpoint, {})
        
        if response_data:
            return self._convert_work_to_paper(response_data)
        
        return None
    
    def get_api_status(self) -> Dict[str, Any]:
        """Check API status and rate limits."""
        
        try:
            response = requests.get(
                f"{self.base_url}/works",
                headers=self.session.headers,
                params={'per-page': 1, 'mailto': self.email},
                timeout=10
            )
            
            return {
                'available': response.status_code == 200,
                'rate_limit': self.rate_limit,
                'email_configured': bool(self.email),
                'polite_pool': bool(self.email),
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': str(e)
            }


if __name__ == "__main__":
    # Test the OpenAlex client
    client = OpenAlexClient()
    
    print("Testing OpenAlex client...")
    
    # Test API status
    status = client.get_api_status()
    print(f"API Status: {json.dumps(status, indent=2)}")
    
    # Test search
    papers = client.search_papers(
        query="prognostics health management fault diagnosis",
        max_results=5
    )
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.get('title', 'No title')}")
        print(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"   Venue: {paper.get('venue', 'Unknown')}")
        print(f"   Year: {paper.get('year', 'Unknown')}")
        print(f"   Citations: {paper.get('cited_by_count', 0)}")
        print(f"   PHM Relevance: {paper.get('phm_relevance_score', 0):.2f}")
        print(f"   Abstract: {paper.get('abstract', 'No abstract')[:200]}...")