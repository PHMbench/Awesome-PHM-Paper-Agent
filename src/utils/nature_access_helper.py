"""
Nature Access Helper - Specialized handler for Nature series publications.

This module provides optimized access strategies for Nature series journals
including proper headers, rate limiting, and fallback mechanisms.

Created: 2025-08-23
"""

import time
import requests
import random
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class NatureAccessHelper:
    """
    Specialized helper for accessing Nature series publications.
    
    Handles the unique requirements and restrictions of Nature's platforms.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Nature access helper with optimized settings."""
        self.config = config or {}
        
        # Nature-specific configuration
        self.nature_domains = {
            'nature.com',
            'www.nature.com', 
            'link.springer.com',
            'rdcu.be'  # Nature sharing links
        }
        
        # Optimized headers for Nature
        self.nature_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        # Rate limiting for Nature
        self.last_request_time = 0
        self.min_delay = 3.0  # Minimum 3 seconds between requests
        self.max_retries = 2  # Limited retries to avoid blocking
        
        # Session with optimized settings
        self.session = requests.Session()
        self.session.headers.update(self.nature_headers)
        
    def is_nature_url(self, url: str) -> bool:
        """Check if URL belongs to Nature series."""
        try:
            domain = urlparse(url).netloc.lower()
            return any(nature_domain in domain for nature_domain in self.nature_domains)
        except:
            return False
    
    def get_nature_paper_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to retrieve paper information from Nature URL.
        
        Uses multiple strategies to maximize success rate while respecting
        Nature's terms of service.
        """
        if not self.is_nature_url(url):
            return None
            
        logger.info(f"Attempting Nature access: {url}")
        
        # Strategy 1: Try direct access with proper headers
        result = self._try_direct_access(url)
        if result:
            return result
            
        # Strategy 2: Try DOI resolution if URL contains DOI
        if '10.1038' in url:
            doi_result = self._try_doi_resolution(url)
            if doi_result:
                return doi_result
        
        # Strategy 3: Try alternative access methods
        alt_result = self._try_alternative_access(url)
        if alt_result:
            return alt_result
            
        logger.warning(f"All Nature access strategies failed for: {url}")
        return self._create_limited_metadata(url)
    
    def _try_direct_access(self, url: str) -> Optional[Dict[str, Any]]:
        """Try direct access to Nature URL with optimized headers."""
        try:
            # Respect rate limiting
            self._wait_for_rate_limit()
            
            response = self.session.get(
                url, 
                timeout=30,
                allow_redirects=True
            )
            
            # Update last request time
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                # Extract basic metadata from HTML
                return self._extract_metadata_from_html(response.text, url)
            elif response.status_code == 403:
                logger.warning(f"Nature access forbidden (403) for: {url}")
                return None
            elif response.status_code == 429:
                logger.warning(f"Nature rate limit exceeded (429) for: {url}")
                # Wait longer before next attempt
                time.sleep(10)
                return None
            else:
                logger.warning(f"Nature returned {response.status_code} for: {url}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Nature direct access failed: {e}")
            return None
    
    def _try_doi_resolution(self, url: str) -> Optional[Dict[str, Any]]:
        """Try accessing via DOI resolution services."""
        try:
            # Extract DOI from URL
            doi = self._extract_doi_from_url(url)
            if not doi:
                return None
                
            # Try dx.doi.org resolution
            doi_url = f"https://dx.doi.org/{doi}"
            
            self._wait_for_rate_limit()
            
            # Request with accept header for metadata
            headers = self.nature_headers.copy()
            headers['Accept'] = 'application/vnd.citationstyles.csl+json'
            
            response = self.session.get(doi_url, headers=headers, timeout=20)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                try:
                    # Parse JSON metadata
                    metadata = response.json()
                    return self._convert_doi_metadata(metadata, doi)
                except:
                    # Fallback to HTML parsing
                    return self._extract_metadata_from_html(response.text, url)
            else:
                logger.warning(f"DOI resolution failed with {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"DOI resolution error: {e}")
            return None
    
    def _try_alternative_access(self, url: str) -> Optional[Dict[str, Any]]:
        """Try alternative access methods for Nature papers."""
        try:
            # Check for sharing links or alternative URLs
            if 'rdcu.be' in url:
                # Nature ReadCube sharing link - often more accessible
                return self._try_direct_access(url)
            
            # Try to find alternative access via CrossRef
            if '10.1038' in url:
                doi = self._extract_doi_from_url(url)
                if doi:
                    crossref_result = self._try_crossref_metadata(doi)
                    if crossref_result:
                        return crossref_result
            
            return None
            
        except Exception as e:
            logger.error(f"Alternative access failed: {e}")
            return None
    
    def _try_crossref_metadata(self, doi: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata from CrossRef API."""
        try:
            self._wait_for_rate_limit()
            
            crossref_url = f"https://api.crossref.org/works/{doi}"
            headers = {
                'User-Agent': 'APPA-Research/1.0 (mailto:research@example.com)',
                'Accept': 'application/json'
            }
            
            response = requests.get(crossref_url, headers=headers, timeout=15)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                work = data.get('message', {})
                
                return {
                    'title': ' '.join(work.get('title', [])),
                    'authors': self._extract_crossref_authors(work.get('author', [])),
                    'journal': work.get('container-title', ['Unknown'])[0] if work.get('container-title') else 'Unknown',
                    'year': self._extract_crossref_year(work.get('published-print', work.get('published-online', {}))),
                    'doi': doi,
                    'abstract': work.get('abstract', ''),
                    'url': f"https://doi.org/{doi}",
                    'access_method': 'crossref',
                    'access_status': 'metadata_only'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"CrossRef metadata retrieval failed: {e}")
            return None
    
    def _extract_doi_from_url(self, url: str) -> Optional[str]:
        """Extract DOI from Nature URL."""
        try:
            import re
            
            # Common Nature DOI patterns
            patterns = [
                r'10\.1038/[a-zA-Z0-9.-]+',
                r'doi\.org/(10\.1038/[a-zA-Z0-9.-]+)',
                r'/articles/(10\.1038/[a-zA-Z0-9.-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    doi = match.group(1) if match.groups() else match.group(0)
                    return doi.replace('doi.org/', '')
            
            return None
            
        except Exception:
            return None
    
    def _extract_metadata_from_html(self, html: str, url: str) -> Optional[Dict[str, Any]]:
        """Extract paper metadata from Nature HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = None
            title_selectors = [
                'h1[data-test="article-title"]',
                'h1.c-article-title',
                'h1',
                'title'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            # Extract authors
            authors = []
            author_selectors = [
                '[data-test="author-name"]',
                '.c-article-author-list a',
                '.author-list a'
            ]
            
            for selector in author_selectors:
                author_elems = soup.select(selector)
                if author_elems:
                    authors = [elem.get_text(strip=True) for elem in author_elems]
                    break
            
            # Extract abstract
            abstract = ""
            abstract_selectors = [
                '[data-test="article-description"]',
                '.c-article-section--abstract',
                '.abstract'
            ]
            
            for selector in abstract_selectors:
                abstract_elem = soup.select_one(selector)
                if abstract_elem:
                    abstract = abstract_elem.get_text(strip=True)
                    break
            
            # Extract DOI
            doi = ""
            doi_elem = soup.select_one('[data-track-label="doi"]')
            if doi_elem:
                doi = doi_elem.get_text(strip=True)
            
            return {
                'title': title or 'Nature Article',
                'authors': authors,
                'abstract': abstract,
                'doi': doi,
                'url': url,
                'journal': 'Nature Series',
                'access_method': 'html_scraping',
                'access_status': 'partial_success'
            }
            
        except Exception as e:
            logger.error(f"HTML metadata extraction failed: {e}")
            return None
    
    def _create_limited_metadata(self, url: str) -> Dict[str, Any]:
        """Create limited metadata when direct access fails."""
        doi = self._extract_doi_from_url(url)
        
        return {
            'title': 'Nature Article (Access Limited)',
            'authors': [],
            'abstract': 'Full text access restricted. This appears to be a Nature series publication.',
            'doi': doi or '',
            'url': url,
            'journal': 'Nature Series',
            'access_method': 'limited',
            'access_status': 'restricted',
            'note': 'Full text access may require institutional subscription or payment.'
        }
    
    def _wait_for_rate_limit(self):
        """Implement respectful rate limiting for Nature requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            wait_time = self.min_delay - time_since_last
            # Add some random jitter to avoid synchronized requests
            wait_time += random.uniform(0, 1)
            time.sleep(wait_time)
    
    def _extract_crossref_authors(self, authors: List[Dict]) -> List[str]:
        """Extract author names from CrossRef data."""
        result = []
        for author in authors:
            given = author.get('given', '')
            family = author.get('family', '')
            if given and family:
                result.append(f"{given} {family}")
            elif family:
                result.append(family)
        return result
    
    def _extract_crossref_year(self, date_parts: Dict) -> Optional[int]:
        """Extract year from CrossRef date information."""
        try:
            if 'date-parts' in date_parts and date_parts['date-parts']:
                return date_parts['date-parts'][0][0]
        except:
            pass
        return None
    
    def _convert_doi_metadata(self, metadata: Dict, doi: str) -> Dict[str, Any]:
        """Convert DOI metadata to standard format."""
        return {
            'title': metadata.get('title', 'Unknown Title'),
            'authors': [author.get('literal', '') for author in metadata.get('author', [])],
            'journal': metadata.get('container-title', 'Unknown Journal'),
            'year': metadata.get('issued', {}).get('date-parts', [[None]])[0][0],
            'doi': doi,
            'abstract': metadata.get('abstract', ''),
            'access_method': 'doi_metadata',
            'access_status': 'metadata_available'
        }


# Usage example and integration function
def get_nature_paper_safely(url: str, config: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
    """
    Safe wrapper function to get Nature paper information.
    
    This function can be used by other modules to access Nature content
    with appropriate error handling and rate limiting.
    """
    try:
        helper = NatureAccessHelper(config)
        
        if not helper.is_nature_url(url):
            return None
            
        result = helper.get_nature_paper_info(url)
        
        if result:
            logger.info(f"Successfully retrieved Nature paper: {result.get('title', 'Unknown')}")
        else:
            logger.warning(f"Failed to retrieve Nature paper from: {url}")
            
        return result
        
    except Exception as e:
        logger.error(f"Nature access error: {e}")
        return None


if __name__ == "__main__":
    # Test the Nature access helper
    test_urls = [
        "https://www.nature.com/articles/s41586-024-07123-4",
        "https://doi.org/10.1038/nature12345"
    ]
    
    for url in test_urls:
        print(f"\nTesting: {url}")
        result = get_nature_paper_safely(url)
        if result:
            print(f"✅ Success: {result.get('title', 'Unknown')}")
            print(f"   Method: {result.get('access_method', 'unknown')}")
            print(f"   Status: {result.get('access_status', 'unknown')}")
        else:
            print(f"❌ Failed to access")