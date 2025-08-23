#!/usr/bin/env python3
"""
Fetch Recent PHM Papers Script

This script demonstrates the enhanced paper discovery capabilities using
the new MCP-integrated system to fetch real PHM papers from academic databases.

Usage:
    python scripts/fetch_recent_papers.py --help
    python scripts/fetch_recent_papers.py --keywords "fault diagnosis" "predictive maintenance" --max-results 10
    python scripts/fetch_recent_papers.py --date-after "2025-05-01" --output papers_2025.json
"""

import argparse
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.agents.enhanced_paper_discovery_agent import EnhancedPaperDiscoveryAgent
from src.agents.content_analysis_agent import ContentAnalysisAgent
from src.utils.pdf_downloader import PDFDownloader, PaperValidator
from src.utils.logging_config import setup_logging, get_logger


def create_default_config():
    """Create default configuration for the agents."""
    return {
        'logging': {
            'level': 'INFO',
            'console_output': True,
            'file_output': False
        },
        'mcp_tools': {
            'academic_researcher_enabled': True,
            'max_results_per_query': 50,
            'timeout_seconds': 120
        },
        'discovery_settings': {
            'max_results_per_source': 100,
            'enable_pdf_download': True,
            'enable_citation_enhancement': True,
            'minimum_relevance_score': 0.3
        },
        'content_analysis': {
            'include_reproducibility': True,
            'include_impact_analysis': True,
            'include_methodology_extraction': True,
            'enable_multilingual': True
        },
        'output_preferences': {
            'summary_length': 'medium'
        },
        'pdf_downloader': {
            'download_directory': 'downloads/pdfs',
            'max_file_size_mb': 50,
            'timeout_seconds': 30,
            'max_retries': 3
        },
        'paper_validator': {
            'timeout_seconds': 10,
            'enable_crossref': True,
            'enable_orcid': False
        }
    }


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Fetch recent PHM papers using enhanced discovery system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch papers on bearing fault diagnosis
  python scripts/fetch_recent_papers.py --keywords "bearing fault" "diagnosis"
  
  # Fetch papers after May 2025 
  python scripts/fetch_recent_papers.py --date-after "2025-05-01"
  
  # Fetch papers with custom settings
  python scripts/fetch_recent_papers.py --max-results 20 --include-preprints --output results.json
  
  # Fetch and analyze papers
  python scripts/fetch_recent_papers.py --analyze --download-pdfs
        """
    )
    
    # Search parameters
    parser.add_argument('--keywords', nargs='+', 
                       default=['prognostics', 'health management', 'fault diagnosis'],
                       help='Keywords to search for (default: prognostics, health management, fault diagnosis)')
    
    parser.add_argument('--date-range', 
                       default='2023-2025',
                       help='Date range in format YYYY-YYYY (default: 2023-2025)')
    
    parser.add_argument('--date-after', 
                       help='Only include papers after this date (ISO format: YYYY-MM-DD)')
    
    parser.add_argument('--max-results', type=int, 
                       default=20,
                       help='Maximum number of papers to fetch (default: 20)')
    
    parser.add_argument('--research-areas', nargs='+',
                       help='Specific research areas to filter by')
    
    parser.add_argument('--include-preprints', action='store_true',
                       help='Include preprints (arXiv, etc.)')
    
    # Processing options
    parser.add_argument('--analyze', action='store_true',
                       help='Run content analysis on fetched papers')
    
    parser.add_argument('--download-pdfs', action='store_true',
                       help='Attempt to download PDFs for papers')
    
    parser.add_argument('--validate', action='store_true',
                       help='Validate paper metadata and citations')
    
    # Output options
    parser.add_argument('--output', '-o',
                       help='Output file for results (JSON format)')
    
    parser.add_argument('--create-pages', action='store_true',
                       help='Create markdown pages for each paper')
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    # Demo mode
    parser.add_argument('--demo', action='store_true',
                       help='Run demonstration with sample queries')
    
    return parser.parse_args()


def setup_demo_queries():
    """Setup demonstration queries."""
    return [
        {
            'name': '2025年最新PHM论文',
            'keywords': ['prognostics', 'health management', 'predictive maintenance'],
            'date_after': '2025-05-01',
            'max_results': 5
        },
        {
            'name': '深度学习故障诊断',
            'keywords': ['deep learning', 'fault diagnosis', 'neural network'],
            'research_areas': ['bearing fault diagnosis', 'rotating machinery'],
            'max_results': 3
        },
        {
            'name': '轴承健康监测最新进展',
            'keywords': ['bearing', 'health monitoring', 'condition monitoring'],
            'date_range': '2024-2025',
            'max_results': 3
        }
    ]


def run_paper_discovery(config, search_params, logger):
    """Run paper discovery with given parameters."""
    try:
        logger.info(f"🔍 Starting paper discovery...")
        logger.info(f"Keywords: {search_params.get('keywords', [])}")
        logger.info(f"Date range: {search_params.get('date_range', 'N/A')}")
        logger.info(f"Max results: {search_params.get('max_results', 'N/A')}")
        
        # Initialize enhanced discovery agent
        discovery_agent = EnhancedPaperDiscoveryAgent(config)
        
        # Run discovery
        papers = discovery_agent.process(search_params)
        
        logger.info(f"✅ Found {len(papers)} papers")
        return papers
        
    except Exception as e:
        logger.error(f"❌ Paper discovery failed: {e}")
        return []


def run_content_analysis(config, papers, logger):
    """Run content analysis on papers."""
    try:
        logger.info(f"📊 Starting content analysis for {len(papers)} papers...")
        
        # Initialize content analysis agent
        analysis_agent = ContentAnalysisAgent(config)
        
        # Run analysis
        analyzed_papers = analysis_agent.process(papers)
        
        logger.info(f"✅ Analysis completed")
        return analyzed_papers
        
    except Exception as e:
        logger.error(f"❌ Content analysis failed: {e}")
        return papers  # Return original papers if analysis fails


def download_pdfs(config, papers, logger):
    """Download PDFs for papers."""
    try:
        logger.info(f"📥 Starting PDF download for {len(papers)} papers...")
        
        # Initialize PDF downloader
        pdf_downloader = PDFDownloader(config)
        
        download_count = 0
        for paper in papers:
            try:
                pdf_path = pdf_downloader.download_paper_pdf(paper)
                if pdf_path:
                    paper['pdf_downloaded'] = True
                    paper['pdf_path'] = pdf_path
                    download_count += 1
                else:
                    paper['pdf_downloaded'] = False
            except Exception as e:
                logger.warning(f"PDF download failed for {paper.get('title', 'Unknown')}: {e}")
                paper['pdf_downloaded'] = False
        
        logger.info(f"✅ Downloaded {download_count} PDFs")
        return papers
        
    except Exception as e:
        logger.error(f"❌ PDF download failed: {e}")
        return papers


def validate_papers(config, papers, logger):
    """Validate paper metadata."""
    try:
        logger.info(f"✅ Starting validation for {len(papers)} papers...")
        
        # Initialize paper validator
        validator = PaperValidator(config)
        
        validated_papers = []
        for paper in papers:
            try:
                validated_paper = validator.validate_paper(paper)
                validated_papers.append(validated_paper)
            except Exception as e:
                logger.warning(f"Validation failed for {paper.get('title', 'Unknown')}: {e}")
                validated_papers.append(paper)  # Include anyway
        
        logger.info(f"✅ Validation completed")
        return validated_papers
        
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        return papers


def save_results(papers, output_path, logger):
    """Save results to JSON file."""
    try:
        # Prepare output data
        output_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_papers': len(papers),
                'discovery_agent': 'enhanced_mcp',
                'version': '2.0'
            },
            'papers': papers
        }
        
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save results: {e}")


def print_paper_summary(papers, logger):
    """Print a summary of discovered papers."""
    if not papers:
        logger.info("No papers found.")
        return
    
    logger.info("\n" + "="*60)
    logger.info(f"📚 PAPER DISCOVERY SUMMARY - {len(papers)} Papers Found")
    logger.info("="*60)
    
    for i, paper in enumerate(papers, 1):
        title = paper.get('title', 'Unknown Title')[:80]
        if len(paper.get('title', '')) > 80:
            title += "..."
        
        authors = paper.get('authors', [])
        author_str = ', '.join(authors[:2])  # First 2 authors
        if len(authors) > 2:
            author_str += f" et al. ({len(authors)} authors)"
        
        year = paper.get('year', 'N/A')
        venue = paper.get('venue', 'Unknown')[:40]
        citations = paper.get('citation_count', 0)
        
        # PHM relevance
        relevance = paper.get('phm_relevance_score', 0.0)
        
        # Analysis info
        analysis_status = "N/A"
        if paper.get('analysis'):
            analysis_status = paper['analysis'].get('analysis_status', 'unknown')
        
        logger.info(f"\n{i:2d}. {title}")
        logger.info(f"    👥 Authors: {author_str}")
        logger.info(f"    📅 Year: {year} | 📖 Venue: {venue}")
        logger.info(f"    📊 Citations: {citations} | 🎯 PHM Relevance: {relevance:.2f}")
        logger.info(f"    📝 Analysis: {analysis_status}")
        
        # Show TL;DR if available
        if paper.get('analysis', {}).get('tldr', {}).get('chinese'):
            tldr = paper['analysis']['tldr']['chinese']
            logger.info(f"    💡 TL;DR: {tldr}")
        
        # Show DOI if available
        if paper.get('doi'):
            logger.info(f"    🔗 DOI: {paper['doi']}")
    
    logger.info("\n" + "="*60)


def run_demo_mode(config, logger):
    """Run demonstration mode with sample queries."""
    logger.info("🎭 Running demonstration mode...")
    
    demo_queries = setup_demo_queries()
    all_papers = []
    
    for query in demo_queries:
        logger.info(f"\n🔍 Demo Query: {query['name']}")
        logger.info("-" * 40)
        
        # Prepare search parameters
        search_params = {
            'keywords': query.get('keywords', []),
            'date_range': query.get('date_range', '2023-2025'),
            'max_results': query.get('max_results', 5),
            'research_areas': query.get('research_areas'),
            'specific_date_after': query.get('date_after'),
            'include_preprints': True
        }
        
        # Run discovery
        papers = run_paper_discovery(config, search_params, logger)
        
        if papers:
            logger.info(f"Found {len(papers)} papers for '{query['name']}'")
            all_papers.extend(papers)
        else:
            logger.warning(f"No papers found for '{query['name']}'")
    
    logger.info(f"\n🎯 Demo Results: {len(all_papers)} total papers found")
    print_paper_summary(all_papers, logger)
    
    return all_papers


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Setup configuration
    config = create_default_config()
    if args.verbose:
        config['logging']['level'] = 'DEBUG'
    
    # Setup logging
    setup_logging(config)
    logger = get_logger(__name__)
    
    logger.info("🚀 Enhanced PHM Paper Discovery System")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run demo mode or regular mode
        if args.demo:
            papers = run_demo_mode(config, logger)
        else:
            # Prepare search parameters
            search_params = {
                'keywords': args.keywords,
                'date_range': args.date_range,
                'max_results': args.max_results,
                'research_areas': args.research_areas,
                'specific_date_after': args.date_after,
                'include_preprints': args.include_preprints
            }
            
            # Run paper discovery
            papers = run_paper_discovery(config, search_params, logger)
        
        if not papers:
            logger.warning("❌ No papers found with current search parameters")
            return
        
        # Run content analysis if requested
        if args.analyze:
            papers = run_content_analysis(config, papers, logger)
        
        # Download PDFs if requested
        if args.download_pdfs:
            papers = download_pdfs(config, papers, logger)
        
        # Validate papers if requested
        if args.validate:
            papers = validate_papers(config, papers, logger)
        
        # Save results if output file specified
        if args.output:
            save_results(papers, args.output, logger)
        
        # Print summary
        if not args.demo:  # Already printed in demo mode
            print_paper_summary(papers, logger)
        
        # Success message
        logger.info(f"\n🎉 Paper discovery completed successfully!")
        logger.info(f"Found and processed {len(papers)} papers")
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()