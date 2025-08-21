"""
Data models for APPA system.

This module defines the data structures used throughout the system for
representing papers, metadata, and analysis results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class VenueType(Enum):
    """Enumeration for venue types."""
    JOURNAL = "journal"
    CONFERENCE = "conference"
    PREPRINT = "preprint"


class VenueQuartile(Enum):
    """Enumeration for venue quartiles."""
    Q1 = "Q1"
    Q2 = "Q2"
    Q3 = "Q3"
    Q4 = "Q4"


@dataclass
class PaperIdentifiers:
    """Container for paper identifiers and URLs."""
    doi: Optional[str] = None
    arxiv: Optional[str] = None
    urls: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure required URL fields exist."""
        required_urls = ['pdf', 'publisher', 'google_scholar']
        for url_type in required_urls:
            if url_type not in self.urls:
                self.urls[url_type] = ""


@dataclass
class CitationMetrics:
    """Container for citation-related metrics."""
    count: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def update_count(self, new_count: int) -> None:
        """Update citation count and timestamp."""
        self.count = new_count
        self.last_updated = datetime.now().strftime("%Y-%m-%d")


@dataclass
class QualityMetrics:
    """Container for paper quality assessment metrics."""
    venue_rank: Optional[VenueQuartile] = None
    h5_index: Optional[int] = None
    filtering_reason: str = ""
    relevance_score: float = 0.0
    
    def is_high_quality(self) -> bool:
        """Check if paper meets high quality criteria."""
        return (self.venue_rank in [VenueQuartile.Q1, VenueQuartile.Q2] and
                self.relevance_score >= 0.7)


@dataclass
class PaperMetadata:
    """Complete metadata for a research paper."""
    title: str
    authors: List[str]
    affiliations: List[str]
    year: int
    venue: str
    type: VenueType
    identifiers: PaperIdentifiers
    citations: CitationMetrics
    keywords: List[str]
    abstract: str
    quality_metrics: QualityMetrics
    
    # Additional fields for internal processing
    discovered_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    last_updated: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    def __post_init__(self):
        """Validate and normalize metadata after initialization."""
        # Ensure minimum required fields
        if not self.title:
            raise ValueError("Paper title is required")
        if not self.authors:
            raise ValueError("At least one author is required")
        if not self.abstract:
            raise ValueError("Paper abstract is required")
        if len(self.keywords) < 3:
            raise ValueError("At least 3 keywords are required")
        
        # Normalize data
        self.title = self.title.strip()
        self.authors = [author.strip() for author in self.authors]
        self.affiliations = [aff.strip() for aff in self.affiliations]
        self.keywords = [kw.strip().lower() for kw in self.keywords]
        
        # Validate year
        current_year = datetime.now().year
        if self.year < 1900 or self.year > current_year:
            raise ValueError(f"Invalid publication year: {self.year}")
    
    def get_first_author_lastname(self) -> str:
        """Extract last name of first author."""
        if not self.authors:
            return "Unknown"
        
        first_author = self.authors[0]
        # Handle "LastName, FirstName" format
        if ',' in first_author:
            return first_author.split(',')[0].strip()
        # Handle "FirstName LastName" format
        else:
            parts = first_author.split()
            return parts[-1] if parts else "Unknown"
    
    def get_short_title(self, max_length: int = 50) -> str:
        """Generate shortened title for folder naming."""
        # Remove common words and clean title
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = self.title.lower().split()
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        short_title = ' '.join(filtered_words[:6])  # Take first 6 meaningful words
        if len(short_title) > max_length:
            short_title = short_title[:max_length-3] + "..."
        
        return short_title
    
    def to_bibtex(self) -> str:
        """Generate BibTeX citation for the paper."""
        # Generate citation key
        first_author = self.get_first_author_lastname()
        key = f"{first_author}{self.year}"
        
        # Determine entry type
        entry_type = "article" if self.type == VenueType.JOURNAL else "inproceedings"
        
        # Build BibTeX entry
        bibtex_lines = [f"@{entry_type}{{{key},"]
        bibtex_lines.append(f"  title = {{{self.title}}},")
        bibtex_lines.append(f"  author = {{{' and '.join(self.authors)}}},")
        bibtex_lines.append(f"  year = {{{self.year}}},")
        
        if self.type == VenueType.JOURNAL:
            bibtex_lines.append(f"  journal = {{{self.venue}}},")
        else:
            bibtex_lines.append(f"  booktitle = {{{self.venue}}},")
        
        if self.identifiers.doi:
            bibtex_lines.append(f"  doi = {{{self.identifiers.doi}}},")
        
        if self.identifiers.urls.get('pdf'):
            bibtex_lines.append(f"  url = {{{self.identifiers.urls['pdf']}}},")
        
        bibtex_lines.append("}")
        
        return '\n'.join(bibtex_lines)


@dataclass
class AnalysisResult:
    """Container for paper analysis results."""
    tldr: str  # ≤50 words
    key_points: List[str]  # 4-6 bullets
    deep_analysis: str  # 500-800 words
    extracted_topics: List[str]
    reproducibility_score: float = 0.0
    
    def __post_init__(self):
        """Validate analysis content."""
        # Validate TL;DR length
        tldr_words = len(self.tldr.split())
        if tldr_words > 50:
            raise ValueError(f"TL;DR too long: {tldr_words} words (max 50)")
        
        # Validate key points count
        if len(self.key_points) < 4 or len(self.key_points) > 6:
            raise ValueError(f"Key points must be 4-6 items, got {len(self.key_points)}")
        
        # Validate deep analysis length
        analysis_words = len(self.deep_analysis.split())
        if analysis_words < 500 or analysis_words > 800:
            raise ValueError(f"Deep analysis must be 500-800 words, got {analysis_words}")


@dataclass
class ProcessingResult:
    """Result of processing a batch of papers."""
    processed_papers: List[PaperMetadata]
    failed_papers: List[Dict[str, Any]]
    processing_stats: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


if __name__ == "__main__":
    # Test data models
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
    
    print("Paper metadata created successfully")
    print(f"First author: {paper.get_first_author_lastname()}")
    print(f"Short title: {paper.get_short_title()}")
    print("\nBibTeX:")
    print(paper.to_bibtex())
