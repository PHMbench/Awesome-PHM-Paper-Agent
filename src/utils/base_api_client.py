"""
Base API Client for APPA System

Provides common functionality for all academic database API clients,
including request handling, rate limiting, PHM relevance scoring,
and quality assessment.
"""

import os
import re
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import requests

from .logging_config import get_logger


class APIClientError(Exception):
    """Base exception for API client errors."""
    pass


class BaseAPIClient(ABC):
    """
    Base class for all academic database API clients.
    
    Provides common functionality:
    - HTTP request handling with retry logic
    - Rate limiting and timeout management
    - PHM relevance scoring
    - Quality assessment methods
    - Standardized error handling
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)
        
        # Common configuration
        self.rate_limit = 5  # requests per second (override in subclasses)
        self.timeout = 30
        self.max_retries = 3
        
        # Request session with common headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'APPA/1.0 (Awesome-PHM-Paper-Agent)',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self._last_request_time = 0
        self._request_interval = 1.0 / self.rate_limit if self.rate_limit > 0 else 0
        
        # PHM-specific keywords for relevance scoring
        self.phm_keywords = {
            'core': [
                'prognostics', 'health management', 'PHM', 'condition monitoring',
                'predictive maintenance', 'fault diagnosis', 'anomaly detection',
                'failure prediction', 'reliability engineering', 'remaining useful life'
            ],
            'technical': [
                'RUL', 'degradation modeling', 'health assessment', 'system reliability',
                'maintenance optimization', 'sensor fusion', 'digital twin',
                'signal processing', 'pattern recognition', 'vibration analysis'
            ],
            'ml_methods': [
                'machine learning', 'deep learning', 'neural networks', 'CNN', 'RNN', 'LSTM',
                'support vector machine', 'random forest', 'ensemble learning',
                'transfer learning', 'unsupervised learning', 'classification'
            ],
            'applications': [
                'bearing', 'gearbox', 'turbine', 'motor', 'pump', 'valve', 'battery',
                'aircraft', 'automotive', 'wind energy', 'manufacturing', 'industrial'
            ]
        }
        
        # Excluded publishers (MDPI, predatory journals)
        self.excluded_publishers = {
            'mdpi', 'mdpi ag', 'multidisciplinary digital publishing institute',
            'hindawi', 'bentham', 'scirp', 'omics', 'frontiers media'
        }
        
    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by sleeping if necessary."""
        if self._request_interval > 0:
            time_since_last = time.time() - self._last_request_time
            if time_since_last < self._request_interval:
                sleep_time = self._request_interval - time_since_last
                time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def _make_request(self, 
                     url: str,
                     method: str = 'GET',
                     params: Optional[Dict[str, Any]] = None,
                     json_data: Optional[Dict[str, Any]] = None,
                     custom_headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request with rate limiting and error handling.
        
        Args:
            url: Request URL
            method: HTTP method ('GET' or 'POST')
            params: Query parameters
            json_data: JSON payload for POST requests
            custom_headers: Additional headers
            
        Returns:
            Parsed JSON response or None if request failed
            
        Raises:
            APIClientError: If request fails after all retries
        """
        # Retry logic
        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                self._enforce_rate_limit()
                
                # Prepare headers
                headers = self.session.headers.copy()
                if custom_headers:
                    headers.update(custom_headers)
                
                if method.upper() == 'POST':
                    response = self.session.post(
                        url, 
                        params=params, 
                        json=json_data, 
                        headers=headers, 
                        timeout=self.timeout
                    )
                else:
                    response = self.session.get(
                        url, 
                        params=params, 
                        headers=headers, 
                        timeout=self.timeout
                    )
                
                # Handle specific status codes
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise APIClientError(f"Authentication failed (401): Invalid API key")
                elif response.status_code == 403:
                    raise APIClientError(f"Access forbidden (403): Check permissions")
                elif response.status_code == 429:
                    # Rate limit - retry with exponential backoff
                    if attempt < self.max_retries:
                        wait_time = 2 ** attempt
                        self.logger.warning(f"Rate limit exceeded, waiting {wait_time}s before retry {attempt + 1}")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise APIClientError("Rate limit exceeded: max retries reached")
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {response.text[:200]}")
                    response.raise_for_status()
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt
                    self.logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"Request failed after {self.max_retries} retries: {e}")
                    raise APIClientError(f"Request failed: {e}")
                    
        return None
    
    def calculate_phm_relevance(self, paper: Dict[str, Any]) -> float:
        """
        Calculate PHM relevance score based on content analysis.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Relevance score from 0.0 to 1.0
        """
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
        
        # Calculate weighted scores for each category
        scores = {}
        weights = {
            'core': 0.4,        # Core PHM concepts most important
            'technical': 0.3,   # Technical terms moderate weight
            'ml_methods': 0.2,  # ML methods moderate weight
            'applications': 0.1 # Application domains lowest weight
        }
        
        for category, keywords in self.phm_keywords.items():
            matches = sum(1 for kw in keywords if kw.lower() in combined_text)
            total_keywords = len(keywords)
            category_score = matches / total_keywords if total_keywords > 0 else 0.0
            scores[category] = category_score
        
        # Calculate weighted average
        relevance_score = sum(scores[cat] * weights[cat] for cat in weights.keys())
        
        # Boost for high-citation papers in relevant domains
        citations = paper.get('cited_by_count', 0)
        if citations > 20 and relevance_score > 0.3:
            relevance_score = min(1.0, relevance_score * 1.2)
        
        return min(1.0, relevance_score)
    
    def is_phm_relevant(self, paper: Dict[str, Any], min_threshold: float = 0.2) -> bool:
        """
        Check if paper meets minimum PHM relevance threshold.
        
        Args:
            paper: Paper metadata dictionary
            min_threshold: Minimum relevance score required
            
        Returns:
            True if paper is PHM-relevant
        """
        relevance_score = paper.get('phm_relevance_score', 0.0)
        if relevance_score == 0.0:
            relevance_score = self.calculate_phm_relevance(paper)
            paper['phm_relevance_score'] = relevance_score
        
        return relevance_score >= min_threshold
    
    def is_excluded_publisher(self, paper: Dict[str, Any]) -> bool:
        """
        Check if paper is from an excluded publisher.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            True if publisher should be excluded
        """
        publisher = paper.get('publisher', '').lower()
        venue = paper.get('venue', '').lower()
        
        # Check publisher exclusions
        for excluded in self.excluded_publishers:
            if excluded in publisher or excluded in venue:
                return True
        
        return False
    
    def assess_data_completeness(self, paper: Dict[str, Any]) -> float:
        """
        Assess how complete the paper metadata is.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Completeness score from 0.0 to 1.0
        """
        completeness_score = 0.0
        
        # Define important fields and their weights
        field_weights = {
            'title': 0.25,
            'authors': 0.20,
            'abstract': 0.20,
            'doi': 0.10,
            'venue': 0.10,
            'year': 0.10,
            'keywords': 0.05
        }
        
        for field, weight in field_weights.items():
            value = paper.get(field)
            if value:
                if isinstance(value, str) and value.strip():
                    completeness_score += weight
                elif isinstance(value, (list, int)) and value:
                    completeness_score += weight
        
        return min(1.0, completeness_score)
    
    def apply_quality_filters(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply basic quality filters to remove low-quality papers.
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Filtered list of papers
        """
        filtered_papers = []
        current_year = datetime.now().year
        
        for paper in papers:
            # Skip if excluded publisher
            if self.is_excluded_publisher(paper):
                continue
            
            # Basic completeness checks
            if not paper.get('title') or len(paper['title']) < 10:
                continue
            
            if not paper.get('authors'):
                continue
            
            # Year filter
            year = paper.get('year')
            if year and (year < 2010 or year > current_year):
                continue
            
            # Citation filter for older papers
            citations = paper.get('cited_by_count', 0)
            if year and current_year - year > 3 and citations < 5:
                continue
            
            # PHM relevance filter
            if not self.is_phm_relevant(paper):
                continue
            
            # Add quality indicators
            paper['quality_indicators'] = {
                'data_completeness': self.assess_data_completeness(paper),
                'citations': citations,
                'is_recent': year and current_year - year <= 3,
                'has_abstract': bool(paper.get('abstract')),
                'excluded_publisher': False
            }
            
            filtered_papers.append(paper)
        
        return filtered_papers
    
    def get_basic_api_status(self) -> Dict[str, Any]:
        """
        Get basic API status information.
        Subclasses should override this method.
        
        Returns:
            Dictionary with status information
        """
        return {
            'client_type': self.__class__.__name__,
            'rate_limit': self.rate_limit,
            'timeout': self.timeout,
            'last_request_time': self._last_request_time
        }
    
    # Abstract methods that subclasses must implement
    @abstractmethod
    def search_papers(self, 
                     query: str,
                     filters: Optional[Dict[str, Any]] = None,
                     max_results: int = 50,
                     year_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
        """
        Search for papers using the specific API.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def get_api_status(self) -> Dict[str, Any]:
        """
        Check API-specific status and availability.
        Must be implemented by subclasses.
        """
        pass


if __name__ == "__main__":
    # This is a base class and cannot be instantiated directly
    print("BaseAPIClient is an abstract base class.")
    print("Use specific API client implementations instead.")