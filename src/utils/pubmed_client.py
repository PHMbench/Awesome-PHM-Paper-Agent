"""
PubMed & Europe PMC API Client for APPA System

This client integrates with both PubMed E-utilities and Europe PMC REST API
for comprehensive biomedical and life sciences paper discovery.
Particularly strong for Nature/Science/Cell publications and biomedical PHM applications.

PubMed: https://www.ncbi.nlm.nih.gov/books/NBK25501/
Europe PMC: https://europepmc.org/docs/EBI_Europe_PMC_Web_Service_Reference.pdf
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from urllib.parse import quote
import requests
from xml.etree import ElementTree as ET
from tenacity import retry, stop_after_attempt, wait_exponential

from .logging_config import get_logger


class PubMedClient:
    """
    Dual PubMed/Europe PMC client for biomedical and life sciences papers.
    
    Features:
    - PubMed E-utilities for MEDLINE/PubMed database
    - Europe PMC REST API for broader European coverage  
    - Excellent abstract coverage
    - Strong coverage of high-impact journals (Nature, Science, Cell)
    - No API keys required (but email recommended)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # API Endpoints
        self.pubmed_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.europepmc_base_url = "https://www.ebi.ac.uk/europepmc/webservices/rest"
        
        # Configuration
        self.email = os.environ.get('EUROPEPMC_EMAIL', '')
        self.rate_limit = 3  # requests per second (NCBI recommendation: 3/sec with email)
        
        # Request headers
        self.headers = {
            'User-Agent': 'APPA/1.0 (Awesome-PHM-Paper-Agent; academic-research)',
            'Accept': 'application/json'
        }
        
        # PHM-related MeSH terms and keywords for biomedical search
        self.phm_mesh_terms = [
            'Equipment Failure Analysis',
            'Predictive Value of Tests', 
            'Monitoring, Physiologic',
            'Diagnostic Techniques and Procedures',
            'Quality Control',
            'Risk Assessment',
            'Artificial Intelligence',
            'Machine Learning',
            'Signal Processing, Computer-Assisted',
            'Pattern Recognition, Automated'
        ]
        
        # Biomedical PHM keywords
        self.biomedical_phm_keywords = {
            'medical_devices': [
                'medical device', 'biomedical equipment', 'diagnostic equipment',
                'monitoring system', 'sensor system', 'wearable device'
            ],
            'predictive': [
                'predictive maintenance', 'predictive analytics', 'prognostics',
                'health monitoring', 'condition monitoring', 'fault prediction'
            ],
            'reliability': [
                'equipment reliability', 'system reliability', 'failure analysis',
                'risk assessment', 'quality control', 'safety monitoring'
            ],
            'ai_methods': [
                'machine learning', 'artificial intelligence', 'deep learning',
                'neural network', 'pattern recognition', 'signal processing'
            ]
        }
        
        # Target high-impact journals
        self.target_journals = {
            'nature', 'science', 'cell', 'nature medicine', 'nature biotechnology',
            'science translational medicine', 'cell metabolism', 'nature methods',
            'proceedings of the national academy of sciences', 'pnas'
        }
        
        self.logger.info("PubMed/Europe PMC client initialized")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Any]:
        """Make rate-limited request to PubMed/Europe PMC APIs."""
        
        try:
            # Rate limiting
            time.sleep(1.0 / self.rate_limit)
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            # Return JSON for Europe PMC, text for PubMed
            if 'europepmc' in url:
                return response.json()
            else:
                return response.text
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            return None
    
    def search_papers(self,
                     query: str,
                     filters: Optional[Dict[str, Any]] = None,
                     max_results: int = 50,
                     year_range: Optional[Tuple[int, int]] = None) -> List[Dict[str, Any]]:
        """
        Search for biomedical PHM papers using both PubMed and Europe PMC.
        
        Args:
            query: Search query string
            filters: Additional filters
            max_results: Maximum number of results
            year_range: Tuple of (start_year, end_year)
            
        Returns:
            List of paper metadata dictionaries
        """
        self.logger.info(f"Searching PubMed/Europe PMC for: {query}")
        
        # Search both databases
        pubmed_papers = self._search_pubmed(query, filters, max_results // 2, year_range)
        europepmc_papers = self._search_europepmc(query, filters, max_results // 2, year_range)
        
        # Combine and deduplicate
        all_papers = pubmed_papers + europepmc_papers
        unique_papers = self._deduplicate_papers(all_papers)
        
        # Apply PHM relevance filtering
        phm_papers = [p for p in unique_papers if self._is_phm_relevant(p)]
        
        # Apply quality filters
        filtered_papers = self._apply_quality_filters(phm_papers)
        
        # Sort by relevance and citations
        filtered_papers.sort(key=self._calculate_paper_score, reverse=True)
        
        self.logger.info(f"Found {len(filtered_papers)} biomedical PHM papers")
        return filtered_papers[:max_results]
    
    def _search_pubmed(self,
                      query: str,
                      filters: Optional[Dict[str, Any]],
                      max_results: int,
                      year_range: Optional[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """Search PubMed using E-utilities."""
        
        # Build enhanced query with PHM context
        enhanced_query = self._build_pubmed_query(query, year_range)
        
        # Step 1: Search for PMIDs
        search_params = {
            'db': 'pubmed',
            'term': enhanced_query,
            'retmax': max_results,
            'sort': 'relevance'
        }
        
        if self.email:
            search_params['email'] = self.email
        
        search_url = f"{self.pubmed_base_url}/esearch.fcgi"
        search_response = self._make_request(search_url, search_params)
        
        if not search_response:
            return []
        
        # Parse PMIDs from XML
        pmids = self._parse_pubmed_search_results(search_response)
        if not pmids:
            return []
        
        # Step 2: Fetch detailed information for PMIDs
        fetch_params = {
            'db': 'pubmed',
            'id': ','.join(pmids[:max_results]),
            'retmode': 'xml',
            'rettype': 'abstract'
        }
        
        if self.email:
            fetch_params['email'] = self.email
        
        fetch_url = f"{self.pubmed_base_url}/efetch.fcgi"
        fetch_response = self._make_request(fetch_url, fetch_params)
        
        if not fetch_response:
            return []
        
        # Parse paper details from XML
        papers = self._parse_pubmed_fetch_results(fetch_response)
        
        return papers
    
    def _search_europepmc(self,
                         query: str, 
                         filters: Optional[Dict[str, Any]],
                         max_results: int,
                         year_range: Optional[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """Search Europe PMC using REST API."""
        
        # Build query with PHM terms
        enhanced_query = self._build_europepmc_query(query, year_range, filters)
        
        params = {
            'query': enhanced_query,
            'format': 'json',
            'resultType': 'core',
            'pageSize': min(max_results, 100),  # Europe PMC limit
            'sort': 'CITED desc'  # Most cited first
        }
        
        response_data = self._make_request(f"{self.europepmc_base_url}/search", params)
        if not response_data:
            return []
        
        papers = []
        for result in response_data.get('resultList', {}).get('result', []):
            try:
                paper = self._convert_europepmc_result_to_paper(result)
                if paper:
                    papers.append(paper)
            except Exception as e:
                self.logger.warning(f"Failed to process Europe PMC result: {e}")
                continue
        
        return papers
    
    def _build_pubmed_query(self, query: str, year_range: Optional[Tuple[int, int]]) -> str:
        """Build enhanced PubMed query with MeSH terms and filters."""
        
        # Start with base query
        query_parts = [f"({query})"]
        
        # Add PHM-related MeSH terms
        mesh_terms = []
        for term in self.phm_mesh_terms[:5]:  # Limit to avoid overly complex query
            mesh_terms.append(f'"{term}"[MeSH Terms]')
        
        if mesh_terms:
            query_parts.append(f"({' OR '.join(mesh_terms)})")
        
        # Add biomedical PHM keywords
        keyword_parts = []
        for category, keywords in self.biomedical_phm_keywords.items():
            category_terms = []
            for keyword in keywords[:3]:  # Limit per category
                category_terms.append(f'"{keyword}"')
            if category_terms:
                keyword_parts.append(f"({' OR '.join(category_terms)})")
        
        if keyword_parts:
            query_parts.append(f"({' OR '.join(keyword_parts)})")
        
        # Combine with OR
        enhanced_query = ' OR '.join(query_parts)
        
        # Add publication date filter
        if year_range:
            start_year, end_year = year_range
            enhanced_query += f' AND ("{start_year}"[Date - Publication] : "{end_year}"[Date - Publication])'
        
        # Add language filter
        enhanced_query += ' AND English[Language]'
        
        return enhanced_query
    
    def _build_europepmc_query(self, 
                              query: str,
                              year_range: Optional[Tuple[int, int]],
                              filters: Optional[Dict[str, Any]]) -> str:
        """Build Europe PMC query string."""
        
        # Base query with PHM enhancement
        enhanced_query = f"{query} AND (predictive OR maintenance OR monitoring OR diagnostic OR reliability)"
        
        # Add year filter
        if year_range:
            start_year, end_year = year_range
            enhanced_query += f" AND (PUB_YEAR:[{start_year} TO {end_year}])"
        
        # Add journal filter for high-impact venues
        if filters and 'target_journals' in filters:
            journal_parts = []
            for journal in self.target_journals:
                journal_parts.append(f'JOURNAL:"{journal}"')
            if journal_parts:
                enhanced_query += f" AND ({' OR '.join(journal_parts)})"
        
        # Filter to open access when possible
        enhanced_query += " AND (OPEN_ACCESS:Y OR HAS_PDF:Y)"
        
        return enhanced_query
    
    def _parse_pubmed_search_results(self, xml_response: str) -> List[str]:
        """Parse PMIDs from PubMed search XML response."""
        
        try:
            root = ET.fromstring(xml_response)
            id_list = root.find('IdList')
            
            if id_list is None:
                return []
            
            pmids = []
            for id_element in id_list.findall('Id'):
                if id_element.text:
                    pmids.append(id_element.text)
            
            return pmids
            
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse PubMed search XML: {e}")
            return []
    
    def _parse_pubmed_fetch_results(self, xml_response: str) -> List[Dict[str, Any]]:
        """Parse paper details from PubMed fetch XML response."""
        
        papers = []
        
        try:
            root = ET.fromstring(xml_response)
            
            for article in root.findall('.//PubmedArticle'):
                try:
                    paper = self._convert_pubmed_article_to_paper(article)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    self.logger.warning(f"Failed to parse PubMed article: {e}")
                    continue
            
            return papers
            
        except ET.ParseError as e:
            self.logger.error(f"Failed to parse PubMed fetch XML: {e}")
            return []
    
    def _convert_pubmed_article_to_paper(self, article: ET.Element) -> Optional[Dict[str, Any]]:
        """Convert PubMed XML article to standard paper format."""
        
        try:
            # Basic information
            citation = article.find('.//MedlineCitation')
            if citation is None:
                return None
            
            paper = {
                'source': 'pubmed'
            }
            
            # PMID
            pmid_elem = citation.find('PMID')
            if pmid_elem is not None:
                paper['pmid'] = pmid_elem.text
                paper['id'] = f"pubmed:{pmid_elem.text}"
            
            # Article details
            article_elem = citation.find('Article')
            if article_elem is None:
                return None
            
            # Title
            title_elem = article_elem.find('ArticleTitle')
            if title_elem is not None:
                paper['title'] = title_elem.text or ''
            
            # Abstract
            abstract_parts = []
            abstract_elem = article_elem.find('.//Abstract')
            if abstract_elem is not None:
                for abstract_text in abstract_elem.findall('.//AbstractText'):
                    if abstract_text.text:
                        abstract_parts.append(abstract_text.text)
            paper['abstract'] = ' '.join(abstract_parts)
            
            # Authors
            authors = []
            author_list = article_elem.find('AuthorList')
            if author_list is not None:
                for author in author_list.findall('Author'):
                    last_name = author.find('LastName')
                    first_name = author.find('ForeName')
                    
                    if last_name is not None and first_name is not None:
                        authors.append(f"{first_name.text} {last_name.text}")
                    elif last_name is not None:
                        authors.append(last_name.text)
            paper['authors'] = authors
            
            # Journal information
            journal_elem = article_elem.find('Journal')
            if journal_elem is not None:
                title_elem = journal_elem.find('Title')
                if title_elem is not None:
                    paper['venue'] = title_elem.text
                
                issn_elem = journal_elem.find('ISSN')
                if issn_elem is not None:
                    paper['issn'] = issn_elem.text
            
            paper['venue_type'] = 'journal'
            
            # Publication date
            pub_date_elem = article_elem.find('.//PubDate')
            if pub_date_elem is not None:
                year_elem = pub_date_elem.find('Year')
                if year_elem is not None:
                    paper['year'] = int(year_elem.text)
            
            # DOI
            doi_list = article_elem.find('.//ELocationID[@EIdType="doi"]')
            if doi_list is not None:
                paper['doi'] = doi_list.text
            
            # MeSH terms as keywords
            mesh_list = citation.find('.//MeshHeadingList')
            keywords = []
            if mesh_list is not None:
                for mesh_heading in mesh_list.findall('MeshHeading'):
                    descriptor = mesh_heading.find('DescriptorName')
                    if descriptor is not None:
                        keywords.append(descriptor.text)
            paper['keywords'] = keywords[:10]
            
            # Calculate PHM relevance
            paper['phm_relevance_score'] = self._calculate_phm_relevance(paper)
            
            # Quality indicators
            paper['quality_indicators'] = {
                'has_pmid': bool(paper.get('pmid')),
                'has_abstract': bool(paper.get('abstract')),
                'has_doi': bool(paper.get('doi')),
                'has_mesh_terms': len(keywords) > 0,
                'data_completeness': self._assess_data_completeness(paper)
            }
            
            return paper
            
        except Exception as e:
            self.logger.error(f"Error converting PubMed article: {e}")
            return None
    
    def _convert_europepmc_result_to_paper(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Europe PMC result to standard paper format."""
        
        try:
            paper = {
                'source': 'europepmc',
                'title': result.get('title', ''),
                'abstract': result.get('abstractText', ''),
                'authors': result.get('authorString', '').split(', ') if result.get('authorString') else [],
                'venue': result.get('journalTitle', ''),
                'venue_type': 'journal',
                'year': int(result.get('pubYear', 0)) if result.get('pubYear') else None,
                'doi': result.get('doi', ''),
                'pmid': result.get('pmid', ''),
                'pmcid': result.get('pmcid', ''),
                'cited_by_count': int(result.get('citedByCount', 0)),
                'is_open_access': result.get('isOpenAccess') == 'Y',
                'has_pdf': result.get('hasPDF') == 'Y'
            }
            
            # ID
            paper['id'] = result.get('id', '')
            
            # Keywords from subject terms
            keywords = []
            if result.get('keywordList'):
                for keyword_group in result['keywordList']['keyword']:
                    if isinstance(keyword_group, str):
                        keywords.append(keyword_group)
                    elif isinstance(keyword_group, dict):
                        keywords.append(keyword_group.get('value', ''))
            paper['keywords'] = keywords[:10]
            
            # Calculate PHM relevance
            paper['phm_relevance_score'] = self._calculate_phm_relevance(paper)
            
            # Quality indicators
            paper['quality_indicators'] = {
                'has_abstract': bool(paper['abstract']),
                'has_doi': bool(paper['doi']),
                'citations': paper['cited_by_count'],
                'open_access': paper['is_open_access'],
                'has_pdf': paper['has_pdf'],
                'data_completeness': self._assess_data_completeness(paper)
            }
            
            return paper
            
        except Exception as e:
            self.logger.error(f"Error converting Europe PMC result: {e}")
            return None
    
    def _calculate_phm_relevance(self, paper: Dict[str, Any]) -> float:
        """Calculate PHM relevance for biomedical papers."""
        
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
        weights = {
            'medical_devices': 0.3,
            'predictive': 0.3,
            'reliability': 0.2,
            'ai_methods': 0.2
        }
        
        for category, keywords in self.biomedical_phm_keywords.items():
            matches = sum(1 for kw in keywords if kw.lower() in text_content)
            max_possible = len(keywords)
            category_score = matches / max_possible if max_possible > 0 else 0.0
            
            weight = weights.get(category, 0.1)
            category_scores[category] = category_score * weight
        
        base_score = sum(category_scores.values())
        
        # Boost for high-impact journals
        venue = paper.get('venue', '').lower()
        if any(journal in venue for journal in self.target_journals):
            base_score = min(1.0, base_score * 1.5)
        
        return min(1.0, base_score)
    
    def _is_phm_relevant(self, paper: Dict[str, Any]) -> bool:
        """Check if paper meets PHM relevance threshold."""
        
        relevance_score = paper.get('phm_relevance_score', 0.0)
        return relevance_score >= 0.2  # Lower threshold for biomedical papers
    
    def _deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate papers from combined results."""
        
        seen_papers = set()
        unique_papers = []
        
        for paper in papers:
            # Create identifier from multiple fields
            identifiers = []
            
            if paper.get('doi'):
                identifiers.append(('doi', paper['doi'].lower()))
            if paper.get('pmid'):
                identifiers.append(('pmid', paper['pmid']))
            if paper.get('title'):
                # Use first 50 chars of title as identifier
                identifiers.append(('title', paper['title'][:50].lower().strip()))
            
            # Check if any identifier has been seen
            is_duplicate = any(identifier in seen_papers for identifier in identifiers)
            
            if not is_duplicate:
                unique_papers.append(paper)
                # Add all identifiers to seen set
                for identifier in identifiers:
                    seen_papers.add(identifier)
        
        return unique_papers
    
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
            
            filtered_papers.append(paper)
        
        return filtered_papers
    
    def _calculate_paper_score(self, paper: Dict[str, Any]) -> float:
        """Calculate composite score for ranking."""
        
        relevance = paper.get('phm_relevance_score', 0.0)
        citations = paper.get('cited_by_count', 0)
        year = paper.get('year', 2000)
        
        # Normalize components
        citation_score = min(1.0, citations / 50.0)  # Normalize citations
        recency_score = max(0.0, (year - 2015) / (datetime.now().year - 2015))
        
        # Check if high-impact journal
        venue = paper.get('venue', '').lower()
        impact_bonus = 0.2 if any(journal in venue for journal in self.target_journals) else 0.0
        
        # Weighted combination
        composite_score = (
            relevance * 0.4 +
            citation_score * 0.3 +
            recency_score * 0.2 +
            impact_bonus * 0.1
        )
        
        return composite_score
    
    def _assess_data_completeness(self, paper: Dict[str, Any]) -> float:
        """Assess completeness of paper metadata."""
        
        completeness_score = 0.0
        
        checks = [
            ('title', 0.2),
            ('abstract', 0.3),
            ('authors', 0.15),
            ('venue', 0.1),
            ('year', 0.1),
            ('doi', 0.1),
            ('pmid', 0.05)
        ]
        
        for field, weight in checks:
            if paper.get(field):
                if isinstance(paper[field], (str, int)) and paper[field]:
                    completeness_score += weight
                elif isinstance(paper[field], list) and paper[field]:
                    completeness_score += weight
        
        return min(1.0, completeness_score)
    
    def get_api_status(self) -> Dict[str, Any]:
        """Check API status for both services."""
        
        status = {}
        
        # Test PubMed
        try:
            response = requests.get(
                f"{self.pubmed_base_url}/einfo.fcgi",
                timeout=10
            )
            status['pubmed'] = {
                'available': response.status_code == 200,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            status['pubmed'] = {'available': False, 'error': str(e)}
        
        # Test Europe PMC
        try:
            response = requests.get(
                f"{self.europepmc_base_url}/search",
                params={'query': 'test', 'format': 'json', 'pageSize': 1},
                timeout=10
            )
            status['europepmc'] = {
                'available': response.status_code == 200,
                'response_time_ms': response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            status['europepmc'] = {'available': False, 'error': str(e)}
        
        status['email_configured'] = bool(self.email)
        status['rate_limit'] = self.rate_limit
        
        return status


if __name__ == "__main__":
    # Test the PubMed client
    client = PubMedClient()
    
    print("Testing PubMed/Europe PMC client...")
    
    # Test API status
    status = client.get_api_status()
    print(f"API Status: {json.dumps(status, indent=2)}")
    
    # Test search
    papers = client.search_papers(
        query="machine learning medical device monitoring",
        max_results=5,
        year_range=(2020, 2024)
    )
    
    print(f"\nFound {len(papers)} biomedical PHM papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.get('title', 'No title')}")
        print(f"   Authors: {', '.join(paper.get('authors', [])[:3])}")
        print(f"   Venue: {paper.get('venue', 'Unknown')}")
        print(f"   Year: {paper.get('year', 'Unknown')}")
        print(f"   Source: {paper.get('source', 'Unknown')}")
        if paper.get('pmid'):
            print(f"   PMID: {paper['pmid']}")
        if paper.get('doi'):
            print(f"   DOI: {paper['doi']}")
        print(f"   PHM Relevance: {paper.get('phm_relevance_score', 0):.3f}")
        if paper.get('abstract'):
            print(f"   Abstract: {paper['abstract'][:200]}...")