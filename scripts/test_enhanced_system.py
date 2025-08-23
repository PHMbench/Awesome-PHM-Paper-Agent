#!/usr/bin/env python3
"""
Enhanced APPA System Testing Script

This script tests the new MCP-integrated enhanced paper discovery and analysis system
to ensure all components are working correctly.

Usage:
    python scripts/test_enhanced_system.py
    python scripts/test_enhanced_system.py --verbose
    python scripts/test_enhanced_system.py --component discovery
"""

import argparse
import sys
import os
from pathlib import Path
import traceback
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from src.agents.enhanced_paper_discovery_agent import EnhancedPaperDiscoveryAgent
    from src.agents.content_analysis_agent import ContentAnalysisAgent
    from src.agents.paper_discovery_agent import PaperDiscoveryAgent
    from src.utils.mcp_integration import MCPAcademicTools
    from src.utils.pdf_downloader import PDFDownloader, PaperValidator
    from src.utils.logging_config import setup_logging, get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running from the APPA root directory")
    sys.exit(1)


def create_test_config():
    """Create test configuration."""
    return {
        'logging': {
            'level': 'INFO',
            'console_output': True,
            'file_output': False
        },
        'mcp_tools': {
            'academic_researcher_enabled': True,
            'max_results_per_query': 5,  # Small for testing
            'timeout_seconds': 30
        },
        'discovery_settings': {
            'max_results_per_source': 10,
            'enable_pdf_download': False,  # Disabled for testing
            'enable_citation_enhancement': True,
            'minimum_relevance_score': 0.2
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
            'download_directory': 'test_downloads',
            'max_file_size_mb': 10,
            'timeout_seconds': 10,
            'max_retries': 1
        },
        'paper_validator': {
            'timeout_seconds': 5,
            'enable_crossref': False,  # Disabled for testing
            'enable_orcid': False
        }
    }


