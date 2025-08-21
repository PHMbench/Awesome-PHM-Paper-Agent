#!/usr/bin/env python3
"""
APPA (Awesome-PHM-Paper-Agent) Main Orchestrator

This is the main entry point for the APPA system that coordinates all agents
to discover, analyze, and organize PHM research papers.
"""

import sys
import os
import argparse
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import load_config, ConfigError
from src.utils.logging_config import setup_logging, get_logger
from src.agents.paper_discovery_agent import PaperDiscoveryAgent
from src.agents.quality_curation_agent import QualityCurationAgent
from src.agents.content_analysis_agent import ContentAnalysisAgent
from src.agents.filesystem_organization_agent import FileSystemOrganizationAgent
from src.agents.cross_reference_linking_agent import CrossReferenceLinkingAgent


class APPAOrchestrator:
    """
    Main orchestrator for the APPA system.
    
    Coordinates the execution of all agents in the correct sequence.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            # Load configuration
            self.config = load_config(config_path)
            
            # Setup logging
            setup_logging(self.config)
            self.logger = get_logger(__name__)
            
            # Initialize agents
            self.discovery_agent = PaperDiscoveryAgent(self.config)
            self.curation_agent = QualityCurationAgent(self.config)
            self.analysis_agent = ContentAnalysisAgent(self.config)
            self.organization_agent = FileSystemOrganizationAgent(self.config)
            self.linking_agent = CrossReferenceLinkingAgent(self.config)
            
            self.logger.info("APPA Orchestrator initialized successfully")
            
        except ConfigError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Initialization error: {e}")
            sys.exit(1)
    
    def run_full_pipeline(self, incremental: bool = False) -> Dict[str, Any]:
        """
        Run the complete APPA pipeline.
        
        Args:
            incremental: Whether to run incremental update
            
        Returns:
            Dictionary with pipeline execution results
        """
        self.logger.info("Starting APPA full pipeline execution")
        start_time = datetime.now()
        
        pipeline_results = {
            'start_time': start_time.isoformat(),
            'incremental': incremental,
            'phases': {}
        }
        
        try:
            # Phase 1: Paper Discovery
            self.logger.info("Phase 1: Paper Discovery")
            discovery_input = self._prepare_discovery_input(incremental)
            discovered_papers = self.discovery_agent.run(discovery_input)
            pipeline_results['phases']['discovery'] = {
                'papers_found': len(discovered_papers),
                'status': 'completed'
            }
            
            if not discovered_papers:
                self.logger.warning("No papers discovered, stopping pipeline")
                return pipeline_results
            
            # Phase 2: Quality Curation
            self.logger.info("Phase 2: Quality Curation")
            curated_papers = self.curation_agent.run(discovered_papers)
            pipeline_results['phases']['curation'] = {
                'papers_curated': len(curated_papers),
                'status': 'completed'
            }
            
            if not curated_papers:
                self.logger.warning("No papers passed quality curation, stopping pipeline")
                return pipeline_results
            
            # Phase 3: Content Analysis
            self.logger.info("Phase 3: Content Analysis")
            analyzed_papers = self.analysis_agent.run(curated_papers)
            pipeline_results['phases']['analysis'] = {
                'papers_analyzed': len(analyzed_papers),
                'status': 'completed'
            }
            
            # Phase 4: File System Organization
            self.logger.info("Phase 4: File System Organization")
            organization_results = self.organization_agent.run(analyzed_papers)
            pipeline_results['phases']['organization'] = organization_results
            
            # Phase 5: Cross-Reference Linking
            self.logger.info("Phase 5: Cross-Reference Linking")
            linking_input = {
                'papers': analyzed_papers,
                'file_structure': organization_results
            }
            linking_results = self.linking_agent.run(linking_input)
            pipeline_results['phases']['linking'] = linking_results
            
            # Update incremental date if successful
            if incremental:
                self._update_incremental_date()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            pipeline_results.update({
                'end_time': end_time.isoformat(),
                'duration_seconds': duration,
                'status': 'completed',
                'total_papers_processed': len(analyzed_papers)
            })
            
            self.logger.info(f"APPA pipeline completed successfully in {duration:.2f} seconds")
            self.logger.info(f"Processed {len(analyzed_papers)} papers")
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            pipeline_results.update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            raise
        
        return pipeline_results
    
    def run_discovery_only(self, incremental: bool = False) -> List[Dict[str, Any]]:
        """
        Run only the paper discovery phase.
        
        Args:
            incremental: Whether to run incremental discovery
            
        Returns:
            List of discovered papers
        """
        self.logger.info("Running paper discovery only")
        
        discovery_input = self._prepare_discovery_input(incremental)
        discovered_papers = self.discovery_agent.run(discovery_input)
        
        self.logger.info(f"Discovery completed: {len(discovered_papers)} papers found")
        return discovered_papers
    
    def run_analysis_only(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Run only the content analysis phase.
        
        Args:
            papers: List of papers to analyze
            
        Returns:
            List of analyzed papers
        """
        self.logger.info(f"Running content analysis for {len(papers)} papers")
        
        analyzed_papers = self.analysis_agent.run(papers)
        
        self.logger.info(f"Analysis completed: {len(analyzed_papers)} papers analyzed")
        return analyzed_papers
    
    def validate_links_only(self) -> Dict[str, Any]:
        """
        Run only link validation.
        
        Returns:
            Link validation results
        """
        self.logger.info("Running link validation only")
        
        # Create dummy input for link validation
        linking_input = {
            'papers': [],
            'file_structure': {}
        }
        
        # Run only validation part
        validation_results = self.linking_agent._validate_all_links()
        
        self.logger.info("Link validation completed")
        return validation_results
    
    def _prepare_discovery_input(self, incremental: bool) -> Dict[str, Any]:
        """Prepare input for paper discovery agent."""
        search_params = self.config.get('search_parameters', {})
        
        discovery_input = {
            'keywords': search_params.get('keywords', []),
            'date_range': search_params.get('time_range', '2020-2024'),
            'max_results_per_source': search_params.get('max_results_per_source', 100)
        }
        
        if incremental:
            discovery_input['incremental_date'] = search_params.get('incremental_update_date')
        
        return discovery_input
    
    def _update_incremental_date(self) -> None:
        """Update incremental update date in configuration."""
        from src.utils.config import update_config_value, save_config
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        update_config_value(self.config, 'search_parameters.incremental_update_date', current_date)
        save_config(self.config)
        
        self.logger.info(f"Updated incremental update date to {current_date}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and statistics."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'config_loaded': bool(self.config),
            'agents_initialized': True,
            'base_directories': {
                'papers': os.path.exists('papers'),
                'topics': os.path.exists('topics'),
                'venues': os.path.exists('venues'),
                'authors': os.path.exists('authors'),
                'indices': os.path.exists('indices')
            }
        }
        
        # Count existing papers
        papers_dir = 'papers'
        if os.path.exists(papers_dir):
            paper_count = 0
            for year_dir in os.listdir(papers_dir):
                year_path = os.path.join(papers_dir, year_dir)
                if os.path.isdir(year_path):
                    paper_count += len([d for d in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, d))])
            status['total_papers'] = paper_count
        else:
            status['total_papers'] = 0
        
        return status


