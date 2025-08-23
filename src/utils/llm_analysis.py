"""
LLM Analysis Utilities - Shared LLM-based analysis functions.

This module consolidates LLM-based analysis functions that were previously
duplicated across multiple agent files.

Created during redundancy removal refactoring - 2025-08-23
"""

import re
from typing import List, Dict, Any, Optional
import logging

from .llm_client import LLMManager

logger = logging.getLogger(__name__)


def generate_tldr_summary(paper: Dict[str, Any], llm_manager: LLMManager, 
                         language: str = 'chinese', max_words: int = 50) -> Optional[str]:
    """
    Generate TL;DR summary using LLM.
    
    Args:
        paper: Paper metadata dictionary
        llm_manager: LLM manager instance
        language: 'chinese' or 'english'
        max_words: Maximum words in summary
        
    Returns:
        TL;DR summary string or None if generation fails
    """
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')
    
    if not title or not abstract:
        logger.debug("Cannot generate TL;DR: missing title or abstract")
        return None
        
    if not llm_manager.get_feature_enabled('paper_enhancement'):
        logger.debug("LLM paper enhancement disabled")
        return None

    if language.lower() == 'chinese':
        prompt = f"""
        Generate a concise TL;DR summary (maximum {max_words} words) for this PHM research paper:
        
        Title: {title}
        
        Abstract: {abstract}
        
        Focus on: main contribution, method used, and key result/improvement.
        Write in Chinese for better readability.
        """
    else:
        prompt = f"""
        Generate a concise TL;DR summary (maximum {max_words} words) for this PHM research paper:
        
        Title: {title}
        
        Abstract: {abstract}
        
        Focus on: main contribution, method used, and key result/improvement.
        """

    try:
        response = llm_manager.generate_text(prompt, max_tokens=150, temperature=0.3)
        if response and len(response.strip()) > 10:
            return response.strip()
    except Exception as e:
        logger.warning(f"TL;DR generation failed: {e}")

    return None


def extract_key_contributions(paper: Dict[str, Any], llm_manager: LLMManager, 
                             max_contributions: int = 5) -> Optional[List[str]]:
    """
    Extract key contributions using LLM.
    
    Args:
        paper: Paper metadata dictionary
        llm_manager: LLM manager instance
        max_contributions: Maximum number of contributions to extract
        
    Returns:
        List of key contributions or None if extraction fails
    """
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')
    
    if not abstract:
        logger.debug("Cannot extract contributions: missing abstract")
        return None
        
    if not llm_manager.get_feature_enabled('paper_enhancement'):
        logger.debug("LLM paper enhancement disabled")
        return None

    prompt = f"""
    Extract {max_contributions} key contributions from this PHM research paper:
    
    Title: {title}
    Abstract: {abstract}
    
    List only the main technical/methodological contributions, one per line.
    Be specific and focus on novel aspects.
    """

    try:
        response = llm_manager.generate_text(prompt, max_tokens=250, temperature=0.3)
        if response:
            contributions = []
            lines = response.strip().split('\n')
            for line in lines:
                # Clean up list markers
                line = re.sub(r'^[-*•\d\.)\s]+', '', line).strip()
                if line and len(line) > 10:
                    contributions.append(line)
            return contributions[:max_contributions]
    except Exception as e:
        logger.warning(f"Contribution extraction failed: {e}")

    return None


def generate_research_summary(paper: Dict[str, Any], llm_manager: LLMManager) -> Dict[str, str]:
    """
    Generate comprehensive research summary with multiple components.
    
    Args:
        paper: Paper metadata dictionary
        llm_manager: LLM manager instance
        
    Returns:
        Dictionary with summary components
    """
    summary = {
        'tldr_chinese': None,
        'tldr_english': None,
        'key_contributions': None,
        'methodology_summary': None,
        'impact_assessment': None
    }
    
    if not llm_manager.get_feature_enabled('paper_enhancement'):
        logger.debug("LLM paper enhancement disabled")
        return summary

    # Generate TL;DR summaries
    summary['tldr_chinese'] = generate_tldr_summary(paper, llm_manager, 'chinese')
    summary['tldr_english'] = generate_tldr_summary(paper, llm_manager, 'english')
    
    # Extract contributions
    contributions = extract_key_contributions(paper, llm_manager)
    if contributions:
        summary['key_contributions'] = contributions

    return summary