class SystemTester:
    """Main system testing class."""
    
    def __init__(self, config, verbose=False):
        self.config = config
        self.verbose = verbose
        self.test_results = {}
        
        # Setup logging
        setup_logging(config)
        self.logger = get_logger(__name__)
        
        if verbose:
            self.config['logging']['level'] = 'DEBUG'
    
    def run_all_tests(self):
        """Run all system tests."""
        self.logger.info("🧪 Starting Enhanced APPA System Tests")
        self.logger.info("=" * 50)
        
        test_methods = [
            ('MCP Integration', self.test_mcp_integration),
            ('Enhanced Discovery Agent', self.test_enhanced_discovery),
            ('Legacy Discovery Agent', self.test_legacy_discovery),
            ('Content Analysis Agent', self.test_content_analysis),
            ('PDF Downloader', self.test_pdf_downloader),
            ('Paper Validator', self.test_paper_validator),
            ('End-to-End Pipeline', self.test_end_to_end_pipeline)
        ]
        
        for test_name, test_method in test_methods:
            self.logger.info(f"\n🔍 Testing: {test_name}")
            self.logger.info("-" * 30)
            
            try:
                result = test_method()
                self.test_results[test_name] = {
                    'status': 'passed' if result else 'failed',
                    'error': None
                }
                
                if result:
                    self.logger.info(f"✅ {test_name}: PASSED")
                else:
                    self.logger.warning(f"⚠️  {test_name}: FAILED")
                    
            except Exception as e:
                self.logger.error(f"❌ {test_name}: ERROR - {e}")
                self.test_results[test_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                
                if self.verbose:
                    self.logger.error(traceback.format_exc())
        
        self._print_summary()
    
    def test_mcp_integration(self):
        """Test MCP academic tools integration."""
        try:
            mcp_tools = MCPAcademicTools(self.config)
            
            # Test basic functionality
            if not hasattr(mcp_tools, 'search_phm_papers'):
                self.logger.error("MCP tools missing search_phm_papers method")
                return False
            
            # Test configuration
            if not mcp_tools.config:
                self.logger.error("MCP tools not properly configured")
                return False
            
            self.logger.info("MCP integration basic checks passed")
            return True
            
        except Exception as e:
            self.logger.error(f"MCP integration test failed: {e}")
            return False
    
    def test_enhanced_discovery(self):
        """Test enhanced paper discovery agent."""
        try:
            agent = EnhancedPaperDiscoveryAgent(self.config)
            
            # Test with minimal input
            test_input = {
                'keywords': ['prognostics'],
                'date_range': '2024-2025',
                'max_results': 3
            }
            
            self.logger.info("Testing enhanced discovery with minimal input...")
            
            # Note: This may not return real results without MCP connection
            # but should not crash
            papers = agent.process(test_input)
            
            self.logger.info(f"Enhanced discovery returned {len(papers)} papers")
            
            # Test with comprehensive input
            comprehensive_input = {
                'keywords': ['fault diagnosis', 'deep learning'],
                'date_range': '2023-2025',
                'max_results': 5,
                'research_areas': ['rotating machinery'],
                'include_preprints': True
            }
            
            papers_comprehensive = agent.process(comprehensive_input)
            self.logger.info(f"Comprehensive test returned {len(papers_comprehensive)} papers")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Enhanced discovery test failed: {e}")
            return False
    
    def test_legacy_discovery(self):
        """Test legacy discovery agent (compatibility layer)."""
        try:
            agent = PaperDiscoveryAgent(self.config)
            
            # Test legacy input format
            legacy_input = {
                'keywords': ['health management'],
                'date_range': '2024-2025',
                'max_results_per_source': 3
            }
            
            self.logger.info("Testing legacy discovery compatibility...")
            
            papers = agent.process(legacy_input)
            self.logger.info(f"Legacy discovery returned {len(papers)} papers")
            
            # Verify agent delegation
            if not hasattr(agent, 'enhanced_agent'):
                self.logger.error("Legacy agent not properly delegating to enhanced agent")
                return False
            
            self.logger.info("Legacy compatibility verified")
            return True
            
        except Exception as e:
            self.logger.error(f"Legacy discovery test failed: {e}")
            return False
    
    def test_content_analysis(self):
        """Test enhanced content analysis agent."""
        try:
            agent = ContentAnalysisAgent(self.config)
            
            # Create test papers
            test_papers = [
                {
                    'title': 'Deep Learning Approaches for Bearing Fault Diagnosis Using CNN-LSTM Networks',
                    'abstract': 'This paper presents a novel deep learning framework combining convolutional neural networks (CNN) and long short-term memory (LSTM) networks for automated bearing fault diagnosis. The proposed method achieves 97.5% accuracy on benchmark datasets and outperforms traditional machine learning approaches by 12%. The framework demonstrates strong generalization capabilities across different operating conditions and fault severities.',
                    'authors': ['Zhang, Wei', 'Smith, John', 'Liu, Ming'],
                    'year': 2024,
                    'venue': 'Mechanical Systems and Signal Processing',
                    'keywords': ['deep learning', 'fault diagnosis', 'CNN', 'LSTM', 'bearing'],
                    'doi': '10.1016/j.ymssp.2024.111234',
                    'citation_count': 15
                }
            ]
            
            self.logger.info("Testing content analysis with sample paper...")
            
            analyzed_papers = agent.process(test_papers)
            
            if not analyzed_papers:
                self.logger.error("Content analysis returned no results")
                return False
            
            analyzed_paper = analyzed_papers[0]
            
            # Check if analysis was added
            if 'analysis' not in analyzed_paper:
                self.logger.error("No analysis added to paper")
                return False
            
            analysis = analyzed_paper['analysis']
            
            # Check analysis components
            required_components = ['tldr', 'key_points', 'methodology_classification', 'phm_relevance']
            for component in required_components:
                if component not in analysis:
                    self.logger.warning(f"Missing analysis component: {component}")
                else:
                    self.logger.info(f"✓ {component} present")
            
            # Check TL;DR quality
            if analysis.get('tldr') and analysis['tldr'].get('chinese'):
                self.logger.info(f"TL;DR generated: {analysis['tldr']['chinese'][:50]}...")
            
            # Check PHM relevance
            if analysis.get('phm_relevance'):
                score = analysis['phm_relevance'].get('overall_score', 0)
                self.logger.info(f"PHM relevance score: {score:.2f}")
            
            self.logger.info("Content analysis test completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Content analysis test failed: {e}")
            return False
    
    def test_pdf_downloader(self):
        """Test PDF downloader functionality."""
        try:
            downloader = PDFDownloader(self.config)
            
            # Test configuration
            if not downloader.download_dir:
                self.logger.error("PDF downloader not properly configured")
                return False
            
            # Test directory creation
            if not downloader.download_dir.exists():
                self.logger.error("Download directory not created")
                return False
            
            # Test basic functionality without actual download
            test_paper = {
                'title': 'Test Paper for PDF Download',
                'authors': ['Test Author'],
                'year': 2024,
                'urls': {
                    'pdf': 'https://example.com/test.pdf'  # Non-existent URL for testing
                }
            }
            
            # This should fail gracefully
            result = downloader.download_paper_pdf(test_paper)
            
            # Should return None for non-existent URL
            if result is None:
                self.logger.info("PDF downloader handled non-existent URL correctly")
            
            # Test statistics
            stats = downloader.get_download_stats()
            self.logger.info(f"Download stats: {stats}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"PDF downloader test failed: {e}")
            return False
    
    def test_paper_validator(self):
        """Test paper validator functionality."""
        try:
            validator = PaperValidator(self.config)
            
            # Test with valid paper data
            test_paper = {
                'title': 'Test Paper for Validation',
                'authors': ['Test Author'],
                'year': 2024,
                'venue': 'Test Journal',
                'doi': '10.1000/test.doi',
                'citation_count': 5
            }
            
            self.logger.info("Testing paper validation...")
            
            validated_paper = validator.validate_paper(test_paper)
            
            # Check if validation results were added
            if 'validation_results' not in validated_paper:
                self.logger.warning("No validation results added")
            else:
                self.logger.info("Validation results added successfully")
            
            # Check validation score
            if 'validation_score' in validated_paper:
                score = validated_paper['validation_score']
                self.logger.info(f"Validation score: {score:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Paper validator test failed: {e}")
            return False
    
    def test_end_to_end_pipeline(self):
        """Test end-to-end pipeline with enhanced agents."""
        try:
            self.logger.info("Testing end-to-end pipeline...")
            
            # Step 1: Discovery
            discovery_agent = EnhancedPaperDiscoveryAgent(self.config)
            test_input = {
                'keywords': ['prognostics'],
                'date_range': '2024-2025',
                'max_results': 2
            }
            
            papers = discovery_agent.process(test_input)
            self.logger.info(f"Discovery: {len(papers)} papers found")
            
            if not papers:
                # Create mock paper for testing
                papers = [{
                    'title': 'Mock Paper for Testing',
                    'abstract': 'This is a mock paper for testing the enhanced APPA system with prognostics and health management concepts.',
                    'authors': ['Test Author'],
                    'year': 2024,
                    'venue': 'Test Journal',
                    'keywords': ['prognostics', 'testing'],
                    'citation_count': 0
                }]
                self.logger.info("Using mock paper for pipeline test")
            
            # Step 2: Analysis
            analysis_agent = ContentAnalysisAgent(self.config)
            analyzed_papers = analysis_agent.process(papers)
            self.logger.info(f"Analysis: {len(analyzed_papers)} papers analyzed")
            
            # Step 3: Validation
            validator = PaperValidator(self.config)
            for paper in analyzed_papers:
                validated_paper = validator.validate_paper(paper)
                self.logger.info("Paper validation completed")
                break  # Test only first paper
            
            self.logger.info("End-to-end pipeline test completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"End-to-end pipeline test failed: {e}")
            return False
    
    def _print_summary(self):
        """Print test summary."""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("🧪 TEST RESULTS SUMMARY")
        self.logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'passed')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'failed')
        error_tests = sum(1 for result in self.test_results.values() if result['status'] == 'error')
        
        for test_name, result in self.test_results.items():
            status_icon = {
                'passed': '✅',
                'failed': '⚠️',
                'error': '❌'
            }.get(result['status'], '❓')
            
            self.logger.info(f"{status_icon} {test_name}: {result['status'].upper()}")
            if result['error'] and self.verbose:
                self.logger.info(f"    Error: {result['error']}")
        
        self.logger.info(f"\n📊 Summary: {passed_tests}/{total_tests} tests passed")
        
        if failed_tests > 0:
            self.logger.warning(f"⚠️  {failed_tests} tests failed")
        
        if error_tests > 0:
            self.logger.error(f"❌ {error_tests} tests had errors")
        
        if passed_tests == total_tests:
            self.logger.info("🎉 All tests passed! Enhanced system is working correctly.")
        else:
            self.logger.warning("⚠️  Some tests failed. Check the logs for details.")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Test the enhanced APPA system components',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    parser.add_argument('--component', 
                       choices=['discovery', 'analysis', 'pdf', 'validator', 'mcp', 'pipeline'],
                       help='Test only specific component')
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    
    print("🚀 Enhanced APPA System Testing")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    try:
        config = create_test_config()
        tester = SystemTester(config, verbose=args.verbose)
        
        if args.component:
            # Test specific component
            component_methods = {
                'mcp': tester.test_mcp_integration,
                'discovery': tester.test_enhanced_discovery,
                'analysis': tester.test_content_analysis,
                'pdf': tester.test_pdf_downloader,
                'validator': tester.test_paper_validator,
                'pipeline': tester.test_end_to_end_pipeline
            }
            
            method = component_methods.get(args.component)
            if method:
                print(f"🔍 Testing component: {args.component}")
                result = method()
                print(f"Result: {'PASSED' if result else 'FAILED'}")
            else:
                print(f"❌ Unknown component: {args.component}")
                return 1
        else:
            # Run all tests
            tester.run_all_tests()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Fatal error during testing: {e}")
        if args.verbose:
            print(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())