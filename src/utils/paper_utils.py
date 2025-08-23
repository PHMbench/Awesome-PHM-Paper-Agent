"""
Paper Utilities - Shared utility functions for paper processing.

This module consolidates common utility functions that were previously duplicated
across multiple files in the enhanced APPA system.

Created during redundancy removal refactoring - 2025-08-23
"""

import hashlib
import re
import requests
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging

from .phm_constants import (
    PHM_CONCEPTS, METHODOLOGY_KEYWORDS, APPLICATION_DOMAINS,
    VENUE_QUALITY_MAPPING, RELEVANCE_THRESHOLDS, CITATION_IMPACT_CATEGORIES,
    TIME_DECAY_FACTORS
)

logger = logging.getLogger(__name__)


def create_paper_fingerprint(paper: Dict[str, Any], method: str = 'advanced') -> str:
    """
    Create a unique fingerprint for paper deduplication.
    
    Args:
        paper: Paper metadata dictionary
        method: 'advanced' (detailed) or 'legacy' (simple) fingerprinting
        
    Returns:
        Unique fingerprint string
    """
    if method == 'legacy':
        return _create_legacy_fingerprint(paper)
    else:
        return _create_advanced_fingerprint(paper)


def _create_legacy_fingerprint(paper: Dict[str, Any]) -> str:
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


def _create_advanced_fingerprint(paper: Dict[str, Any]) -> str:
    """Create advanced fingerprint with multiple components."""
    components = []
    
    # Title component (normalized)
    title = paper.get('title', '').lower()
    title = re.sub(r'[^\w\s]', '', title)  # Remove punctuation
    title = ' '.join(title.split())  # Normalize whitespace
    components.append(title[:100])  # First 100 chars
    
    # First author last name
    authors = paper.get('authors', [])
    if authors:
        first_author = str(authors[0]).lower()
        # Extract last name (handle various formats)
        if ',' in first_author:
            last_name = first_author.split(',')[0].strip()
        else:
            parts = first_author.split()
            last_name = parts[-1] if parts else first_author
        components.append(last_name[:20])
    else:
        components.append('')
    
    # Year
    components.append(str(paper.get('year', 0)))
    
    # Venue (normalized)
    venue = paper.get('venue', '').lower()
    venue = re.sub(r'[^\w\s]', '', venue)
    components.append(venue[:30])
    
    # Create fingerprint
    fingerprint_text = '|'.join(components)
    return hashlib.sha256(fingerprint_text.encode('utf-8')).hexdigest()[:16]


