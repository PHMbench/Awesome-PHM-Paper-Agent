"""
Enhanced Paper Discovery Agent with MCP Integration

This agent uses MCP academic research tools to discover, validate, and analyze
PHM research papers from multiple authoritative sources.

Key Features:
- Real academic database integration via MCP
- Multi-source paper discovery (arXiv, PubMed, Google Scholar, etc.)
- Automatic metadata validation and enhancement
- PHM-specific relevance scoring
- PDF download and BibTeX generation
"""

import asyncio
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import json
import re

from .base_agent import BaseAgent, AgentError
from ..utils.mcp_integration import MCPAcademicTools
from ..utils.llm_client import LLMManager
from ..models import PaperMetadata, VenueType


class EnhancedPaperDiscoveryAgent(BaseAgent):
    """
    Enhanced paper discovery agent using MCP academic research tools.
    
    Provides comprehensive paper discovery with real academic database integration,
    automatic validation, and PHM-specific analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "EnhancedPaperDiscoveryAgent")
        
        # Initialize MCP academic tools
        self.mcp_tools = MCPAcademicTools(config)
        
        # Initialize LLM manager for enhanced analysis
        self.llm_manager = LLMManager(config)
        
        # Configuration
        self.discovery_config = self.get_config_value('discovery_settings', {})
        self.max_results_per_source = self.discovery_config.get('max_results_per_source', 100)
        self.enable_pdf_download = self.discovery_config.get('enable_pdf_download', True)
        self.enable_citation_enhancement = self.discovery_config.get('enable_citation_enhancement', True)
        self.minimum_relevance_score = self.discovery_config.get('minimum_relevance_score', 0.3)
        
        # Tracking sets for deduplication
        self.seen_dois: Set[str] = set()
        self.seen_fingerprints: Set[str] = set()
        
        self.logger.info("Enhanced Paper Discovery Agent initialized with MCP integration")
    
    def process(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Discover papers using MCP academic research tools.
        
        Args:
            input_data: Dictionary containing:
                - keywords: List of search keywords
                - date_range: String in format "YYYY-YYYY" 
                - max_results: Maximum total results
                - specific_date_after: Optional ISO date for recent papers only
                - research_areas: Optional list of specific PHM research areas
                - include_preprints: Whether to include preprints (default: True)
        
        Returns:
            List of enhanced paper metadata dictionaries
        """
        keywords = input_data.get('keywords', [])
        date_range = input_data.get('date_range', '2020-2025')
        max_results = input_data.get('max_results', self.max_results_per_source)
        specific_date_after = input_data.get('specific_date_after')
        research_areas = input_data.get('research_areas', [])
        include_preprints = input_data.get('include_preprints', True)
        
        if not keywords:
            # Use default PHM keywords if none provided
            keywords = self._get_default_phm_keywords()
            
        self.logger.info(f"Starting enhanced paper discovery with {len(keywords)} keywords")
        self.logger.info(f"Date range: {date_range}, Max results: {max_results}")
        
        try:
            # Step 1: Discover papers using MCP academic tools
            discovered_papers = self._discover_papers_mcp(
                keywords, date_range, max_results, include_preprints
            )
            
            if not discovered_papers:
                self.logger.warning("No papers discovered from MCP tools")
                return []
            
            self.logger.info(f"Discovered {len(discovered_papers)} papers from MCP tools")
            
            # Step 2: Filter by specific date if provided
            if specific_date_after:
                discovered_papers = self._filter_by_recent_date(discovered_papers, specific_date_after)
                self.logger.info(f"After date filtering: {len(discovered_papers)} papers")
            
            # Step 3: Filter by research areas if specified
            if research_areas:
                discovered_papers = self._filter_by_research_areas(discovered_papers, research_areas)
                self.logger.info(f"After research area filtering: {len(discovered_papers)} papers")
            
            # Step 4: Deduplicate papers
            unique_papers = self._advanced_deduplication(discovered_papers)
            self.logger.info(f"After deduplication: {len(unique_papers)} papers")
            
            # Step 5: Enhance with additional metadata
            enhanced_papers = self._enhance_papers_with_llm(unique_papers)
            self.logger.info(f"Enhanced {len(enhanced_papers)} papers with LLM analysis")
            
            # Step 6: Filter by PHM relevance
            relevant_papers = self._filter_by_phm_relevance(enhanced_papers)
            self.logger.info(f"After relevance filtering: {len(relevant_papers)} papers")
            
            # Step 7: Sort by composite score (relevance + citations + recency)
            sorted_papers = self._sort_by_composite_score(relevant_papers)
            
            # Step 8: Validate and finalize
            final_papers = self._final_validation(sorted_papers[:max_results])
            
            self.logger.info(f"Final result: {len(final_papers)} validated papers")
            return final_papers
            
        except Exception as e:
            self.logger.error(f"Enhanced paper discovery failed: {e}")
            raise AgentError(f"Paper discovery failed: {e}")
    
    def _discover_papers_mcp(self, 
                           keywords: List[str], 
                           date_range: str,
                           max_results: int,
                           include_preprints: bool) -> List[Dict[str, Any]]:
        """Discover papers using MCP academic research tools."""
        try:
            # Use MCP tools to search for PHM papers
            papers = self.mcp_tools.search_phm_papers(
                keywords=keywords,
                date_range=date_range,
                max_results=max_results * 2,  # Get more for filtering
                include_preprints=include_preprints
            )
            
            # Validate and enhance citation data
            if self.enable_citation_enhancement and papers:
                papers = self.mcp_tools.validate_citation_data(papers)
            
            return papers
            
        except Exception as e:
            self.logger.error(f"MCP paper discovery failed: {e}")
            return []
    
    def _filter_by_recent_date(self, papers: List[Dict[str, Any]], cutoff_date: str) -> List[Dict[str, Any]]:
        """Filter papers to only include those after a specific date."""
        try:
            cutoff = datetime.fromisoformat(cutoff_date.replace('Z', '+00:00'))
            filtered_papers = []
            
            for paper in papers:
                # Try to get publication date
                pub_date = None
                if paper.get('publication_date'):
                    try:
                        pub_date = datetime.fromisoformat(paper['publication_date'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # Fallback to year if no specific date
                if not pub_date and paper.get('year'):
                    try:
                        pub_date = datetime(int(paper['year']), 1, 1)
                    except:
                        pass
                
                # Include if date is after cutoff or unknown (to be safe)
                if not pub_date or pub_date >= cutoff:
                    filtered_papers.append(paper)
            
            return filtered_papers
            
        except Exception as e:
            self.logger.warning(f"Date filtering failed: {e}")
            return papers
    
    def _filter_by_research_areas(self, papers: List[Dict[str, Any]], areas: List[str]) -> List[Dict[str, Any]]:
        """Filter papers by specific research areas."""
        if not areas:
            return papers
        
        filtered_papers = []
        areas_lower = [area.lower() for area in areas]
        
        for paper in papers:
            paper_text = (
                paper.get('title', '') + ' ' + 
                paper.get('abstract', '') + ' ' +
                ' '.join(paper.get('keywords', []))
            ).lower()
            
            # Check if any research area is mentioned
            if any(area in paper_text for area in areas_lower):
                filtered_papers.append(paper)
        
        return filtered_papers
    
    def _advanced_deduplication(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Advanced deduplication using multiple strategies."""
        unique_papers = []
        
        for paper in papers:
            # Strategy 1: DOI-based deduplication
            doi = paper.get('doi')
            if doi and doi in self.seen_dois:
                continue
            
            # Strategy 2: Title + first author fingerprint
            fingerprint = self._create_advanced_fingerprint(paper)
            if fingerprint in self.seen_fingerprints:
                continue
            
            # Strategy 3: Fuzzy title matching for near-duplicates
            if self._is_fuzzy_duplicate(paper, unique_papers):
                continue
            
            # Add to unique papers
            unique_papers.append(paper)
            
            # Track for future deduplication
            if doi:
                self.seen_dois.add(doi)
            self.seen_fingerprints.add(fingerprint)
        
        return unique_papers
    
    def _create_advanced_fingerprint(self, paper: Dict[str, Any]) -> str:
        """Create advanced fingerprint for deduplication."""
        import hashlib
        
        # Normalize title
        title = re.sub(r'[^\w\s]', '', paper.get('title', '').lower())
        title = ' '.join(title.split())
        
        # Get first author
        authors = paper.get('authors', [])
        first_author = ''
        if authors:
            first_author = authors[0].lower().strip()
            # Extract last name
            name_parts = first_author.replace(',', ' ').split()
            first_author = name_parts[-1] if name_parts else ''
        
        # Include year and venue for better uniqueness
        year = str(paper.get('year', 0))
        venue = paper.get('venue', '').lower()[:20]  # First 20 chars of venue
        
        fingerprint_text = f"{title}|{first_author}|{year}|{venue}"
        return hashlib.sha256(fingerprint_text.encode()).hexdigest()
    
    def _is_fuzzy_duplicate(self, paper: Dict[str, Any], existing_papers: List[Dict[str, Any]]) -> bool:
        """Check for fuzzy duplicates using title similarity."""
        from difflib import SequenceMatcher
        
        paper_title = paper.get('title', '').lower()
        if len(paper_title) < 10:
            return False
        
        for existing in existing_papers:
            existing_title = existing.get('title', '').lower()
            similarity = SequenceMatcher(None, paper_title, existing_title).ratio()
            
            # If titles are 90% similar, consider as duplicate
            if similarity > 0.9:
                return True
        
        return False
    
    def _enhance_papers_with_llm(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance papers using LLM analysis."""
        if not self.llm_manager.get_feature_enabled('paper_enhancement'):
            return papers
        
        enhanced_papers = []
        
        for paper in papers:
            try:
                # Generate TL;DR summary
                tldr = self._generate_tldr(paper)
                if tldr:
                    paper['tldr'] = tldr
                
                # Extract key contributions
                contributions = self._extract_contributions(paper)
                if contributions:
                    paper['key_contributions'] = contributions
                
                # Classify methodology
                methodology = self._classify_methodology(paper)
                if methodology:
                    paper['methodology_category'] = methodology
                
                # Extract application domain
                domain = self._extract_application_domain(paper)
                if domain:
                    paper['application_domain'] = domain
                
                enhanced_papers.append(paper)
                
            except Exception as e:
                self.logger.warning(f"LLM enhancement failed for paper {paper.get('title', 'Unknown')}: {e}")
                enhanced_papers.append(paper)  # Include anyway
        
        return enhanced_papers
    
    def _generate_tldr(self, paper: Dict[str, Any]) -> Optional[str]:
        """Generate TL;DR summary using LLM."""
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        if not title or not abstract:
            return None
        
        prompt = f"""
        Generate a concise TL;DR summary (maximum 50 words) for this PHM research paper:
        
        Title: {title}
        
        Abstract: {abstract}
        
        Focus on: main contribution, method used, and key result/improvement.
        Write in Chinese for better readability.
        """
        
        try:
            response = self.llm_manager.generate_text(prompt, max_tokens=150, temperature=0.3)
            if response and len(response.strip()) > 10:
                return response.strip()
        except Exception as e:
            self.logger.warning(f"TL;DR generation failed: {e}")
        
        return None
    
    def _extract_contributions(self, paper: Dict[str, Any]) -> Optional[List[str]]:
        """Extract key contributions using LLM."""
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        if not abstract:
            return None
        
        prompt = f"""
        Extract 3-5 key contributions from this PHM research paper:
        
        Title: {title}
        Abstract: {abstract}
        
        List only the main technical/methodological contributions, one per line.
        Be specific and focus on novel aspects.
        """
        
        try:
            response = self.llm_manager.generate_text(prompt, max_tokens=200, temperature=0.3)
            if response:
                contributions = []
                lines = response.strip().split('\n')
                for line in lines:
                    line = re.sub(r'^[-*•\d\.)\s]+', '', line).strip()
                    if line and len(line) > 10:
                        contributions.append(line)
                return contributions[:5]
        except Exception as e:
            self.logger.warning(f"Contribution extraction failed: {e}")
        
        return None
    
    def _classify_methodology(self, paper: Dict[str, Any]) -> Optional[str]:
        """Classify paper methodology."""
        text = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
        
        # Methodology categories
        methods = {
            'Deep Learning': ['deep learning', 'neural network', 'cnn', 'lstm', 'transformer', 'autoencoder'],
            'Machine Learning': ['machine learning', 'svm', 'random forest', 'ensemble', 'decision tree'],
            'Signal Processing': ['signal processing', 'wavelet', 'fourier', 'fft', 'time-frequency'],
            'Statistical Methods': ['statistical', 'bayesian', 'gaussian', 'monte carlo', 'kalman'],
            'Physics-Based': ['physics-based', 'model-based', 'analytical', 'mathematical model'],
            'Hybrid Methods': ['hybrid', 'combined', 'integrated', 'multi-modal']
        }
        
        for category, keywords in methods.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'Other'
    
    def _extract_application_domain(self, paper: Dict[str, Any]) -> Optional[str]:
        """Extract application domain."""
        text = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
        
        domains = {
            'Rotating Machinery': ['bearing', 'gear', 'rotor', 'shaft', 'rotating', 'centrifugal'],
            'Electric Motors': ['motor', 'electric machine', 'induction', 'synchronous'],
            'Power Systems': ['power system', 'transformer', 'generator', 'electrical'],
            'Aerospace': ['aircraft', 'aerospace', 'jet engine', 'turbine', 'aviation'],
            'Automotive': ['vehicle', 'automotive', 'engine', 'transmission', 'brake'],
            'Industrial Process': ['process', 'manufacturing', 'chemical', 'production'],
            'Energy Systems': ['wind turbine', 'solar', 'battery', 'energy storage'],
            'Infrastructure': ['bridge', 'building', 'structural', 'civil']
        }
        
        for domain, keywords in domains.items():
            if any(keyword in text for keyword in keywords):
                return domain
        
        return 'General'
    
    def _filter_by_phm_relevance(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter papers by PHM relevance score."""
        relevant_papers = []
        
        for paper in papers:
            # Calculate PHM relevance if not already done
            if 'phm_relevance_score' not in paper:
                paper['phm_relevance_score'] = self.mcp_tools._calculate_phm_relevance(paper)
            
            # Filter by minimum relevance score
            if paper['phm_relevance_score'] >= self.minimum_relevance_score:
                relevant_papers.append(paper)
            else:
                self.logger.debug(f"Filtered out low relevance paper: {paper.get('title', 'Unknown')}")
        
        return relevant_papers
    
    def _sort_by_composite_score(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort papers by composite score considering relevance, citations, and recency."""
        current_year = datetime.now().year
        
        for paper in papers:
            # Components of composite score
            relevance_score = paper.get('phm_relevance_score', 0.0)
            citation_count = paper.get('citation_count', 0)
            year = paper.get('year', current_year - 10)
            
            # Normalize citation count (log scale)
            import math
            citation_score = math.log(citation_count + 1) / 10.0  # Log scale, capped influence
            
            # Recency score (more recent papers get higher scores)
            years_old = max(0, current_year - year)
            recency_score = max(0, 1.0 - years_old / 10.0)  # Decays over 10 years
            
            # Venue quality (if available)
            venue_score = 0.0
            if paper.get('venue_quartile') == 'Q1':
                venue_score = 0.2
            elif paper.get('venue_quartile') == 'Q2':
                venue_score = 0.1
            
            # Composite score (weighted combination)
            composite_score = (
                relevance_score * 0.4 +      # 40% relevance
                citation_score * 0.3 +       # 30% citations  
                recency_score * 0.2 +        # 20% recency
                venue_score * 0.1            # 10% venue quality
            )
            
            paper['composite_score'] = composite_score
        
        # Sort by composite score (descending)
        return sorted(papers, key=lambda x: x.get('composite_score', 0), reverse=True)
    
    def _final_validation(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform final validation on papers."""
        validated_papers = []
        
        for paper in papers:
            # Basic validation
            if not paper.get('title') or len(paper.get('title', '')) < 10:
                continue
            
            if not paper.get('authors'):
                continue
            
            # Add metadata
            paper['discovery_date'] = datetime.now().isoformat()
            paper['discovery_agent'] = 'enhanced_mcp'
            paper['validation_status'] = 'validated'
            
            # Add search tags for better organization
            paper['search_tags'] = self._generate_search_tags(paper)
            
            validated_papers.append(paper)
        
        return validated_papers
    
    def _generate_search_tags(self, paper: Dict[str, Any]) -> List[str]:
        """Generate search tags for paper organization."""
        tags = []
        
        # Add methodology tags
        if paper.get('methodology_category'):
            tags.append(f"method:{paper['methodology_category'].lower().replace(' ', '-')}")
        
        # Add domain tags
        if paper.get('application_domain'):
            tags.append(f"domain:{paper['application_domain'].lower().replace(' ', '-')}")
        
        # Add year tag
        if paper.get('year'):
            tags.append(f"year:{paper['year']}")
        
        # Add venue type tag
        venue_type = paper.get('venue_type', 'unknown')
        tags.append(f"type:{venue_type}")
        
        # Add quality tags
        if paper.get('citation_impact'):
            tags.append(f"impact:{paper['citation_impact']}")
        
        return tags
    
    def _get_default_phm_keywords(self) -> List[str]:
        """Get default PHM search keywords."""
        return [
            'prognostics and health management',
            'fault diagnosis',
            'predictive maintenance', 
            'condition monitoring',
            'remaining useful life',
            'anomaly detection',
            'failure prediction',
            'degradation modeling',
            'health assessment',
            'bearing fault diagnosis',
            'vibration analysis',
            'signal processing PHM'
        ]


# Additional utility functions for paper processing

def create_paper_summary(paper: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary representation of a paper for display."""
    return {
        'title': paper.get('title', 'Unknown Title'),
        'authors': paper.get('authors', [])[:3],  # First 3 authors
        'year': paper.get('year', 'Unknown'),
        'venue': paper.get('venue', 'Unknown Venue'),
        'citation_count': paper.get('citation_count', 0),
        'phm_relevance': paper.get('phm_relevance_score', 0.0),
        'composite_score': paper.get('composite_score', 0.0),
        'doi': paper.get('doi'),
        'tldr': paper.get('tldr'),
        'tags': paper.get('search_tags', [])
    }


def export_papers_json(papers: List[Dict[str, Any]], filepath: str) -> bool:
    """Export papers to JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False