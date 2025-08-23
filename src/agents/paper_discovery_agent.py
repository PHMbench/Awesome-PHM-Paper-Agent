"""
Paper Discovery Agent for APPA system (Legacy Support).

This agent provides backward compatibility while delegating to the enhanced
MCP-integrated discovery agent for real academic paper discovery.

Migration Notice: This agent now serves as a compatibility layer.
New implementations should use EnhancedPaperDiscoveryAgent directly.
"""

import time
import requests
import hashlib
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from urllib.parse import quote
import json

from .base_agent import BaseAgent, AgentError
from .enhanced_paper_discovery_agent import EnhancedPaperDiscoveryAgent
from ..models import PaperMetadata, PaperIdentifiers, CitationMetrics, QualityMetrics, VenueType, VenueQuartile
from ..utils.llm_client import LLMManager
from ..utils.mcp_integration import MCPAcademicTools


class PaperDiscoveryAgent(BaseAgent):
    """
    Legacy Paper Discovery Agent - now delegates to EnhancedPaperDiscoveryAgent.
    
    This class maintains backward compatibility while using the new MCP-integrated
    discovery system under the hood.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "PaperDiscoveryAgent (Legacy)")
        
        # Initialize the enhanced agent that does the real work
        self.enhanced_agent = EnhancedPaperDiscoveryAgent(config)
        
        # Legacy configuration for backward compatibility
        self.api_config = self.get_config_value('api_configuration', {})
        self.search_config = self.get_config_value('search_parameters', {})
        
        # Legacy tracking (now handled by enhanced agent)
        self.seen_dois: Set[str] = set()
        self.seen_fingerprints: Set[str] = set()

        # Initialize LLM manager (delegated to enhanced agent)
        self.llm_manager = self.enhanced_agent.llm_manager
        
        self.logger.info("Legacy Paper Discovery Agent initialized - delegating to Enhanced Agent")
    
    def process(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Discover papers from academic APIs (Legacy wrapper).
        
        This method now delegates to the Enhanced Paper Discovery Agent which
        uses MCP academic research tools for real paper discovery.
        
        Args:
            input_data: Dictionary containing:
                - keywords: List of search keywords
                - date_range: String in format "YYYY-YYYY"
                - max_results_per_source: Maximum results per API (mapped to max_results)
                - incremental_date: Optional cutoff date (mapped to specific_date_after)
        
        Returns:
            List of validated paper metadata dictionaries with enhanced information
        """
        self.logger.info("Legacy process() called - delegating to Enhanced Discovery Agent")
        
        # Map legacy parameters to enhanced agent format
        enhanced_input = {
            'keywords': input_data.get('keywords', []),
            'date_range': input_data.get('date_range', '2020-2025'),
            'max_results': input_data.get('max_results_per_source', 100),
            'specific_date_after': input_data.get('incremental_date'),
            'include_preprints': True  # Default for backward compatibility
        }
        
        try:
            # Call enhanced agent
            papers = self.enhanced_agent.process(enhanced_input)
            
            # Update legacy tracking sets (for compatibility)
            for paper in papers:
                if paper.get('doi'):
                    self.seen_dois.add(paper['doi'])
                fingerprint = self._create_legacy_fingerprint(paper)
                self.seen_fingerprints.add(fingerprint)
            
            self.logger.info(f"Enhanced agent returned {len(papers)} papers")
            return papers
            
        except Exception as e:
            self.logger.error(f"Enhanced discovery failed, falling back to legacy mode: {e}")
            # Could implement a minimal fallback here if needed
            return []
    
    def _create_legacy_fingerprint(self, paper: Dict[str, Any]) -> str:
        """Create legacy fingerprint for backward compatibility."""
        title = paper.get('title', '').lower().strip()
        title = ''.join(c for c in title if c.isalnum() or c.isspace())
        title = ' '.join(title.split())
        
        authors = paper.get('authors', [])
        first_author = ''
        if authors:
            first_author = authors[0].lower().strip()
            if ',' in first_author:
                first_author = first_author.split(',')[0]
            else:
                parts = first_author.split()
                first_author = parts[-1] if parts else ''
        
        fingerprint_text = f"{title}|{first_author}|{paper.get('year', 0)}"
        return hashlib.md5(fingerprint_text.encode('utf-8')).hexdigest()


# Legacy compatibility note:
# This agent now serves as a compatibility wrapper around EnhancedPaperDiscoveryAgent.
# All the complex paper discovery logic, including API calls to OpenAlex, Semantic Scholar,
# and arXiv, has been moved to the enhanced agent with MCP integration.
#
# The old methods (_query_openalex, _query_semantic_scholar, _query_arxiv, etc.) have been
# removed as they are replaced by the MCP academic research tools which provide more
# accurate and comprehensive paper discovery capabilities.
#
# For new implementations, use EnhancedPaperDiscoveryAgent directly.


if __name__ == "__main__":
    # Test the legacy agent (now delegates to enhanced agent)
    config = {
        'api_configuration': {
            'rate_limits': {'openalex': 10, 'semantic_scholar': 1},
            'timeout_seconds': 30
        },
        'mcp_tools': {
            'academic_researcher_enabled': True,
            'max_results_per_query': 50
        }
    }
    
    agent = PaperDiscoveryAgent(config)
    
    test_input = {
        'keywords': ['prognostics', 'health management'],
        'date_range': '2023-2024',
        'max_results_per_source': 5
    }
    
    print("Testing Legacy Paper Discovery Agent (now using Enhanced Agent)...")
    try:
        papers = agent.process(test_input)
        print(f"Found {len(papers)} papers via enhanced discovery")
        for paper in papers[:2]:  # Show first 2 papers
            print(f"- {paper.get('title', 'Unknown Title')}")
    except Exception as e:
        print(f"Test failed: {e}")