def calculate_phm_relevance_score(paper: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate PHM relevance score based on multiple factors.
    
    Args:
        paper: Paper metadata dictionary
        
    Returns:
        Tuple of (overall_score, detailed_scores)
    """
    detailed_scores = {
        'concept_scores': {},
        'title_score': 0.0,
        'abstract_score': 0.0,
        'keyword_score': 0.0,
        'venue_score': 0.0,
        'overall_score': 0.0
    }
    
    # Get text content
    title = paper.get('title', '').lower()
    abstract = paper.get('abstract', '').lower()
    keywords = [k.lower() for k in paper.get('keywords', [])]
    venue = paper.get('venue', '').lower()
    
    # Combine text for analysis
    combined_text = f"{title} {abstract} {' '.join(keywords)}"
    
    # Calculate concept scores
    total_concept_score = 0.0
    for concept, config in PHM_CONCEPTS.items():
        concept_keywords = config['keywords']
        weight = config['weight']
        
        # Count matches in different fields
        title_matches = sum(1 for kw in concept_keywords if kw in title)
        abstract_matches = sum(1 for kw in concept_keywords if kw in abstract)
        keyword_matches = sum(1 for kw in concept_keywords if any(kw in k for k in keywords))
        
        # Calculate normalized scores
        title_norm = min(title_matches / len(title.split()) * 10, 1.0) if title else 0
        abstract_norm = min(abstract_matches / len(abstract.split()) * 100, 1.0) if abstract else 0
        keyword_norm = min(keyword_matches / max(len(keywords), 1), 1.0)
        
        # Weighted concept score
        concept_score = (title_norm * 0.4 + abstract_norm * 0.4 + keyword_norm * 0.2) * weight
        detailed_scores['concept_scores'][concept] = concept_score
        total_concept_score += concept_score
    
    # Individual field scores
    detailed_scores['title_score'] = _calculate_field_score(title, 'title')
    detailed_scores['abstract_score'] = _calculate_field_score(abstract, 'abstract')
    detailed_scores['keyword_score'] = _calculate_field_score(' '.join(keywords), 'keywords')
    detailed_scores['venue_score'] = _calculate_venue_relevance(venue)
    
    # Overall score calculation
    overall_score = (
        total_concept_score * 0.5 +
        detailed_scores['title_score'] * 0.2 +
        detailed_scores['abstract_score'] * 0.15 +
        detailed_scores['keyword_score'] * 0.1 +
        detailed_scores['venue_score'] * 0.05
    )
    
    detailed_scores['overall_score'] = min(overall_score, 1.0)
    
    return detailed_scores['overall_score'], detailed_scores


def _calculate_field_score(text: str, field_type: str) -> float:
    """Calculate relevance score for a specific text field."""
    if not text:
        return 0.0
    
    words = text.split()
    if not words:
        return 0.0
    
    # Count PHM-related terms
    phm_count = 0
    all_phm_keywords = []
    for concept_config in PHM_CONCEPTS.values():
        all_phm_keywords.extend(concept_config['keywords'])
    
    for keyword in all_phm_keywords:
        if keyword in text:
            phm_count += 1
    
    # Normalize based on field type
    if field_type == 'title':
        return min(phm_count / len(words) * 5, 1.0)
    elif field_type == 'abstract':
        return min(phm_count / len(words) * 20, 1.0)
    elif field_type == 'keywords':
        return min(phm_count / max(len(words), 1), 1.0)
    else:
        return min(phm_count / len(words) * 10, 1.0)


def _calculate_venue_relevance(venue: str) -> float:
    """Calculate venue-based relevance score."""
    if not venue:
        return 0.0
    
    venue_lower = venue.lower().strip()
    
    # Check exact matches first
    if venue_lower in VENUE_QUALITY_MAPPING:
        venue_info = VENUE_QUALITY_MAPPING[venue_lower]
        if 'impact_factor' in venue_info:
            return min(venue_info['impact_factor'] / 10.0, 1.0)
        elif 'score' in venue_info:
            return venue_info['score']
    
    # Check partial matches
    phm_venue_keywords = [
        'prognostics', 'health management', 'reliability', 'maintenance',
        'condition monitoring', 'fault diagnosis', 'mechanical systems',
        'signal processing', 'industrial electronics', 'measurement'
    ]
    
    matches = sum(1 for keyword in phm_venue_keywords if keyword in venue_lower)
    return min(matches * 0.15, 0.6)  # Max 0.6 for partial matches


def classify_methodology(paper: Dict[str, Any]) -> List[str]:
    """
    Classify paper methodology based on content analysis.
    
    Args:
        paper: Paper metadata dictionary
        
    Returns:
        List of methodology classifications
    """
    title = paper.get('title', '').lower()
    abstract = paper.get('abstract', '').lower()
    keywords = [k.lower() for k in paper.get('keywords', [])]
    
    combined_text = f"{title} {abstract} {' '.join(keywords)}"
    
    classifications = []
    for method_id, method_config in METHODOLOGY_KEYWORDS.items():
        method_keywords = method_config['keywords']
        matches = sum(1 for keyword in method_keywords if keyword in combined_text)
        
        if matches >= 2:  # Require at least 2 keyword matches
            classifications.append(method_config['category'])
        elif matches == 1 and any(keyword in title for keyword in method_keywords):
            # Single match in title is also significant
            classifications.append(method_config['category'])
    
    return list(set(classifications))  # Remove duplicates


def identify_application_domains(paper: Dict[str, Any]) -> List[str]:
    """
    Identify application domains mentioned in the paper.
    
    Args:
        paper: Paper metadata dictionary
        
    Returns:
        List of identified application domains
    """
    title = paper.get('title', '').lower()
    abstract = paper.get('abstract', '').lower()
    keywords = [k.lower() for k in paper.get('keywords', [])]
    
    combined_text = f"{title} {abstract} {' '.join(keywords)}"
    
    domains = []
    for domain_id, domain_config in APPLICATION_DOMAINS.items():
        domain_keywords = domain_config['keywords']
        matches = sum(1 for keyword in domain_keywords if keyword in combined_text)
        
        if matches >= 1:  # Single match is sufficient for domain identification
            domains.append(domain_config['domain'])
    
    return list(set(domains))  # Remove duplicates


def assess_venue_quality(venue: str) -> Dict[str, Any]:
    """
    Assess the quality of a publication venue.
    
    Args:
        venue: Venue name
        
    Returns:
        Dictionary with quality assessment information
    """
    if not venue:
        return {
            'quality_tier': 'unknown',
            'impact_factor': None,
            'quartile': None,
            'category': 'unknown',
            'score': 0.0
        }
    
    venue_lower = venue.lower().strip()
    
    # Check exact match
    if venue_lower in VENUE_QUALITY_MAPPING:
        venue_info = VENUE_QUALITY_MAPPING[venue_lower].copy()
        
        # Determine quality tier
        if venue_info.get('quartile') == 'Q1' or venue_info.get('score', 0) >= 0.8:
            venue_info['quality_tier'] = 'top_tier'
        elif venue_info.get('quartile') == 'Q2' or venue_info.get('score', 0) >= 0.6:
            venue_info['quality_tier'] = 'high_quality'
        elif venue_info.get('quartile') in ['Q3', 'Q4'] or venue_info.get('score', 0) >= 0.4:
            venue_info['quality_tier'] = 'standard'
        else:
            venue_info['quality_tier'] = 'emerging'
        
        # Add score if missing
        if 'score' not in venue_info:
            if 'impact_factor' in venue_info:
                venue_info['score'] = min(venue_info['impact_factor'] / 10.0, 1.0)
            else:
                venue_info['score'] = 0.5
        
        return venue_info
    
    # Partial matching for unknown venues
    return {
        'quality_tier': 'unknown',
        'impact_factor': None,
        'quartile': None,
        'category': 'unknown',
        'score': 0.3  # Default score for unknown venues
    }


def calculate_time_relevance_factor(year: int) -> float:
    """
    Calculate time-based relevance factor.
    
    Args:
        year: Publication year
        
    Returns:
        Time relevance factor (0.0 to 1.0)
    """
    current_year = datetime.now().year
    age = current_year - year
    
    if age <= 0:
        return TIME_DECAY_FACTORS['current_year']
    elif age == 1:
        return TIME_DECAY_FACTORS['last_year']
    elif age == 2:
        return TIME_DECAY_FACTORS['two_years']
    elif age == 3:
        return TIME_DECAY_FACTORS['three_years']
    else:
        return TIME_DECAY_FACTORS['older']


def categorize_citation_impact(citation_count: int) -> str:
    """
    Categorize citation impact based on citation count.
    
    Args:
        citation_count: Number of citations
        
    Returns:
        Impact category string
    """
    if citation_count >= CITATION_IMPACT_CATEGORIES['high_impact']:
        return 'high_impact'
    elif citation_count >= CITATION_IMPACT_CATEGORIES['medium_impact']:
        return 'medium_impact'
    elif citation_count >= CITATION_IMPACT_CATEGORIES['emerging']:
        return 'emerging'
    else:
        return 'new'


def validate_doi(doi: str) -> bool:
    """
    Validate DOI format.
    
    Args:
        doi: DOI string
        
    Returns:
        True if valid DOI format
    """
    if not doi:
        return False
    
    # Basic DOI pattern validation
    doi_pattern = re.compile(r'^10\.\d{4,}/[^\s]+$')
    return bool(doi_pattern.match(doi))


def normalize_author_name(author: str) -> str:
    """
    Normalize author name for consistency.
    
    Args:
        author: Raw author name
        
    Returns:
        Normalized author name
    """
    if not author:
        return ""
    
    # Remove extra whitespace
    normalized = ' '.join(author.split())
    
    # Handle common patterns
    if ',' in normalized:
        # "Last, First" format
        parts = normalized.split(',', 1)
        if len(parts) == 2:
            last_name = parts[0].strip()
            first_name = parts[1].strip()
            normalized = f"{first_name} {last_name}"
    
    return normalized


def extract_keywords_from_text(text: str, max_keywords: int = 10) -> List[str]:
    """
    Extract potential keywords from text content.
    
    Args:
        text: Input text
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
    
    # Simple keyword extraction based on PHM terminology
    text_lower = text.lower()
    found_keywords = []
    
    # Check for PHM concepts
    for concept_config in PHM_CONCEPTS.values():
        for keyword in concept_config['keywords']:
            if keyword in text_lower and keyword not in found_keywords:
                found_keywords.append(keyword)
    
    # Check for methodology keywords
    for method_config in METHODOLOGY_KEYWORDS.values():
        for keyword in method_config['keywords']:
            if keyword in text_lower and keyword not in found_keywords:
                found_keywords.append(keyword)
    
    return found_keywords[:max_keywords]


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unknown_file"
    
    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)  # Replace spaces with underscores
    sanitized = sanitized[:200]  # Limit length
    
    return sanitized or "unknown_file"


