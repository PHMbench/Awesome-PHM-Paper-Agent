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
# Legacy agent imports removed - now using Claude Code agents directly
# Only keep essential utilities for configuration and status


class APPAStatusManager:
    """
    Simplified status manager for the APPA system.
    
    Provides system status, configuration management, and logging support
    for Claude Code agent operations.
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
            
            self.logger.info("APPA Status Manager initialized - using Claude Code agents")
            
        except ConfigError as e:
            print(f"Configuration error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Initialization error: {e}")
            sys.exit(1)
    
    def run_full_pipeline(self, incremental: bool = False) -> Dict[str, Any]:
        """
        Legacy method - now returns information about using Claude Code agents.
        
        The actual pipeline execution should be done using Claude Code agents:
        - academic-researcher for paper discovery
        - phm-quality-curator for quality curation
        - phm-content-analyzer for content analysis
        - phm-knowledge-organizer for organization
        - phm-relationship-builder for linking
        """
        self.logger.warning("run_full_pipeline is deprecated - use Claude Code agents instead")
        
        return {
            'status': 'deprecated',
            'message': 'Please use Claude Code agents directly',
            'recommended_approach': [
                '1. Use academic-researcher agent for paper discovery',
                '2. Use phm-quality-curator agent for quality filtering',
                '3. Use phm-content-analyzer agent for content analysis',
                '4. Use phm-knowledge-organizer agent for organization',
                '5. Use phm-relationship-builder agent for cross-referencing'
            ],
            'shell_scripts': [
                './scripts/daily_greeting.sh - for daily updates',
                './scripts/search_papers.sh - for paper search'
            ]
        }
    
    def run_discovery_only(self, incremental: bool = False) -> List[Dict[str, Any]]:
        """
        Legacy method - use academic-researcher agent instead.
        """
        self.logger.warning("run_discovery_only is deprecated - use academic-researcher agent instead")
        return []
    
    def run_analysis_only(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Legacy method - use phm-content-analyzer agent instead.
        """
        self.logger.warning("run_analysis_only is deprecated - use phm-content-analyzer agent instead")
        return []
    
    def validate_links_only(self) -> Dict[str, Any]:
        """
        Legacy method - use phm-relationship-builder agent instead.
        """
        self.logger.warning("validate_links_only is deprecated - use phm-relationship-builder agent instead")
        return {'status': 'deprecated', 'message': 'Use phm-relationship-builder agent'}
    
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
            'system_type': 'Claude Code Agent Based',
            'architecture': 'Shell Scripts → Claude Code Agents → Support Utils',
            'base_directories': {
                'papers': os.path.exists('papers'),
                'topics': os.path.exists('topics'),
                'venues': os.path.exists('venues'),
                'authors': os.path.exists('authors'),
                'indices': os.path.exists('indices')
            },
            'available_scripts': {
                'daily_greeting': os.path.exists('scripts/daily_greeting.sh'),
                'search_papers': os.path.exists('scripts/search_papers.sh'),
                'validate_awesome': os.path.exists('scripts/awesome-validate.sh')
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
    """Main entry point for APPA system status and configuration management."""
    parser = argparse.ArgumentParser(
        description='APPA - Awesome PHM Paper Agent (Status Manager)',
        epilog='Note: APPA now uses Claude Code agents. Use shell scripts for operations.'
    )
    parser.add_argument('--config', '-c', default='config.yaml', help='Configuration file path')
    parser.add_argument('--incremental', '-i', action='store_true', help='Run incremental update')
    parser.add_argument('--discovery-only', action='store_true', help='Run only paper discovery')
    parser.add_argument('--validate-links', action='store_true', help='Run only link validation')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    try:
        # Initialize status manager
        status_manager = APPAStatusManager(args.config)
        
        if args.status:
            # Show system status
            status = status_manager.get_system_status()
            print("APPA System Status:")
            print(f"  Architecture: {status['system_type']}")
            print(f"  Total papers: {status['total_papers']}")
            print(f"  Base directories exist: {all(status['base_directories'].values())}")
            print(f"  Scripts available: {all(status['available_scripts'].values())}")
            print(f"  Last check: {status['timestamp']}")
            print("\n💡 Use shell scripts to interact with Claude Code agents:")
            print("  ./scripts/daily_greeting.sh - Daily status and updates")
            print("  ./scripts/search_papers.sh - Search and manage papers")
            
        elif args.discovery_only:
            # Legacy method - show guidance
            print("⚠️  Discovery-only mode is deprecated.")
            print("💡 Use: academic-researcher agent via Claude Code instead")
            
        elif args.validate_links:
            # Legacy method - show guidance
            print("⚠️  Link validation mode is deprecated.")
            print("💡 Use: phm-relationship-builder agent via Claude Code instead")
            
        else:
            # Legacy pipeline - show guidance
            print("⚠️  Full pipeline mode is deprecated.")
            print("💡 APPA now uses Claude Code agents directly:")
            print("  1. academic-researcher - for paper discovery")
            print("  2. phm-quality-curator - for quality filtering")
            print("  3. phm-content-analyzer - for content analysis")
            print("  4. phm-knowledge-organizer - for organization")
            print("  5. phm-relationship-builder - for cross-referencing")
            print("\n🚀 Quick start: ./scripts/daily_greeting.sh")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