def assess_methodology_novelty(paper: Dict[str, Any], llm_manager: LLMManager) -> Optional[Dict[str, Any]]:
    """
    Assess the novelty and innovation level of the methodology.
    
    Args:
        paper: Paper metadata dictionary
        llm_manager: LLM manager instance
        
    Returns:
        Dictionary with novelty assessment
    """
    if not llm_manager.get_feature_enabled('paper_enhancement'):
        return None
        
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')
    
    if not abstract:
        return None

    prompt = f"""
    Assess the methodological novelty of this PHM research paper:
    
    Title: {title}
    Abstract: {abstract}
    
    Provide:
    1. Novelty level (High/Medium/Low/Incremental)
    2. Innovation type (Methodological/Application/Theoretical/Experimental)
    3. Key innovative aspects (1-2 sentences)
    4. Comparison with existing approaches (if mentioned)
    
    Format as JSON-like structure.
    """

    try:
        response = llm_manager.generate_text(prompt, max_tokens=200, temperature=0.3)
        if response:
            # Simple parsing - could be enhanced with actual JSON parsing
            novelty_assessment = {
                'raw_response': response.strip(),
                'generated_at': 'llm_analysis'
            }
            
            # Extract novelty level if mentioned
            if 'high' in response.lower():
                novelty_assessment['novelty_level'] = 'High'
            elif 'medium' in response.lower():
                novelty_assessment['novelty_level'] = 'Medium'
            elif 'low' in response.lower():
                novelty_assessment['novelty_level'] = 'Low'
            elif 'incremental' in response.lower():
                novelty_assessment['novelty_level'] = 'Incremental'
            
            return novelty_assessment
            
    except Exception as e:
        logger.warning(f"Methodology novelty assessment failed: {e}")

    return None


def extract_technical_keywords(paper: Dict[str, Any], llm_manager: LLMManager, 
                              max_keywords: int = 10) -> Optional[List[str]]:
    """
    Extract technical keywords using LLM analysis.
    
    Args:
        paper: Paper metadata dictionary
        llm_manager: LLM manager instance
        max_keywords: Maximum keywords to extract
        
    Returns:
        List of technical keywords
    """
    if not llm_manager.get_feature_enabled('paper_enhancement'):
        return None
        
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')
    existing_keywords = paper.get('keywords', [])
    
    if not abstract:
        return existing_keywords[:max_keywords] if existing_keywords else None

    prompt = f"""
    Extract {max_keywords} technical keywords from this PHM research paper:
    
    Title: {title}
    Abstract: {abstract}
    Existing keywords: {', '.join(existing_keywords) if existing_keywords else 'None'}
    
    Focus on:
    - Technical methods and algorithms
    - Application domains
    - Key concepts and terminology
    - Equipment types
    
    Return as comma-separated list.
    """

    try:
        response = llm_manager.generate_text(prompt, max_tokens=150, temperature=0.3)
        if response:
            # Parse comma-separated keywords
            keywords = [kw.strip() for kw in response.split(',')]
            keywords = [kw for kw in keywords if kw and len(kw) > 2]
            
            # Combine with existing keywords and deduplicate
            all_keywords = list(existing_keywords) + keywords
            unique_keywords = []
            seen = set()
            
            for kw in all_keywords:
                kw_lower = kw.lower()
                if kw_lower not in seen and len(kw) > 2:
                    unique_keywords.append(kw)
                    seen.add(kw_lower)
            
            return unique_keywords[:max_keywords]
            
    except Exception as e:
        logger.warning(f"Technical keyword extraction failed: {e}")

    return existing_keywords[:max_keywords] if existing_keywords else None