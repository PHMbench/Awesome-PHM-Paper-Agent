"""
MCP Academic Research Tools Integration Layer

This module provides a unified interface to interact with MCP academic research tools
for discovering, analyzing, and validating scholarly papers.
"""

import json
import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import quote
import logging

from .logging_config import get_logger


class MCPAcademicTools:
    """
    Wrapper class for MCP academic research tools integration.
    
    Provides methods to search academic databases, extract paper metadata,
    and validate scholarly sources with proper error handling and rate limiting.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MCP Academic Tools integration.
        
        Args:
            config: Configuration dictionary containing MCP settings
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.mcp_config = config.get('mcp_tools', {})
        
        # Initialize academic research capabilities
        self.academic_enabled = self.mcp_config.get('academic_researcher_enabled', True)
        self.max_results_per_query = self.mcp_config.get('max_results_per_query', 50)
        self.timeout_seconds = self.mcp_config.get('timeout_seconds', 120)
        
        self.logger.info("MCP Academic Tools integration initialized")
    
    def search_phm_papers(self, 
                         keywords: List[str],
                         date_range: str = "2023-2025",
                         max_results: int = 50,
                         include_preprints: bool = True) -> List[Dict[str, Any]]:
        """
        Search for PHM-related papers using MCP academic researcher.
        
        Args:
            keywords: List of search keywords
            date_range: Date range in format "YYYY-YYYY"
            max_results: Maximum number of results to return
            include_preprints: Whether to include preprints (arXiv, etc.)
            
        Returns:
            List of paper metadata dictionaries
        """
        if not self.academic_enabled:
            self.logger.warning("Academic researcher MCP tool is disabled")
            return []
        
        self.logger.info(f"Searching PHM papers with {len(keywords)} keywords")
        
        # Build comprehensive search query
        search_query = self._build_phm_search_query(keywords, date_range, include_preprints)
        
        # Execute MCP academic search (this would call the actual MCP tool)
        try:
            papers = self._execute_academic_search(search_query, max_results)
            
            # Parse and validate results
            validated_papers = []
            for paper in papers:
                validated_paper = self._validate_paper_metadata(paper)
                if validated_paper:
                    validated_papers.append(validated_paper)
            
            self.logger.info(f"Found {len(validated_papers)} valid PHM papers")
            return validated_papers[:max_results]
            
        except Exception as e:
            self.logger.error(f"MCP academic search failed: {e}")
            return []
    
    def get_paper_details(self, 
                         identifier: str,
                         identifier_type: str = "doi") -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific paper.
        
        Args:
            identifier: Paper identifier (DOI, arXiv ID, etc.)
            identifier_type: Type of identifier ('doi', 'arxiv', 'pmid')
            
        Returns:
            Detailed paper metadata or None if not found
        """
        self.logger.info(f"Getting details for paper {identifier_type}: {identifier}")
        
        try:
            # Build query for specific paper
            if identifier_type == "doi":
                query = f"DOI:{identifier}"
            elif identifier_type == "arxiv":
                query = f"arXiv:{identifier}"
            elif identifier_type == "pmid":
                query = f"PMID:{identifier}"
            else:
                query = identifier
            
            # Execute detailed lookup
            paper_data = self._execute_paper_lookup(query)
            
            if paper_data:
                return self._enhance_paper_metadata(paper_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get paper details: {e}")
        
        return None
    
    def validate_citation_data(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and enhance citation data for a list of papers.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            List of papers with validated and enhanced citation data
        """
        self.logger.info(f"Validating citation data for {len(papers)} papers")
        
        validated_papers = []
        for paper in papers:
            try:
                # Validate DOI if present
                if paper.get('doi'):
                    paper = self._validate_doi(paper)
                
                # Enhance citation metrics
                paper = self._enhance_citation_metrics(paper)
                
                # Validate journal/venue information
                paper = self._validate_venue_info(paper)
                
                validated_papers.append(paper)
                
            except Exception as e:
                self.logger.warning(f"Citation validation failed for paper {paper.get('title', 'Unknown')}: {e}")
                # Still include paper but mark as unvalidated
                paper['validation_status'] = 'failed'
                validated_papers.append(paper)
        
        return validated_papers
    
    def extract_research_themes(self, papers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extract common research themes from a collection of papers.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            Dictionary mapping themes to paper titles
        """
        self.logger.info(f"Extracting research themes from {len(papers)} papers")
        
        themes = {}
        
        # Extract themes using MCP academic analysis
        try:
            # Combine all abstracts and titles for theme analysis
            text_corpus = []
            for paper in papers:
                title = paper.get('title', '')
                abstract = paper.get('abstract', '')
                keywords = paper.get('keywords', [])
                
                text_corpus.append({
                    'title': title,
                    'abstract': abstract,
                    'keywords': keywords,
                    'paper_id': paper.get('doi', title[:50])
                })
            
            # Use MCP to extract themes
            extracted_themes = self._execute_theme_extraction(text_corpus)
            
            # Process and validate themes
            for theme_name, paper_ids in extracted_themes.items():
                if theme_name not in themes:
                    themes[theme_name] = []
                themes[theme_name].extend(paper_ids)
            
        except Exception as e:
            self.logger.error(f"Theme extraction failed: {e}")
            # Fallback to keyword-based theme extraction
            themes = self._fallback_theme_extraction(papers)
        
        return themes
    
    def _build_phm_search_query(self, 
                               keywords: List[str], 
                               date_range: str,
                               include_preprints: bool) -> str:
        """Build comprehensive search query for PHM papers."""
        
        # Core PHM terms
        core_terms = [
            "prognostics", "health management", "fault diagnosis", 
            "predictive maintenance", "condition monitoring",
            "remaining useful life", "RUL", "degradation modeling",
            "anomaly detection", "failure prediction"
        ]
        
        # Combine user keywords with core PHM terms
        all_keywords = list(set(keywords + core_terms))
        
        # Build search query
        keyword_query = ' OR '.join([f'"{kw}"' for kw in all_keywords])
        
        # Add date constraints
        start_year, end_year = map(int, date_range.split('-'))
        date_query = f"publication_year:[{start_year} TO {end_year}]"
        
        # Build final query
        query_parts = [f"({keyword_query})", date_query]
        
        if include_preprints:
            venue_query = "(venue:arXiv OR venue:bioRxiv OR journal:* OR conference:*)"
        else:
            venue_query = "(journal:* OR conference:*)"
        
        query_parts.append(venue_query)
        
        return " AND ".join(query_parts)
    
    def _execute_academic_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Execute academic search using MCP tools.
        
        Note: This is a placeholder that would interface with actual MCP academic tools.
        In practice, this would call the MCP academic-researcher agent.
        """
        # This would be replaced with actual MCP tool calls
        # For now, providing structure for integration
        
        search_prompt = f"""
        Search for academic papers related to Prognostics and Health Management (PHM) with the following criteria:
        
        Query: {query}
        Maximum results: {max_results}
        
        Please search across multiple academic databases including:
        - ArXiv (for preprints)
        - PubMed (for biomedical applications)
        - Google Scholar (for comprehensive coverage)
        - IEEE Xplore (for engineering papers)
        - Semantic Scholar (for AI/ML papers)
        
        For each paper found, extract:
        - Title (exact)
        - Authors (full names with affiliations)
        - Publication year and date
        - Journal/Conference name
        - DOI (if available)
        - Abstract (complete text)
        - Keywords
        - Citation count
        - PDF URL (if freely available)
        - Impact metrics
        
        Focus on high-quality, peer-reviewed publications relevant to:
        - Fault diagnosis and detection
        - Predictive maintenance
        - Health monitoring systems
        - Machine learning in PHM
        - Signal processing for condition monitoring
        - Reliability engineering
        
        Return results in structured JSON format with complete bibliographic information.
        """
        
        # Placeholder return - would be replaced with actual MCP call
        # return mcp_academic_researcher.search(search_prompt)
        
        self.logger.warning("MCP academic search not yet implemented - returning placeholder")
        return []
    
    def _execute_paper_lookup(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute detailed paper lookup using MCP tools."""
        # Placeholder for MCP paper lookup
        return None
    
    def _execute_theme_extraction(self, text_corpus: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Execute theme extraction using MCP academic analysis."""
        # Placeholder for MCP theme extraction
        return {}
    
    def _validate_paper_metadata(self, paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and standardize paper metadata."""
        try:
            # Required fields
            if not paper.get('title') or not paper.get('authors'):
                return None
            
            # Standardize format
            validated_paper = {
                'title': paper['title'].strip(),
                'authors': [author.strip() for author in paper.get('authors', [])],
                'year': int(paper.get('year', 0)) if paper.get('year') else 0,
                'venue': paper.get('venue', 'Unknown').strip(),
                'doi': self._clean_doi(paper.get('doi')),
                'abstract': paper.get('abstract', '').strip(),
                'keywords': [kw.lower().strip() for kw in paper.get('keywords', [])],
                'citation_count': int(paper.get('citation_count', 0)),
                'urls': paper.get('urls', {}),
                'source': paper.get('source', 'mcp'),
                'retrieved_date': datetime.now().isoformat(),
                'validation_status': 'validated'
            }
            
            # Additional validation
            if validated_paper['year'] < 1900 or validated_paper['year'] > datetime.now().year + 1:
                validated_paper['year'] = 0
            
            return validated_paper
            
        except Exception as e:
            self.logger.error(f"Paper validation error: {e}")
            return None
    
    def _enhance_paper_metadata(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance paper metadata with additional information."""
        # Add PHM relevance score
        paper['phm_relevance_score'] = self._calculate_phm_relevance(paper)
        
        # Extract methodology if possible
        paper['methodology'] = self._extract_methodology(paper)
        
        # Determine research area
        paper['research_area'] = self._classify_research_area(paper)
        
        return paper
    
    def _validate_doi(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Validate DOI and enhance with DOI-based metadata."""
        doi = paper.get('doi')
        if not doi:
            return paper
        
        # Clean and validate DOI format
        clean_doi = self._clean_doi(doi)
        if clean_doi:
            paper['doi'] = clean_doi
            paper['doi_url'] = f"https://doi.org/{clean_doi}"
            
            # Could add DOI resolution here
            paper['doi_valid'] = True
        else:
            paper['doi_valid'] = False
        
        return paper
    
    def _enhance_citation_metrics(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance paper with additional citation metrics."""
        citation_count = paper.get('citation_count', 0)
        year = paper.get('year', datetime.now().year)
        
        # Calculate citations per year
        years_since_publication = max(1, datetime.now().year - year)
        paper['citations_per_year'] = citation_count / years_since_publication
        
        # Classify citation impact
        if citation_count > 100:
            paper['citation_impact'] = 'high'
        elif citation_count > 20:
            paper['citation_impact'] = 'medium'
        else:
            paper['citation_impact'] = 'low'
        
        return paper
    
    def _validate_venue_info(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance venue information."""
        venue = paper.get('venue', '')
        
        # Known high-impact PHM venues
        phm_journals = {
            'Mechanical Systems and Signal Processing': {'impact_factor': 7.8, 'quartile': 'Q1'},
            'IEEE Transactions on Industrial Electronics': {'impact_factor': 8.2, 'quartile': 'Q1'},
            'Reliability Engineering & System Safety': {'impact_factor': 6.1, 'quartile': 'Q1'},
            'IEEE/ASME Transactions on Mechatronics': {'impact_factor': 5.9, 'quartile': 'Q1'},
            'Journal of Sound and Vibration': {'impact_factor': 4.4, 'quartile': 'Q1'},
            'Expert Systems with Applications': {'impact_factor': 8.5, 'quartile': 'Q1'},
            'IEEE Transactions on Reliability': {'impact_factor': 5.9, 'quartile': 'Q1'}
        }
        
        # Enhanced venue info if available
        for journal, info in phm_journals.items():
            if journal.lower() in venue.lower():
                paper['venue_impact_factor'] = info['impact_factor']
                paper['venue_quartile'] = info['quartile']
                paper['venue_type'] = 'journal'
                break
        
        # Check for conferences
        phm_conferences = [
            'PHM Conference', 'ICPHM', 'European Conference of the PHM Society',
            'IEEE Conference on Prognostics and Health Management',
            'Annual Conference of the PHM Society'
        ]
        
        for conf in phm_conferences:
            if conf.lower() in venue.lower():
                paper['venue_type'] = 'conference'
                break
        
        return paper
    
    def _clean_doi(self, doi: Optional[str]) -> Optional[str]:
        """Clean and validate DOI format."""
        if not doi:
            return None
        
        # Remove common prefixes
        doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '').replace('doi:', '')
        
        # Validate DOI format (basic)
        doi_pattern = r'^10\.\d+/.+'
        if re.match(doi_pattern, doi):
            return doi
        
        return None
    
    def _calculate_phm_relevance(self, paper: Dict[str, Any]) -> float:
        """Calculate PHM relevance score for a paper."""
        score = 0.0
        
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        keywords = [kw.lower() for kw in paper.get('keywords', [])]
        
        # PHM-specific terms with weights
        phm_terms = {
            'prognostics': 1.0, 'health management': 1.0, 'fault diagnosis': 0.9,
            'predictive maintenance': 0.9, 'condition monitoring': 0.8,
            'remaining useful life': 0.9, 'rul': 0.9, 'degradation': 0.7,
            'anomaly detection': 0.6, 'failure prediction': 0.8,
            'bearing fault': 0.7, 'vibration analysis': 0.6,
            'signal processing': 0.5, 'machine learning': 0.4,
            'deep learning': 0.4, 'neural network': 0.4
        }
        
        # Check title (weight: 0.4)
        for term, weight in phm_terms.items():
            if term in title:
                score += weight * 0.4
        
        # Check abstract (weight: 0.3)
        for term, weight in phm_terms.items():
            if term in abstract:
                score += weight * 0.3
        
        # Check keywords (weight: 0.3)
        for keyword in keywords:
            for term, weight in phm_terms.items():
                if term in keyword:
                    score += weight * 0.3
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _extract_methodology(self, paper: Dict[str, Any]) -> List[str]:
        """Extract methodology keywords from paper."""
        methodologies = []
        
        text = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
        
        # Common methodologies in PHM
        method_terms = [
            'deep learning', 'machine learning', 'neural network', 'cnn', 'lstm',
            'support vector machine', 'svm', 'random forest', 'decision tree',
            'bayesian', 'kalman filter', 'particle filter', 'hmm', 'gaussian process',
            'wavelet', 'fourier transform', 'fft', 'time-frequency analysis',
            'principal component analysis', 'pca', 'independent component analysis',
            'autoencoder', 'generative adversarial network', 'gan',
            'ensemble learning', 'clustering', 'classification', 'regression'
        ]
        
        for term in method_terms:
            if term in text:
                methodologies.append(term)
        
        return methodologies
    
    def _classify_research_area(self, paper: Dict[str, Any]) -> str:
        """Classify paper into research area."""
        text = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
        
        # Research areas with keywords
        areas = {
            'Bearing Fault Diagnosis': ['bearing', 'roller', 'ball bearing', 'rolling element'],
            'Gear Fault Diagnosis': ['gear', 'gearbox', 'transmission'],
            'Motor Health Monitoring': ['motor', 'electric machine', 'induction motor'],
            'Battery Health Management': ['battery', 'lithium-ion', 'energy storage'],
            'Turbine Monitoring': ['turbine', 'wind turbine', 'gas turbine'],
            'Structural Health Monitoring': ['structural', 'bridge', 'building', 'aircraft'],
            'Process Monitoring': ['chemical process', 'manufacturing', 'industrial process'],
            'Methodology Development': ['algorithm', 'method', 'framework', 'approach']
        }
        
        for area, keywords in areas.items():
            if any(keyword in text for keyword in keywords):
                return area
        
        return 'General PHM'
    
    def _fallback_theme_extraction(self, papers: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Fallback theme extraction using keyword frequency."""
        themes = {}
        
        # Count keyword frequency
        keyword_counts = {}
        for paper in papers:
            for keyword in paper.get('keywords', []):
                keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Group papers by common themes
        common_keywords = [kw for kw, count in keyword_counts.items() if count >= 2]
        
        for keyword in common_keywords:
            themes[keyword] = []
            for paper in papers:
                if keyword in paper.get('keywords', []):
                    themes[keyword].append(paper.get('title', ''))
        
        return themes