def is_preprint_venue(venue: str) -> bool:
    """
    Check if venue is a preprint server.
    
    Args:
        venue: Venue name
        
    Returns:
        True if venue is a preprint server
    """
    if not venue:
        return False
    
    venue_lower = venue.lower()
    preprint_indicators = [
        'arxiv', 'biorxiv', 'medrxiv', 'preprint', 'ssrn',
        'research square', 'techrxiv', 'chemrxiv'
    ]
    
    return any(indicator in venue_lower for indicator in preprint_indicators)


def merge_paper_metadata(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge duplicate papers based on fingerprints.
    
    Args:
        papers: List of paper metadata dictionaries
        
    Returns:
        List of merged papers with duplicates removed
    """
    seen_fingerprints = set()
    merged_papers = []
    
    for paper in papers:
        fingerprint = create_paper_fingerprint(paper)
        
        if fingerprint not in seen_fingerprints:
            seen_fingerprints.add(fingerprint)
            merged_papers.append(paper)
        else:
            # Find existing paper and merge information
            for existing_paper in merged_papers:
                if create_paper_fingerprint(existing_paper) == fingerprint:
                    # Merge additional information if available
                    if not existing_paper.get('doi') and paper.get('doi'):
                        existing_paper['doi'] = paper['doi']
                    if not existing_paper.get('abstract') and paper.get('abstract'):
                        existing_paper['abstract'] = paper['abstract']
                    if paper.get('citation_count', 0) > existing_paper.get('citation_count', 0):
                        existing_paper['citation_count'] = paper['citation_count']
                    break
    
    return merged_papers