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
from .phm_constants import (
    PHM_CONCEPTS, SEARCH_TEMPLATES, MCP_CONFIG,
    ERROR_MESSAGES, DEFAULT_CONFIG
)
from .paper_utils import (
    create_paper_fingerprint, calculate_phm_relevance_score,
    merge_paper_metadata, validate_doi, classify_methodology,
    identify_application_domains
)


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
        Execute academic search using academic-researcher agent via Task tool.
        
        This method calls the academic-researcher agent to search real academic databases
        and returns validated paper metadata.
        """
        search_prompt = f"""
        You are the academic-researcher agent. Search for academic papers related to Prognostics and Health Management (PHM) with the following criteria:
        
        Search Query: {query}
        Maximum results: {max_results}
        
        Please search across multiple academic databases including:
        - ArXiv (for recent preprints and research)
        - PubMed (for biomedical PHM applications)
        - Google Scholar (for comprehensive academic coverage)
        - IEEE Xplore (for engineering and technical papers)
        - Semantic Scholar (for AI/ML in PHM)
        
        For each paper found, extract complete information including:
        - Title (exact as published)
        - Authors (full names with affiliations if available)
        - Publication year and date
        - Journal/Conference name and details
        - DOI (mandatory if available)
        - Complete abstract text (essential for categorization)
        - Keywords or subject terms
        - Citation count (if available)
        - PDF URL (if freely accessible)
        - Publication type (journal/conference/preprint)
        
        Focus specifically on high-quality publications relevant to PHM domains:
        - Bearing fault diagnosis and detection
        - Predictive maintenance strategies  
        - Health monitoring systems and IoT
        - Machine learning applications in PHM
        - Signal processing for condition monitoring
        - Remaining useful life (RUL) prediction
        - Digital twin and cyber-physical systems
        - Reliability and failure analysis
        
        IMPORTANT: Return results in the standard JSON format specified in your agent definition.
        Ensure all abstracts are complete and accurate for proper categorization.
        Prioritize peer-reviewed publications but include high-quality preprints.
        """
        
        try:
            # Import Task tool for calling the academic-researcher agent
            # This would be imported at the module level in practice
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            
            # Call academic-researcher agent (this is a conceptual implementation)
            # In practice, this would use the Task tool
            result = self._call_academic_researcher_agent(search_prompt)
            
            if result and isinstance(result, dict) and 'findings' in result:
                papers = []
                for finding in result['findings']:
                    # Convert academic-researcher format to our internal format
                    paper = self._convert_academic_result_to_paper(finding)
                    if paper and self._validate_paper_metadata(paper):
                        papers.append(paper)
                
                self.logger.info(f"Academic researcher returned {len(papers)} validated papers")
                return papers
            else:
                self.logger.warning("Academic researcher returned invalid or empty results")
                return []
                
        except Exception as e:
            self.logger.error(f"Academic search execution failed: {e}")
            # Return empty list rather than raising exception to allow graceful degradation
            return []
    
    def _call_academic_researcher_agent(self, prompt: str) -> Dict[str, Any]:
        """
        Call the academic-researcher agent via Task tool.
        
        This is a wrapper method that would use the Task tool to invoke
        the academic-researcher subagent with the given prompt.
        """
        # This is a conceptual implementation
        # In practice, this would be handled by the calling code using Task tool
        
        # For now, return a structured placeholder that indicates this should
        # be replaced with actual Task tool call
        return {
            "implementation_note": "This method should be replaced with actual Task tool call",
            "search_summary": {
                "queries_used": [prompt[:100] + "..."],
                "databases_searched": ["arxiv", "pubmed", "google_scholar"],
                "total_papers_reviewed": 0,
                "papers_selected": 0
            },
            "findings": [],
            "synthesis": "Academic researcher agent not yet integrated with Task tool",
            "research_gaps": [],
            "seminal_works": []
        }
    
    def _convert_academic_result_to_paper(self, finding: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert academic-researcher agent result to internal paper format.
        
        Args:
            finding: Single paper result from academic-researcher agent
            
        Returns:
            Paper metadata dictionary in internal format or None if invalid
        """
        try:
            # Extract core information from academic-researcher format
            citation = finding.get('citation', '')
            doi = finding.get('doi', '')
            
            # Parse citation to extract components
            title, authors, year, venue = self._parse_citation(citation)
            
            # Build internal paper format
            paper = {
                'title': title or 'Unknown Title',
                'authors': authors or [],
                'year': year,
                'publication_date': finding.get('publication_date', f"{year}-01-01" if year else None),
                'venue': venue or 'Unknown Venue',
                'doi': doi,
                'abstract': finding.get('abstract', ''),
                'keywords': finding.get('keywords', []),
                'key_findings': finding.get('key_findings', []),
                'methodology': finding.get('methodology', ''),
                'paper_type': finding.get('type', 'unknown'),
                'citation_count': finding.get('quality_indicators', {}).get('citations', 0),
                'journal_impact': finding.get('quality_indicators', {}).get('journal_impact', 'unknown'),
                'peer_reviewed': finding.get('quality_indicators', {}).get('peer_reviewed', True),
                'relevance_to_query': finding.get('relevance', ''),
                'source': 'academic_researcher_agent',
                'extraction_date': datetime.now().isoformat()
            }
            
            # Calculate PHM relevance score
            paper['phm_relevance_score'] = self._calculate_phm_relevance(paper)
            
            # Add search tags for categorization
            paper['search_tags'] = self._generate_search_tags_for_paper(paper)
            
            return paper
            
        except Exception as e:
            self.logger.warning(f"Failed to convert academic result: {e}")
            return None
    
    def _parse_citation(self, citation: str) -> tuple:
        """Parse citation string to extract title, authors, year, venue."""
        try:
            # Basic citation parsing - this could be enhanced with more sophisticated parsing
            parts = citation.split('.')
            
            if len(parts) >= 3:
                # Format: Authors. "Title." Journal/Conference, year.
                authors_part = parts[0].strip()
                title_part = parts[1].strip().strip('"')
                venue_year_part = parts[2].strip()
                
                # Extract authors
                authors = [name.strip() for name in authors_part.split(',')]
                
                # Extract year from venue part
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', venue_year_part)
                year = int(year_match.group()) if year_match else None
                
                # Extract venue (remove year and page numbers)
                venue = re.sub(r'\b(19|20)\d{2}\b', '', venue_year_part)
                venue = re.sub(r'pp?\.\s*\d+[-–]\d+', '', venue)
                venue = venue.strip(', ')
                
                return title_part, authors, year, venue
            
            return citation, [], None, ''
            
        except Exception:
            return citation, [], None, ''
    
    def _calculate_phm_relevance(self, paper: Dict[str, Any]) -> float:
        """Calculate PHM relevance score for a paper."""
        return calculate_phm_relevance_score(paper)
    
    def _generate_search_tags_for_paper(self, paper: Dict[str, Any]) -> List[str]:
        """Generate search tags for paper categorization."""
        tags = []
        
        # Add year tag
        if paper.get('year'):
            tags.append(f"year:{paper['year']}")
        
        # Add methodology tags based on content analysis
        methodologies = classify_methodology(paper)
        for method in methodologies:
            tags.append(f"method:{method.lower().replace(' ', '-')}")
        
        # Add domain tags
        domains = identify_application_domains(paper)
        for domain in domains:
            tags.append(f"domain:{domain.lower().replace(' ', '-')}")
        
        # Add publication type tag
        paper_type = paper.get('paper_type', 'unknown')
        tags.append(f"type:{paper_type}")
        
        # Add impact tag based on citation count
        citation_count = paper.get('citation_count', 0)
        if citation_count > 100:
            tags.append("impact:high")
        elif citation_count > 20:
            tags.append("impact:medium")
        else:
            tags.append("impact:low")
        
        return tags
    
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
        # Add PHM relevance score using centralized function
        overall_score, _ = calculate_phm_relevance_score(paper)
        paper['phm_relevance_score'] = overall_score
        
        # Extract methodology using centralized function
        paper['methodology'] = classify_methodology(paper)
        
        # Determine research area using application domains
        domains = identify_application_domains(paper)
        paper['research_area'] = domains[0] if domains else 'General PHM'
        paper['application_domains'] = domains
        
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