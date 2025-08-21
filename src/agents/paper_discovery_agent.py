"""
Paper Discovery Agent for APPA system.

This agent queries academic APIs and deduplicates results to discover
relevant PHM research papers.

Single Responsibility: Query academic APIs and deduplicate results
Input: Search keywords (list), date range (YYYY-YYYY), max_results_per_source (integer)
Output: JSON list of deduplicated paper metadata with relevance scores
"""

import time
import requests
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import quote
import json

from .base_agent import BaseAgent, AgentError
from ..models import PaperMetadata, PaperIdentifiers, CitationMetrics, QualityMetrics, VenueType, VenueQuartile


class PaperDiscoveryAgent(BaseAgent):
    """
    Agent responsible for discovering papers from multiple academic APIs.
    
    Implements rate limiting, deduplication, and relevance scoring.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "PaperDiscoveryAgent")
        
        # API configuration
        self.api_config = self.get_config_value('api_configuration', {})
        self.rate_limits = self.api_config.get('rate_limits', {})
        self.timeout = self.api_config.get('timeout_seconds', 30)
        self.max_retries = self.api_config.get('max_retries', 3)
        self.retry_delay = self.api_config.get('retry_delay', 2)
        self.user_agent = self.api_config.get('user_agent', 'APPA/1.0')
        
        # Search configuration
        self.search_config = self.get_config_value('search_parameters', {})
        
        # Initialize API clients
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        
        # Rate limiting tracking
        self.last_request_time: Dict[str, float] = {}
        
        # Deduplication tracking
        self.seen_dois: Set[str] = set()
        self.seen_fingerprints: Set[str] = set()
    
    def process(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Discover papers from academic APIs.
        
        Args:
            input_data: Dictionary containing:
                - keywords: List of search keywords
                - date_range: String in format "YYYY-YYYY"
                - max_results_per_source: Maximum results per API
                - incremental_date: Optional cutoff date for incremental updates
        
        Returns:
            List of deduplicated paper metadata dictionaries with relevance scores
        """
        keywords = input_data.get('keywords', [])
        date_range = input_data.get('date_range', '')
        max_results = input_data.get('max_results_per_source', 100)
        incremental_date = input_data.get('incremental_date')
        
        if not keywords:
            raise AgentError("Keywords are required for paper discovery")
        
        self.logger.info(f"Starting paper discovery with {len(keywords)} keywords")
        
        # Parse date range
        start_year, end_year = self._parse_date_range(date_range)
        
        # Collect papers from all sources
        all_papers = []
        
        # Query OpenAlex
        try:
            openalex_papers = self._query_openalex(keywords, start_year, end_year, max_results)
            all_papers.extend(openalex_papers)
            self.logger.info(f"Found {len(openalex_papers)} papers from OpenAlex")
        except Exception as e:
            self.logger.error(f"OpenAlex query failed: {e}")
        
        # Query Semantic Scholar
        try:
            semantic_papers = self._query_semantic_scholar(keywords, start_year, end_year, max_results)
            all_papers.extend(semantic_papers)
            self.logger.info(f"Found {len(semantic_papers)} papers from Semantic Scholar")
        except Exception as e:
            self.logger.error(f"Semantic Scholar query failed: {e}")
        
        # Query arXiv
        try:
            arxiv_papers = self._query_arxiv(keywords, start_year, end_year, max_results)
            all_papers.extend(arxiv_papers)
            self.logger.info(f"Found {len(arxiv_papers)} papers from arXiv")
        except Exception as e:
            self.logger.error(f"arXiv query failed: {e}")
        
        # Deduplicate papers
        deduplicated_papers = self._deduplicate_papers(all_papers)
        
        # Filter by incremental date if specified
        if incremental_date:
            deduplicated_papers = self._filter_by_date(deduplicated_papers, incremental_date)
        
        # Calculate relevance scores
        scored_papers = self._calculate_relevance_scores(deduplicated_papers, keywords)
        
        # Sort by relevance score
        scored_papers.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        self.logger.info(f"Discovered {len(scored_papers)} unique papers after deduplication")
        
        return scored_papers
    
    def _parse_date_range(self, date_range: str) -> tuple[int, int]:
        """Parse date range string into start and end years."""
        try:
            start_year, end_year = map(int, date_range.split('-'))
            return start_year, end_year
        except ValueError:
            raise AgentError(f"Invalid date range format: {date_range}")
    
    def _rate_limit(self, api_name: str) -> None:
        """Apply rate limiting for API requests."""
        if api_name not in self.rate_limits:
            return
        
        min_interval = 1.0 / self.rate_limits[api_name]
        last_request = self.last_request_time.get(api_name, 0)
        elapsed = time.time() - last_request
        
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time[api_name] = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any], api_name: str) -> Dict[str, Any]:
        """Make HTTP request with rate limiting and retries."""
        for attempt in range(self.max_retries):
            try:
                self._rate_limit(api_name)
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise AgentError(f"Request failed after {self.max_retries} attempts: {e}")
                time.sleep(self.retry_delay * (attempt + 1))
        
        return {}

    def _query_openalex(self, keywords: List[str], start_year: int, end_year: int, max_results: int) -> List[Dict[str, Any]]:
        """Query OpenAlex API for papers."""
        base_url = "https://api.openalex.org/works"

        # Build search query
        query_parts = []
        for keyword in keywords:
            query_parts.append(f'"{keyword}"')
        search_query = ' OR '.join(query_parts)

        params = {
            'search': search_query,
            'filter': f'publication_year:{start_year}-{end_year},type:article',
            'per-page': min(max_results, 200),  # OpenAlex max per page
            'sort': 'cited_by_count:desc',
            'select': 'id,title,authorships,publication_year,primary_location,doi,abstract_inverted_index,cited_by_count,keywords'
        }

        papers = []
        page = 1

        while len(papers) < max_results:
            params['page'] = page

            try:
                data = self._make_request(base_url, params, 'openalex')
                results = data.get('results', [])

                if not results:
                    break

                for work in results:
                    paper = self._parse_openalex_paper(work)
                    if paper:
                        papers.append(paper)

                page += 1

            except Exception as e:
                self.logger.error(f"Error querying OpenAlex page {page}: {e}")
                break

        return papers[:max_results]

    def _parse_openalex_paper(self, work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse OpenAlex work data into standardized format."""
        try:
            # Extract basic information
            title = work.get('title', '').strip()
            if not title:
                return None

            # Extract authors
            authors = []
            affiliations = []
            authorships = work.get('authorships', [])
            for authorship in authorships:
                author = authorship.get('author', {})
                display_name = author.get('display_name', '')
                if display_name:
                    authors.append(display_name)

                # Extract affiliations
                for institution in authorship.get('institutions', []):
                    inst_name = institution.get('display_name', '')
                    if inst_name and inst_name not in affiliations:
                        affiliations.append(inst_name)

            # Extract venue information
            primary_location = work.get('primary_location', {})
            source = primary_location.get('source', {})
            venue = source.get('display_name', 'Unknown Venue')
            venue_type = source.get('type', 'journal')

            # Determine venue type
            if venue_type == 'journal':
                paper_type = VenueType.JOURNAL
            elif venue_type in ['conference', 'proceedings']:
                paper_type = VenueType.CONFERENCE
            else:
                paper_type = VenueType.JOURNAL  # Default

            # Extract identifiers
            doi = work.get('doi', '').replace('https://doi.org/', '') if work.get('doi') else None
            openalex_id = work.get('id', '')

            # Build URLs
            urls = {
                'openalex': openalex_id,
                'publisher': primary_location.get('landing_page_url', ''),
                'pdf': primary_location.get('pdf_url', ''),
                'google_scholar': f"https://scholar.google.com/scholar?q={quote(title)}"
            }

            # Extract abstract (OpenAlex uses inverted index)
            abstract = self._reconstruct_abstract(work.get('abstract_inverted_index', {}))

            # Extract keywords
            keywords = []
            for concept in work.get('concepts', []):
                if concept.get('score', 0) > 0.3:  # Only high-confidence concepts
                    keywords.append(concept.get('display_name', '').lower())

            # Add PHM-specific keywords if found in title/abstract
            phm_keywords = self._extract_phm_keywords(title + ' ' + abstract)
            keywords.extend(phm_keywords)

            return {
                'title': title,
                'authors': authors,
                'affiliations': affiliations,
                'year': work.get('publication_year', 0),
                'venue': venue,
                'type': paper_type.value,
                'doi': doi,
                'urls': urls,
                'abstract': abstract,
                'keywords': list(set(keywords))[:10],  # Limit to 10 keywords
                'citation_count': work.get('cited_by_count', 0),
                'source': 'openalex'
            }

        except Exception as e:
            self.logger.error(f"Error parsing OpenAlex paper: {e}")
            return None

    def _reconstruct_abstract(self, inverted_index: Dict[str, List[int]]) -> str:
        """Reconstruct abstract from OpenAlex inverted index."""
        if not inverted_index:
            return ""

        # Create word position mapping
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))

        # Sort by position and reconstruct
        word_positions.sort(key=lambda x: x[0])
        return ' '.join([word for _, word in word_positions])

    def _extract_phm_keywords(self, text: str) -> List[str]:
        """Extract PHM-specific keywords from text."""
        text_lower = text.lower()
        phm_terms = [
            'prognostics', 'health management', 'fault diagnosis', 'condition monitoring',
            'predictive maintenance', 'remaining useful life', 'rul', 'anomaly detection',
            'failure prediction', 'degradation', 'reliability', 'maintenance', 'diagnosis',
            'prognosis', 'health assessment', 'system health', 'fault detection'
        ]

        found_keywords = []
        for term in phm_terms:
            if term in text_lower:
                found_keywords.append(term)

        return found_keywords

    def _query_semantic_scholar(self, keywords: List[str], start_year: int, end_year: int, max_results: int) -> List[Dict[str, Any]]:
        """Query Semantic Scholar API for papers."""
        base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

        # Build search query
        search_query = ' OR '.join([f'"{keyword}"' for keyword in keywords])

        params = {
            'query': search_query,
            'year': f'{start_year}-{end_year}',
            'limit': min(max_results, 100),  # Semantic Scholar max per request
            'fields': 'paperId,title,authors,year,venue,abstract,citationCount,url,externalIds'
        }

        papers = []
        offset = 0

        while len(papers) < max_results:
            params['offset'] = offset

            try:
                data = self._make_request(base_url, params, 'semantic_scholar')
                results = data.get('data', [])

                if not results:
                    break

                for paper_data in results:
                    paper = self._parse_semantic_scholar_paper(paper_data)
                    if paper:
                        papers.append(paper)

                offset += len(results)

                # Check if we've reached the end
                if len(results) < params['limit']:
                    break

            except Exception as e:
                self.logger.error(f"Error querying Semantic Scholar at offset {offset}: {e}")
                break

        return papers[:max_results]

    def _parse_semantic_scholar_paper(self, paper_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Semantic Scholar paper data into standardized format."""
        try:
            title = paper_data.get('title', '').strip()
            if not title:
                return None

            # Extract authors
            authors = []
            affiliations = []
            for author in paper_data.get('authors', []):
                name = author.get('name', '')
                if name:
                    authors.append(name)

                # Semantic Scholar doesn't always provide affiliations
                # We'll extract them from author data if available
                for affiliation in author.get('affiliations', []):
                    aff_name = affiliation.get('name', '')
                    if aff_name and aff_name not in affiliations:
                        affiliations.append(aff_name)

            # Extract identifiers
            external_ids = paper_data.get('externalIds', {})
            doi = external_ids.get('DOI')
            arxiv_id = external_ids.get('ArXiv')

            # Build URLs
            urls = {
                'semantic_scholar': f"https://www.semanticscholar.org/paper/{paper_data.get('paperId', '')}",
                'publisher': paper_data.get('url', ''),
                'pdf': '',  # Semantic Scholar doesn't provide direct PDF links
                'google_scholar': f"https://scholar.google.com/scholar?q={quote(title)}"
            }

            # Extract abstract
            abstract = paper_data.get('abstract', '') or ''

            # Extract keywords from title and abstract
            keywords = self._extract_phm_keywords(title + ' ' + abstract)

            # Determine venue type (Semantic Scholar doesn't clearly distinguish)
            venue = paper_data.get('venue', 'Unknown Venue')
            paper_type = VenueType.JOURNAL  # Default assumption

            return {
                'title': title,
                'authors': authors,
                'affiliations': affiliations,
                'year': paper_data.get('year', 0),
                'venue': venue,
                'type': paper_type.value,
                'doi': doi,
                'arxiv': arxiv_id,
                'urls': urls,
                'abstract': abstract,
                'keywords': keywords,
                'citation_count': paper_data.get('citationCount', 0),
                'source': 'semantic_scholar'
            }

        except Exception as e:
            self.logger.error(f"Error parsing Semantic Scholar paper: {e}")
            return None

    def _query_arxiv(self, keywords: List[str], start_year: int, end_year: int, max_results: int) -> List[Dict[str, Any]]:
        """Query arXiv API for papers."""
        base_url = "http://export.arxiv.org/api/query"

        # Build search query for arXiv
        search_terms = []
        for keyword in keywords:
            # Search in title, abstract, and subject class
            search_terms.append(f'(ti:"{keyword}" OR abs:"{keyword}")')

        search_query = ' OR '.join(search_terms)

        params = {
            'search_query': search_query,
            'start': 0,
            'max_results': min(max_results, 1000),  # arXiv allows up to 1000
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        try:
            # arXiv returns XML, so we need to parse it differently
            response = self.session.get(base_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            papers = self._parse_arxiv_xml(response.text, start_year, end_year)
            return papers[:max_results]

        except Exception as e:
            self.logger.error(f"Error querying arXiv: {e}")
            return []

    def _parse_arxiv_xml(self, xml_content: str, start_year: int, end_year: int) -> List[Dict[str, Any]]:
        """Parse arXiv XML response into standardized format."""
        try:
            import xml.etree.ElementTree as ET

            root = ET.fromstring(xml_content)
            papers = []

            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }

            for entry in root.findall('atom:entry', namespaces):
                paper = self._parse_arxiv_entry(entry, namespaces, start_year, end_year)
                if paper:
                    papers.append(paper)

            return papers

        except Exception as e:
            self.logger.error(f"Error parsing arXiv XML: {e}")
            return []

    def _parse_arxiv_entry(self, entry, namespaces: Dict[str, str], start_year: int, end_year: int) -> Optional[Dict[str, Any]]:
        """Parse individual arXiv entry."""
        try:
            import xml.etree.ElementTree as ET

            # Extract title
            title_elem = entry.find('atom:title', namespaces)
            title = title_elem.text.strip() if title_elem is not None else ''
            if not title:
                return None

            # Extract publication date and filter by year
            published_elem = entry.find('atom:published', namespaces)
            if published_elem is not None:
                pub_date = published_elem.text
                pub_year = int(pub_date[:4])
                if pub_year < start_year or pub_year > end_year:
                    return None
            else:
                pub_year = 0

            # Extract authors
            authors = []
            for author_elem in entry.findall('atom:author', namespaces):
                name_elem = author_elem.find('atom:name', namespaces)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())

            # Extract arXiv ID
            id_elem = entry.find('atom:id', namespaces)
            arxiv_url = id_elem.text if id_elem is not None else ''
            arxiv_id = arxiv_url.split('/')[-1] if arxiv_url else ''

            # Extract abstract
            summary_elem = entry.find('atom:summary', namespaces)
            abstract = summary_elem.text.strip() if summary_elem is not None else ''

            # Extract categories (used as keywords)
            categories = []
            for category_elem in entry.findall('atom:category', namespaces):
                term = category_elem.get('term', '')
                if term:
                    categories.append(term)

            # Extract PHM keywords
            keywords = self._extract_phm_keywords(title + ' ' + abstract)
            keywords.extend(categories)

            # Build URLs
            urls = {
                'arxiv': arxiv_url,
                'pdf': arxiv_url.replace('/abs/', '/pdf/') + '.pdf' if arxiv_url else '',
                'publisher': arxiv_url,
                'google_scholar': f"https://scholar.google.com/scholar?q={quote(title)}"
            }

            return {
                'title': title,
                'authors': authors,
                'affiliations': [],  # arXiv doesn't provide affiliations in API
                'year': pub_year,
                'venue': 'arXiv',
                'type': VenueType.PREPRINT.value,
                'doi': None,
                'arxiv': arxiv_id,
                'urls': urls,
                'abstract': abstract,
                'keywords': list(set(keywords))[:10],
                'citation_count': 0,  # arXiv doesn't provide citation counts
                'source': 'arxiv'
            }

        except Exception as e:
            self.logger.error(f"Error parsing arXiv entry: {e}")
            return None

    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate papers using DOI and title+author fingerprinting."""
        unique_papers = []

        for paper in papers:
            # Check DOI-based deduplication first
            doi = paper.get('doi')
            if doi and doi in self.seen_dois:
                continue

            # Create fingerprint for title+author deduplication
            fingerprint = self._create_paper_fingerprint(paper)
            if fingerprint in self.seen_fingerprints:
                continue

            # Add to unique papers
            unique_papers.append(paper)

            # Track for future deduplication
            if doi:
                self.seen_dois.add(doi)
            self.seen_fingerprints.add(fingerprint)

        return unique_papers

    def _create_paper_fingerprint(self, paper: Dict[str, Any]) -> str:
        """Create a fingerprint for paper deduplication."""
        # Normalize title
        title = paper.get('title', '').lower().strip()
        title = ''.join(c for c in title if c.isalnum() or c.isspace())
        title = ' '.join(title.split())  # Normalize whitespace

        # Get first author's last name
        authors = paper.get('authors', [])
        first_author = ''
        if authors:
            first_author = authors[0].lower().strip()
            if ',' in first_author:
                first_author = first_author.split(',')[0]
            else:
                parts = first_author.split()
                first_author = parts[-1] if parts else ''

        # Create fingerprint
        fingerprint_text = f"{title}|{first_author}|{paper.get('year', 0)}"
        return hashlib.md5(fingerprint_text.encode('utf-8')).hexdigest()

    def _filter_by_date(self, papers: List[Dict[str, Any]], cutoff_date: str) -> List[Dict[str, Any]]:
        """Filter papers by publication date for incremental updates."""
        try:
            cutoff = datetime.fromisoformat(cutoff_date)
            cutoff_year = cutoff.year

            filtered_papers = []
            for paper in papers:
                paper_year = paper.get('year', 0)
                if paper_year >= cutoff_year:
                    filtered_papers.append(paper)

            return filtered_papers

        except ValueError:
            self.logger.error(f"Invalid cutoff date format: {cutoff_date}")
            return papers

    def _calculate_relevance_scores(self, papers: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
        """Calculate relevance scores for papers."""
        keyword_set = set(kw.lower() for kw in keywords)

        for paper in papers:
            score = 0.0

            # Title relevance (weight: 0.4)
            title_words = set(paper.get('title', '').lower().split())
            title_matches = len(keyword_set.intersection(title_words))
            title_score = min(title_matches / len(keyword_set), 1.0) * 0.4

            # Abstract relevance (weight: 0.3)
            abstract_words = set(paper.get('abstract', '').lower().split())
            abstract_matches = len(keyword_set.intersection(abstract_words))
            abstract_score = min(abstract_matches / len(keyword_set), 1.0) * 0.3

            # Keyword relevance (weight: 0.2)
            paper_keywords = set(paper.get('keywords', []))
            keyword_matches = len(keyword_set.intersection(paper_keywords))
            keyword_score = min(keyword_matches / len(keyword_set), 1.0) * 0.2

            # Citation impact (weight: 0.1)
            citation_count = paper.get('citation_count', 0)
            citation_score = min(citation_count / 100, 1.0) * 0.1  # Normalize to 100 citations

            # Combine scores
            total_score = title_score + abstract_score + keyword_score + citation_score
            paper['relevance_score'] = round(total_score, 3)

        return papers


if __name__ == "__main__":
    # Test the agent
    config = {
        'api_configuration': {
            'rate_limits': {'openalex': 10, 'semantic_scholar': 1},
            'timeout_seconds': 30
        }
    }
    
    agent = PaperDiscoveryAgent(config)
    
    test_input = {
        'keywords': ['prognostics', 'health management'],
        'date_range': '2023-2024',
        'max_results_per_source': 5
    }
    
    print("Testing Paper Discovery Agent...")
    # Note: Actual API calls would be made here in a real test
