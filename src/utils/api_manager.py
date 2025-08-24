"""
Centralized API Manager for APPA System

Orchestrates multiple academic APIs with intelligent fallback, deduplication,
and priority-based selection. Provides unified interface for paper discovery
across OpenAlex, Crossref, Semantic Scholar, PubMed, and Lens.org.

Features:
- Priority-based API selection
- Automatic fallback mechanisms
- Result deduplication by DOI/title
- Unified result format
- Rate limiting coordination
- Quality-based result ranking
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import hashlib
from collections import defaultdict

from .logging_config import get_logger
from .openalex_client import OpenAlexClient
from .crossref_client import CrossrefClient
from .semantic_scholar_client import SemanticScholarClient
from .pubmed_client import PubMedClient
from .lens_client import LensClient


class APIManager:
    """
    Centralized manager for all academic APIs with intelligent orchestration.
    
    Manages API priority, fallback strategies, result aggregation, and
    deduplication across multiple academic databases.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # Initialize all API clients
        self._initialize_clients()
        
        # API priority configuration (higher = preferred)
        self.api_priorities = {
            'openalex': 5,      # Free, comprehensive, good metadata
            'crossref': 4,      # Free, DOI authority, venue data
            'semantic_scholar': 3,  # Good AI features, requires key
            'pubmed': 2,        # Biomedical focus
            'lens': 1           # Comprehensive but requires key
        }
        
        # Result deduplication cache
        self.seen_papers = {}  # DOI/title hash -> paper data
        
        # Performance tracking
        self.api_stats = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'papers_found': 0,
            'avg_response_time': 0.0
        })
        
        self.logger.info("API Manager initialized with all clients")
    
    def _initialize_clients(self):
        """Initialize all API clients with error handling."""
        
        self.clients = {}
        
        try:
            self.clients['openalex'] = OpenAlexClient(self.config)
            self.logger.info("OpenAlex client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenAlex client: {e}")
        
        try:
            self.clients['crossref'] = CrossrefClient(self.config)
            self.logger.info("Crossref client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Crossref client: {e}")
        
        try:
            self.clients['semantic_scholar'] = SemanticScholarClient(self.config)
            self.logger.info("Semantic Scholar client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Semantic Scholar client: {e}")
        
        try:
            self.clients['pubmed'] = PubMedClient(self.config)
            self.logger.info("PubMed client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize PubMed client: {e}")
        
        try:
            self.clients['lens'] = LensClient(self.config)
            self.logger.info("Lens.org client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Lens.org client: {e}")
    
    def search_papers(self, 
                     query: str,
                     max_results: int = 50,
                     year_range: Optional[Tuple[int, int]] = None,
                     api_preference: Optional[List[str]] = None,
                     fallback: bool = True) -> List[Dict[str, Any]]:
        """
        Search for papers across multiple APIs with intelligent orchestration.
        
        Args:
            query: Search query string
            max_results: Maximum total results to return
            year_range: Tuple of (start_year, end_year)
            api_preference: List of preferred APIs in order
            fallback: Whether to use fallback if primary APIs fail
            
        Returns:
            Unified, deduplicated list of paper metadata
        """
        
        self.logger.info(f"Starting multi-API search for: '{query}'")
        
        # Determine API execution order
        api_order = self._get_api_execution_order(api_preference)
        
        # Track results from each API
        all_results = []
        per_api_limit = max(10, max_results // len(api_order))
        
        # Execute searches in priority order
        for api_name in api_order:
            if api_name not in self.clients:
                self.logger.warning(f"API client '{api_name}' not available")
                continue
            
            try:
                start_time = datetime.now()
                
                # Execute search
                results = self.clients[api_name].search_papers(
                    query=query,
                    max_results=per_api_limit,
                    year_range=year_range
                )
                
                # Update statistics
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                self._update_api_stats(api_name, len(results), response_time, success=True)
                
                # Add source annotation
                for paper in results:
                    paper['discovered_by'] = api_name
                    paper['discovery_timestamp'] = end_time.isoformat()
                
                all_results.extend(results)
                
                self.logger.info(f"{api_name}: Found {len(results)} papers")
                
                # Early termination if we have enough high-quality results
                if len(all_results) >= max_results * 2:  # Get extra for dedup
                    break
                    
            except Exception as e:
                self.logger.error(f"Error searching {api_name}: {e}")
                self._update_api_stats(api_name, 0, 0, success=False)
                
                if not fallback:
                    continue
        
        # Deduplicate and merge results
        deduplicated_results = self._deduplicate_results(all_results)
        
        # Quality-based ranking and filtering
        ranked_results = self._rank_by_quality(deduplicated_results)
        
        # Return top results
        final_results = ranked_results[:max_results]
        
        self.logger.info(f"Completed search: {len(final_results)} final papers from {len(all_results)} total")
        
        return final_results
    
    def _get_api_execution_order(self, preference: Optional[List[str]] = None) -> List[str]:
        """Determine API execution order based on preferences and priorities."""
        
        available_apis = list(self.clients.keys())
        
        if preference:
            # Use user preference, fallback to priority order
            ordered_apis = []
            for api in preference:
                if api in available_apis:
                    ordered_apis.append(api)
            
            # Add remaining APIs by priority
            remaining = set(available_apis) - set(ordered_apis)
            remaining_sorted = sorted(remaining, 
                                    key=lambda x: self.api_priorities.get(x, 0), 
                                    reverse=True)
            ordered_apis.extend(remaining_sorted)
            
            return ordered_apis
        
        else:
            # Use priority-based order
            return sorted(available_apis, 
                         key=lambda x: self.api_priorities.get(x, 0), 
                         reverse=True)
    
    def _deduplicate_results(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate papers by DOI, title similarity, and ArXiv ID."""
        
        deduplicated = []
        seen_dois = set()
        seen_arxiv_ids = set()
        seen_title_hashes = set()
        
        for paper in papers:
            # DOI-based deduplication (strongest signal)
            doi = paper.get('doi', '').strip().lower()
            if doi and doi in seen_dois:
                self.logger.debug(f"Duplicate DOI found: {doi}")
                continue
            
            # ArXiv ID deduplication
            arxiv_id = paper.get('arxiv_id', '').strip()
            if arxiv_id and arxiv_id in seen_arxiv_ids:
                self.logger.debug(f"Duplicate ArXiv ID found: {arxiv_id}")
                continue
            
            # Title-based deduplication (fuzzy)
            title = paper.get('title', '').strip().lower()
            if title:
                # Create normalized title hash
                title_normalized = self._normalize_title(title)
                title_hash = hashlib.md5(title_normalized.encode()).hexdigest()[:16]
                
                if title_hash in seen_title_hashes:
                    self.logger.debug(f"Duplicate title found: {title[:50]}...")
                    continue
                
                seen_title_hashes.add(title_hash)
            
            # Track identifiers
            if doi:
                seen_dois.add(doi)
            if arxiv_id:
                seen_arxiv_ids.add(arxiv_id)
            
            # Merge data if we've seen similar paper from different APIs
            merged_paper = self._merge_duplicate_data(paper, deduplicated)
            if merged_paper:
                deduplicated.append(merged_paper)
        
        self.logger.info(f"Deduplication: {len(papers)} -> {len(deduplicated)} papers")
        return deduplicated
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for similarity comparison."""
        
        # Remove common variations
        normalized = title.lower().strip()
        
        # Remove punctuation and extra spaces
        import re
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        # Remove common stopwords that don't affect meaning
        stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in normalized.split() if w not in stopwords]
        
        return ' '.join(words)
    
    def _merge_duplicate_data(self, paper: Dict[str, Any], existing: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge data from duplicate papers found by different APIs."""
        
        # For now, return the paper as-is
        # Future enhancement: merge complementary data
        return paper
    
    def _rank_by_quality(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank papers by quality score combining multiple factors."""
        
        def calculate_quality_score(paper: Dict[str, Any]) -> float:
            score = 0.0
            
            # PHM relevance score (40%)
            phm_score = paper.get('phm_relevance_score', 0.0)
            score += phm_score * 0.4
            
            # Citation count (30%)
            citations = paper.get('cited_by_count', 0)
            citation_score = min(1.0, citations / 100)  # Normalize to 0-1
            score += citation_score * 0.3
            
            # Recency bonus (20%)
            year = paper.get('year')
            if year:
                current_year = datetime.now().year
                years_old = current_year - year
                recency_score = max(0.0, 1.0 - years_old / 10)  # Decay over 10 years
                score += recency_score * 0.2
            
            # Data completeness (10%)
            completeness = self._assess_completeness(paper)
            score += completeness * 0.1
            
            return score
        
        # Add quality scores and sort
        for paper in papers:
            paper['quality_score'] = calculate_quality_score(paper)
        
        return sorted(papers, key=lambda p: p['quality_score'], reverse=True)
    
    def _assess_completeness(self, paper: Dict[str, Any]) -> float:
        """Assess metadata completeness."""
        
        important_fields = ['title', 'authors', 'abstract', 'doi', 'venue', 'year']
        present_fields = sum(1 for field in important_fields if paper.get(field))
        
        return present_fields / len(important_fields)
    
    def _update_api_stats(self, api_name: str, papers_found: int, response_time: float, success: bool):
        """Update API performance statistics."""
        
        stats = self.api_stats[api_name]
        stats['requests'] += 1
        stats['papers_found'] += papers_found
        
        if success:
            stats['successes'] += 1
            # Update rolling average response time
            old_avg = stats['avg_response_time']
            stats['avg_response_time'] = (old_avg + response_time) / 2
        else:
            stats['failures'] += 1
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get comprehensive API status and performance metrics."""
        
        status = {
            'apis_available': list(self.clients.keys()),
            'total_apis': len(self.clients),
            'api_priorities': self.api_priorities,
            'performance_stats': dict(self.api_stats)
        }
        
        # Test each API
        for api_name, client in self.clients.items():
            try:
                api_status = client.get_api_status()
                status[f'{api_name}_status'] = api_status
            except Exception as e:
                status[f'{api_name}_status'] = {'error': str(e), 'available': False}
        
        return status
    
    def search_by_doi(self, dois: List[str]) -> List[Dict[str, Any]]:
        """Search for papers by DOI using the most appropriate APIs."""
        
        self.logger.info(f"Searching for {len(dois)} papers by DOI")
        
        results = []
        
        # Prioritize APIs that are good for DOI lookup
        doi_apis = ['crossref', 'openalex', 'semantic_scholar']
        
        for doi in dois:
            found = False
            for api_name in doi_apis:
                if api_name not in self.clients:
                    continue
                
                try:
                    # Try to search by DOI
                    papers = self.clients[api_name].search_papers(
                        query=f'doi:"{doi}"',
                        max_results=1
                    )
                    
                    if papers:
                        results.extend(papers)
                        found = True
                        break
                        
                except Exception as e:
                    self.logger.warning(f"DOI search failed for {api_name}: {e}")
                    continue
            
            if not found:
                self.logger.warning(f"DOI not found in any API: {doi}")
        
        return self._deduplicate_results(results)
    
    def get_aggregated_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics across all APIs."""
        
        total_requests = sum(stats['requests'] for stats in self.api_stats.values())
        total_successes = sum(stats['successes'] for stats in self.api_stats.values())
        total_papers = sum(stats['papers_found'] for stats in self.api_stats.values())
        
        return {
            'total_requests': total_requests,
            'total_successes': total_successes,
            'total_papers_found': total_papers,
            'success_rate': total_successes / total_requests if total_requests > 0 else 0.0,
            'avg_papers_per_request': total_papers / total_requests if total_requests > 0 else 0.0,
            'by_api': dict(self.api_stats)
        }


if __name__ == "__main__":
    # Test the API manager
    manager = APIManager()
    
    print("Testing API Manager...")
    
    # Test API status
    status = manager.get_api_status()
    print(f"API Status: {json.dumps(status, indent=2)}")
    
    # Test search
    papers = manager.search_papers(
        query="prognostics health management bearing fault diagnosis",
        max_results=10
    )
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.get('title', 'No title')[:80]}...")
        print(f"   Source: {paper.get('discovered_by', 'Unknown')}")
        print(f"   Year: {paper.get('year', 'Unknown')}")
        print(f"   Citations: {paper.get('cited_by_count', 0)}")
        print(f"   PHM Relevance: {paper.get('phm_relevance_score', 0):.3f}")
        print(f"   Quality Score: {paper.get('quality_score', 0):.3f}")
    
    # Show aggregated statistics
    stats = manager.get_aggregated_stats()
    print(f"\nAggregated Statistics: {json.dumps(stats, indent=2)}")