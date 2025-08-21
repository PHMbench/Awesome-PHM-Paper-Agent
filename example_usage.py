#!/usr/bin/env python3
"""
Example usage of APPA system components.

This script demonstrates how to use individual APPA agents
and the main orchestrator programmatically.
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import load_config
from src.utils.logging_config import setup_logging
from src.models import PaperMetadata, PaperIdentifiers, CitationMetrics, QualityMetrics, VenueType, VenueQuartile
from src.agents.quality_curation_agent import QualityCurationAgent
from src.agents.content_analysis_agent import ContentAnalysisAgent


def create_sample_papers():
    """Create sample paper data for testing."""
    papers = []
    
    # Sample paper 1
    identifiers1 = PaperIdentifiers(
        doi="10.1016/j.ymssp.2023.110123",
        urls={
            'pdf': 'https://example.com/paper1.pdf',
            'publisher': 'https://www.sciencedirect.com/science/article/pii/S0888327023001234',
            'google_scholar': 'https://scholar.google.com/scholar?q=deep+learning+bearing+fault'
        }
    )
    
    paper1 = {
        'title': 'Deep Learning Approaches for Bearing Fault Diagnosis in Rotating Machinery',
        'authors': ['Zhang, Wei', 'Smith, John A.', 'Liu, Ming'],
        'affiliations': ['Tsinghua University', 'MIT', 'Stanford University'],
        'year': 2023,
        'venue': 'Mechanical Systems and Signal Processing',
        'type': VenueType.JOURNAL.value,
        'doi': identifiers1.doi,
        'urls': identifiers1.urls,
        'abstract': 'This paper proposes a novel deep learning framework for bearing fault diagnosis in rotating machinery. The approach combines convolutional neural networks (CNN) with long short-term memory (LSTM) networks to analyze vibration signals and classify different fault types. Experimental validation on a benchmark dataset demonstrates 97.5% accuracy in fault classification, outperforming traditional machine learning methods. The proposed method shows excellent generalization capability across different operating conditions and fault severities.',
        'keywords': ['deep learning', 'bearing fault diagnosis', 'CNN', 'LSTM', 'vibration analysis', 'rotating machinery'],
        'citation_count': 45,
        'source': 'example',
        'relevance_score': 0.92
    }
    papers.append(paper1)
    
    # Sample paper 2
    identifiers2 = PaperIdentifiers(
        doi="10.1109/TIE.2023.3234567",
        urls={
            'pdf': 'https://example.com/paper2.pdf',
            'publisher': 'https://ieeexplore.ieee.org/document/10123456',
            'google_scholar': 'https://scholar.google.com/scholar?q=predictive+maintenance+IoT'
        }
    )
    
    paper2 = {
        'title': 'IoT-Enabled Predictive Maintenance Framework for Industrial Equipment',
        'authors': ['Johnson, Sarah', 'Brown, Michael'],
        'affiliations': ['University of California Berkeley', 'Georgia Tech'],
        'year': 2023,
        'venue': 'IEEE Transactions on Industrial Electronics',
        'type': VenueType.JOURNAL.value,
        'doi': identifiers2.doi,
        'urls': identifiers2.urls,
        'abstract': 'This work presents an Internet of Things (IoT) enabled predictive maintenance framework for industrial equipment monitoring. The system integrates edge computing with cloud-based analytics to provide real-time health assessment and failure prediction. Machine learning algorithms process sensor data to predict remaining useful life (RUL) with 85% accuracy. Field deployment in a manufacturing facility shows 30% reduction in unplanned downtime and 25% decrease in maintenance costs.',
        'keywords': ['IoT', 'predictive maintenance', 'edge computing', 'remaining useful life', 'industrial equipment'],
        'citation_count': 28,
        'source': 'example',
        'relevance_score': 0.88
    }
    papers.append(paper2)
    
    return papers


def test_quality_curation():
    """Test the Quality Curation Agent."""
    print("Testing Quality Curation Agent...")
    
    # Load configuration
    config = load_config()
    setup_logging(config)
    
    # Create agent
    curation_agent = QualityCurationAgent(config)
    
    # Create sample papers
    papers = create_sample_papers()
    
    # Run curation
    curated_papers = curation_agent.run(papers)
    
    print(f"✓ Curated {len(curated_papers)} papers from {len(papers)} input papers")
    
    for paper in curated_papers:
        quality_metrics = paper.get('quality_metrics', {})
        print(f"  - {paper['title'][:50]}...")
        print(f"    Quality Score: {quality_metrics.get('quality_score', 0):.3f}")
        print(f"    Venue Rank: {quality_metrics.get('venue_rank', 'Unknown')}")
        print(f"    Reason: {paper.get('filtering_reason', 'No reason provided')}")
    
    return curated_papers


def test_content_analysis():
    """Test the Content Analysis Agent."""
    print("\nTesting Content Analysis Agent...")
    
    # Load configuration
    config = load_config()
    
    # Create agent
    analysis_agent = ContentAnalysisAgent(config)
    
    # Create sample papers
    papers = create_sample_papers()
    
    # Run analysis
    analyzed_papers = analysis_agent.run(papers)
    
    print(f"✓ Analyzed {len(analyzed_papers)} papers")
    
    for paper in analyzed_papers:
        analysis = paper.get('analysis', {})
        print(f"  - {paper['title'][:50]}...")
        print(f"    TL;DR: {analysis.get('tldr', 'No TL;DR available')}")
        print(f"    Key Points: {len(analysis.get('key_points', []))} points")
        print(f"    Topics: {', '.join(analysis.get('extracted_topics', [])[:3])}")
        print(f"    Reproducibility: {analysis.get('reproducibility_score', 0):.2f}")
    
    return analyzed_papers


def test_paper_metadata():
    """Test PaperMetadata model creation."""
    print("\nTesting PaperMetadata model...")
    
    identifiers = PaperIdentifiers(
        doi="10.1000/test.2023.123456",
        urls={
            'pdf': 'https://example.com/test.pdf',
            'publisher': 'https://example.com/publisher',
            'google_scholar': 'https://scholar.google.com/test'
        }
    )
    
    citations = CitationMetrics(count=15)
    quality = QualityMetrics(
        venue_rank=VenueQuartile.Q1,
        filtering_reason="High-impact venue with excellent reputation"
    )
    
    paper = PaperMetadata(
        title="Test Paper for APPA System Validation",
        authors=["Doe, Jane", "Smith, John", "Wilson, Alice"],
        affiliations=["Test University", "Research Institute"],
        year=2023,
        venue="Test Journal of Advanced Research",
        type=VenueType.JOURNAL,
        identifiers=identifiers,
        citations=citations,
        keywords=["test", "validation", "system", "research", "methodology"],
        abstract="This is a comprehensive test paper designed to validate the APPA system functionality. The paper demonstrates various aspects of academic paper processing including metadata extraction, content analysis, and quality assessment.",
        quality_metrics=quality
    )
    
    print(f"✓ Created paper metadata successfully")
    print(f"  Title: {paper.title}")
    print(f"  Authors: {len(paper.authors)} authors")
    print(f"  First author: {paper.get_first_author_lastname()}")
    print(f"  Short title: {paper.get_short_title()}")
    print(f"  Year: {paper.year}")
    print(f"  Venue: {paper.venue}")
    print(f"  Keywords: {len(paper.keywords)} keywords")
    
    # Test BibTeX generation
    bibtex = paper.to_bibtex()
    print(f"✓ Generated BibTeX citation ({len(bibtex)} characters)")
    
    return paper


def main():
    """Run all example tests."""
    print("APPA System Example Usage")
    print("=" * 50)
    
    try:
        # Test 1: Paper metadata model
        test_paper_metadata()
        
        # Test 2: Quality curation
        curated_papers = test_quality_curation()
        
        # Test 3: Content analysis
        if curated_papers:
            analyzed_papers = test_content_analysis()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        print("APPA system is ready for use.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
