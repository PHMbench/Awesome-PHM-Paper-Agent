"""
Basic functionality tests for APPA system.

These tests verify that the core components can be imported and initialized.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.config import load_config, validate_config, ConfigError
from src.models import PaperMetadata, PaperIdentifiers, CitationMetrics, QualityMetrics, VenueType, VenueQuartile


class TestConfiguration(unittest.TestCase):
    """Test configuration management."""
    
    def test_config_loading(self):
        """Test that configuration can be loaded."""
        # Test with default config file
        if os.path.exists('config.yaml'):
            config = load_config('config.yaml')
            self.assertIsInstance(config, dict)
            self.assertIn('search_parameters', config)
            self.assertIn('quality_filters', config)
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        valid_config = {
            'search_parameters': {
                'keywords': ['test'],
                'time_range': '2020-2024',
                'max_results_per_source': 10
            },
            'quality_filters': {
                'venue_whitelist': ['Test Journal'],
                'min_citations': 5
            },
            'output_preferences': {
                'summary_length': 'medium'
            },
            'api_configuration': {
                'rate_limits': {'openalex': 10}
            }
        }
        
        # Should not raise exception
        validate_config(valid_config)
        
        # Invalid config - missing required section
        invalid_config = {
            'search_parameters': {
                'keywords': ['test']
            }
        }
        
        with self.assertRaises(ConfigError):
            validate_config(invalid_config)


class TestDataModels(unittest.TestCase):
    """Test data models."""
    
    def test_paper_metadata_creation(self):
        """Test PaperMetadata creation and validation."""
        identifiers = PaperIdentifiers(
            doi="10.1000/test",
            urls={
                'pdf': 'https://example.com/paper.pdf',
                'publisher': 'https://example.com/paper',
                'google_scholar': 'https://scholar.google.com/paper'
            }
        )
        
        citations = CitationMetrics(count=42)
        quality = QualityMetrics(venue_rank=VenueQuartile.Q1, filtering_reason="High-impact venue")
        
        paper = PaperMetadata(
            title="Test Paper on PHM",
            authors=["Smith, John", "Doe, Jane"],
            affiliations=["University A", "University B"],
            year=2023,
            venue="Test Journal",
            type=VenueType.JOURNAL,
            identifiers=identifiers,
            citations=citations,
            keywords=["prognostics", "health management", "fault diagnosis"],
            abstract="This is a test abstract for the paper.",
            quality_metrics=quality
        )
        
        self.assertEqual(paper.title, "Test Paper on PHM")
        self.assertEqual(len(paper.authors), 2)
        self.assertEqual(len(paper.keywords), 3)
        self.assertEqual(paper.get_first_author_lastname(), "Smith")
    
    def test_paper_metadata_validation(self):
        """Test PaperMetadata validation."""
        identifiers = PaperIdentifiers()
        citations = CitationMetrics()
        quality = QualityMetrics()
        
        # Missing title should raise error
        with self.assertRaises(ValueError):
            PaperMetadata(
                title="",
                authors=["Smith, John"],
                affiliations=["University A"],
                year=2023,
                venue="Test Journal",
                type=VenueType.JOURNAL,
                identifiers=identifiers,
                citations=citations,
                keywords=["test", "keywords", "here"],
                abstract="Test abstract",
                quality_metrics=quality
            )
        
        # Insufficient keywords should raise error
        with self.assertRaises(ValueError):
            PaperMetadata(
                title="Test Paper",
                authors=["Smith, John"],
                affiliations=["University A"],
                year=2023,
                venue="Test Journal",
                type=VenueType.JOURNAL,
                identifiers=identifiers,
                citations=citations,
                keywords=["test"],  # Only 1 keyword, need at least 3
                abstract="Test abstract",
                quality_metrics=quality
            )
    
    def test_bibtex_generation(self):
        """Test BibTeX generation."""
        identifiers = PaperIdentifiers(
            doi="10.1000/test",
            urls={'pdf': 'https://example.com/paper.pdf'}
        )
        
        paper = PaperMetadata(
            title="Test Paper on PHM",
            authors=["Smith, John", "Doe, Jane"],
            affiliations=["University A"],
            year=2023,
            venue="Test Journal",
            type=VenueType.JOURNAL,
            identifiers=identifiers,
            citations=CitationMetrics(),
            keywords=["test", "keywords", "here"],
            abstract="Test abstract",
            quality_metrics=QualityMetrics()
        )
        
        bibtex = paper.to_bibtex()
        self.assertIn("@article{Smith2023,", bibtex)
        self.assertIn("title = {Test Paper on PHM}", bibtex)
        self.assertIn("author = {Smith, John and Doe, Jane}", bibtex)
        self.assertIn("year = {2023}", bibtex)
        self.assertIn("doi = {10.1000/test}", bibtex)


class TestAgentImports(unittest.TestCase):
    """Test that agents can be imported and initialized."""
    
    def test_agent_imports(self):
        """Test that available agents can be imported."""
        try:
            from src.agents.quality_curation_agent import QualityCurationAgent
            from src.agents.content_analysis_agent import ContentAnalysisAgent
            
            # Test that classes exist and have process method
            self.assertTrue(hasattr(QualityCurationAgent, 'process'))
            self.assertTrue(hasattr(ContentAnalysisAgent, 'process'))
            
        except ImportError as e:
            self.fail(f"Failed to import available agents: {e}")
    
    @patch('src.utils.logging_config.setup_logging')
    def test_agent_initialization(self, mock_setup_logging):
        """Test that agents can be initialized with config."""
        from src.agents.quality_curation_agent import QualityCurationAgent
        
        test_config = {
            'quality_filters': {
                'venue_whitelist': ['Test Journal'],
                'min_citations': 5,
                'venue_quartile': ['Q1', 'Q2'],
                'min_h5_index': 20,
                'min_publication_year': 2015
            }
        }
        
        # Should not raise exception
        agent = QualityCurationAgent(test_config)
        self.assertEqual(agent.name, "QualityCurationAgent")
        self.assertIsNotNone(agent.config)


class TestMainStatusManager(unittest.TestCase):
    """Test main status manager functionality."""
    
    @patch('src.utils.config.load_config')
    @patch('src.utils.logging_config.setup_logging')
    def test_status_manager_import(self, mock_setup_logging, mock_load_config):
        """Test that status manager can be imported and initialized."""
        mock_load_config.return_value = {
            'search_parameters': {'keywords': ['test']},
            'quality_filters': {'venue_whitelist': []},
            'output_preferences': {'summary_length': 'medium'},
            'api_configuration': {'rate_limits': {}}
        }
        
        try:
            import main
            status_manager = main.APPAStatusManager()
            self.assertIsNotNone(status_manager.config)
            
            # Test status functionality
            status = status_manager.get_system_status()
            self.assertIn('system_type', status)
            self.assertEqual(status['system_type'], 'Claude Code Agent Based')
            
        except Exception as e:
            self.fail(f"Failed to initialize status manager: {e}")


if __name__ == '__main__':
    # Create test configuration if it doesn't exist
    if not os.path.exists('config.yaml'):
        print("Warning: config.yaml not found, some tests may be skipped")
    
    unittest.main()