def main():
    """Main entry point for APPA system."""
    parser = argparse.ArgumentParser(description='APPA - Awesome PHM Paper Agent')
    parser.add_argument('--config', '-c', default='config.yaml', help='Configuration file path')
    parser.add_argument('--incremental', '-i', action='store_true', help='Run incremental update')
    parser.add_argument('--discovery-only', action='store_true', help='Run only paper discovery')
    parser.add_argument('--validate-links', action='store_true', help='Run only link validation')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        orchestrator = APPAOrchestrator(args.config)
        
        if args.status:
            # Show system status
            status = orchestrator.get_system_status()
            print("APPA System Status:")
            print(f"  Total papers: {status['total_papers']}")
            print(f"  Base directories exist: {all(status['base_directories'].values())}")
            print(f"  Last check: {status['timestamp']}")
            
        elif args.discovery_only:
            # Run discovery only
            papers = orchestrator.run_discovery_only(args.incremental)
            print(f"Discovery completed: {len(papers)} papers found")
            
        elif args.validate_links:
            # Run link validation only
            results = orchestrator.validate_links_only()
            print(f"Link validation completed:")
            print(f"  Internal links: {results.get('internal_links_validated', 0)}")
            print(f"  External links: {results.get('external_links_validated', 0)}")
            print(f"  Broken links: {results.get('broken_links_found', 0)}")
            
        else:
            # Run full pipeline
            results = orchestrator.run_full_pipeline(args.incremental)
            print(f"APPA pipeline completed:")
            print(f"  Status: {results['status']}")
            print(f"  Duration: {results.get('duration_seconds', 0):.2f} seconds")
            print(f"  Papers processed: {results.get('total_papers_processed', 0)}")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
