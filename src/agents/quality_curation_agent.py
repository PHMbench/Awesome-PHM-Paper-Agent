"""
Quality Curation Agent for APPA system.

This agent filters papers based on quality metrics and venue reputation.

Single Responsibility: Filter papers based on quality metrics and venue reputation
Input: Raw paper metadata list (JSON)
Output: Curated paper list with quality scores and filtering justifications
"""

from typing import List, Dict, Any, Set, Optional
import re
from datetime import datetime

from .base_agent import BaseAgent, AgentError
from ..models import VenueQuartile, VenueType
from ..utils.llm_client import LLMManager


class QualityCurationAgent(BaseAgent):
    """
    Agent responsible for filtering papers based on quality criteria.
    
    Applies venue whitelist filtering, metric thresholds, and citation impact scoring.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "QualityCurationAgent")
        
        # Quality filter configuration
        self.quality_config = self.get_config_value('quality_filters', {})
        self.venue_whitelist = set(self.quality_config.get('venue_whitelist', []))
        self.min_citations = self.quality_config.get('min_citations', 5)
        self.venue_quartiles = set(self.quality_config.get('venue_quartile', ['Q1', 'Q2']))
        self.min_h5_index = self.quality_config.get('min_h5_index', 20)
        self.min_pub_year = self.quality_config.get('min_publication_year', 2015)
        
        # Load venue rankings database
        self.venue_rankings = self._load_venue_rankings()

        # Initialize LLM manager for smart quality assessment
        self.llm_manager = LLMManager(config)

        self.logger.info(f"Initialized with {len(self.venue_whitelist)} whitelisted venues")
        if self.llm_manager.get_feature_enabled('smart_quality'):
            self.logger.info("LLM-enhanced quality assessment enabled")
    
    def process(self, input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter papers based on quality criteria.
        
        Args:
            input_data: List of raw paper metadata dictionaries
        
        Returns:
            List of curated papers with quality scores and justifications
        """
        if not isinstance(input_data, list):
            raise AgentError("Input must be a list of paper metadata dictionaries")
        
        self.logger.info(f"Starting quality curation for {len(input_data)} papers")
        
        curated_papers = []
        filter_stats = {
            'total_input': len(input_data),
            'venue_filtered': 0,
            'citation_filtered': 0,
            'year_filtered': 0,
            'quality_passed': 0
        }
        
        for paper in input_data:
            # Apply quality filters
            quality_result = self._evaluate_paper_quality(paper)
            
            if quality_result['passed']:
                # Add quality metrics to paper
                paper['quality_metrics'] = quality_result['metrics']
                paper['filtering_reason'] = quality_result['reason']
                curated_papers.append(paper)
                filter_stats['quality_passed'] += 1
            else:
                # Track filtering reasons
                if 'venue' in quality_result['reason'].lower():
                    filter_stats['venue_filtered'] += 1
                elif 'citation' in quality_result['reason'].lower():
                    filter_stats['citation_filtered'] += 1
                elif 'year' in quality_result['reason'].lower():
                    filter_stats['year_filtered'] += 1
        
        # Sort by quality score
        curated_papers.sort(key=lambda x: x['quality_metrics']['quality_score'], reverse=True)
        
        self.logger.info(f"Quality curation completed: {len(curated_papers)} papers passed filters")
        self.logger.info(f"Filter stats: {filter_stats}")
        
        return curated_papers
    
    def _evaluate_paper_quality(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate individual paper quality.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Dictionary with evaluation results
        """
        venue = paper.get('venue', '').strip()
        year = paper.get('year', 0)
        citation_count = paper.get('citation_count', 0)
        paper_type = paper.get('type', 'journal')
        
        # Initialize quality metrics
        quality_metrics = {
            'venue_rank': None,
            'h5_index': None,
            'quality_score': 0.0,
            'citation_impact': 0.0
        }
        
        # Check publication year
        if year < self.min_pub_year:
            return {
                'passed': False,
                'reason': f'Publication year {year} below minimum threshold {self.min_pub_year}',
                'metrics': quality_metrics
            }
        
        # Check minimum citations
        if citation_count < self.min_citations:
            return {
                'passed': False,
                'reason': f'Citation count {citation_count} below minimum threshold {self.min_citations}',
                'metrics': quality_metrics
            }
        
        # Evaluate venue quality
        venue_evaluation = self._evaluate_venue(venue, paper_type)
        quality_metrics.update(venue_evaluation['metrics'])
        
        if not venue_evaluation['passed']:
            return {
                'passed': False,
                'reason': venue_evaluation['reason'],
                'metrics': quality_metrics
            }
        
        # Calculate citation impact score
        citation_impact = self._calculate_citation_impact(citation_count, year)
        quality_metrics['citation_impact'] = citation_impact
        
        # Calculate overall quality score
        quality_score = self._calculate_quality_score(quality_metrics, paper)
        quality_metrics['quality_score'] = quality_score

        # Enhance with LLM-based quality assessment if enabled
        if self.llm_manager.get_feature_enabled('smart_quality'):
            llm_assessment = self._llm_quality_assessment(paper)
            if llm_assessment:
                quality_metrics.update(llm_assessment)
                # Adjust quality score based on LLM assessment
                llm_score = llm_assessment.get('llm_quality_score', 0)
                quality_metrics['quality_score'] = (quality_score + llm_score) / 2

        return {
            'passed': True,
            'reason': f'High-quality paper: {venue_evaluation["reason"]}, {citation_count} citations',
            'metrics': quality_metrics
        }
    
    def _evaluate_venue(self, venue: str, paper_type: str) -> Dict[str, Any]:
        """
        Evaluate venue quality and reputation.
        
        Args:
            venue: Venue name
            paper_type: Type of publication (journal/conference/preprint)
            
        Returns:
            Dictionary with venue evaluation results
        """
        # Check venue whitelist first
        if self._is_venue_whitelisted(venue):
            venue_rank = self._get_venue_quartile(venue)
            h5_index = self._get_venue_h5_index(venue)
            
            return {
                'passed': True,
                'reason': f'Whitelisted venue: {venue}',
                'metrics': {
                    'venue_rank': venue_rank.value if venue_rank else None,
                    'h5_index': h5_index
                }
            }
        
        # For arXiv preprints, apply different criteria
        if paper_type == VenueType.PREPRINT.value or venue.lower() == 'arxiv':
            return {
                'passed': True,
                'reason': 'Preprint venue (arXiv)',
                'metrics': {
                    'venue_rank': None,
                    'h5_index': None
                }
            }
        
        # Check if venue meets quartile requirements
        venue_rank = self._get_venue_quartile(venue)
        if venue_rank and venue_rank.value in self.venue_quartiles:
            h5_index = self._get_venue_h5_index(venue)
            
            if h5_index and h5_index >= self.min_h5_index:
                return {
                    'passed': True,
                    'reason': f'High-quality venue: {venue} ({venue_rank.value}, H5-index: {h5_index})',
                    'metrics': {
                        'venue_rank': venue_rank.value,
                        'h5_index': h5_index
                    }
                }
        
        return {
            'passed': False,
            'reason': f'Venue does not meet quality criteria: {venue}',
            'metrics': {
                'venue_rank': venue_rank.value if venue_rank else None,
                'h5_index': self._get_venue_h5_index(venue)
            }
        }
    
    def _is_venue_whitelisted(self, venue: str) -> bool:
        """Check if venue is in the whitelist."""
        venue_lower = venue.lower()
        
        for whitelisted_venue in self.venue_whitelist:
            if whitelisted_venue.lower() in venue_lower or venue_lower in whitelisted_venue.lower():
                return True
        
        return False
    
    def _get_venue_quartile(self, venue: str) -> VenueQuartile:
        """Get venue quartile ranking."""
        venue_lower = venue.lower()
        
        # Check venue rankings database
        for venue_pattern, quartile in self.venue_rankings.items():
            if venue_pattern.lower() in venue_lower:
                return VenueQuartile(quartile)
        
        # Default to Q3 for unknown venues
        return VenueQuartile.Q3
    
    def _get_venue_h5_index(self, venue: str) -> int:
        """Get venue H5-index (simplified implementation)."""
        # This would typically query a database or API
        # For now, we'll use estimated values based on venue reputation
        venue_lower = venue.lower()
        
        # High-impact venues
        if any(term in venue_lower for term in ['nature', 'science', 'cell']):
            return 200
        elif any(term in venue_lower for term in ['ieee transactions', 'mechanical systems']):
            return 80
        elif any(term in venue_lower for term in ['reliability engineering', 'expert systems']):
            return 60
        elif 'ieee' in venue_lower:
            return 40
        else:
            return 25  # Default for unknown venues
    
    def _calculate_citation_impact(self, citation_count: int, year: int) -> float:
        """Calculate citation impact score normalized by paper age."""
        current_year = datetime.now().year
        paper_age = max(current_year - year, 1)  # Avoid division by zero
        
        # Normalize citations by paper age
        citations_per_year = citation_count / paper_age
        
        # Apply logarithmic scaling to handle outliers
        import math
        impact_score = math.log(citations_per_year + 1) / math.log(10)  # Log base 10
        
        return min(impact_score, 3.0)  # Cap at 3.0
    
    def _calculate_quality_score(self, metrics: Dict[str, Any], paper: Dict[str, Any]) -> float:
        """Calculate overall quality score for the paper."""
        score = 0.0
        
        # Venue quality (40% weight)
        venue_rank = metrics.get('venue_rank')
        if venue_rank == 'Q1':
            score += 0.4
        elif venue_rank == 'Q2':
            score += 0.3
        elif venue_rank == 'Q3':
            score += 0.2
        elif venue_rank == 'Q4':
            score += 0.1
        
        # Citation impact (30% weight)
        citation_impact = metrics.get('citation_impact', 0)
        score += min(citation_impact / 3.0, 1.0) * 0.3
        
        # Relevance score (20% weight)
        relevance_score = paper.get('relevance_score', 0)
        score += relevance_score * 0.2
        
        # Recency bonus (10% weight)
        current_year = datetime.now().year
        paper_year = paper.get('year', 0)
        recency_score = max(0, 1 - (current_year - paper_year) / 10)  # Decay over 10 years
        score += recency_score * 0.1
        
        return round(score, 3)
    
    def _load_venue_rankings(self) -> Dict[str, str]:
        """Load venue rankings database."""
        # This would typically load from a database or file
        # For now, we'll use a hardcoded mapping
        return {
            'Mechanical Systems and Signal Processing': 'Q1',
            'Reliability Engineering & System Safety': 'Q1',
            'IEEE Transactions on Reliability': 'Q1',
            'IEEE Transactions on Industrial Electronics': 'Q1',
            'IEEE Transactions on Instrumentation and Measurement': 'Q1',
            'Journal of Sound and Vibration': 'Q1',
            'Expert Systems with Applications': 'Q1',
            'Engineering Applications of Artificial Intelligence': 'Q2',
            'Computers & Industrial Engineering': 'Q2',
            'International Journal of Prognostics and Health Management': 'Q2',
            'IEEE Access': 'Q2',
            'Sensors': 'Q2',
            'Applied Sciences': 'Q3',
            'Electronics': 'Q3'
        }

    def _llm_quality_assessment(self, paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use LLM to assess paper quality beyond simple metrics.

        Args:
            paper: Paper metadata dictionary

        Returns:
            Dictionary with LLM-based quality metrics or None if assessment fails
        """
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        venue = paper.get('venue', '')
        year = paper.get('year', 0)

        prompt = f"""
Please assess the quality of this PHM research paper based on methodology rigor, novelty, and research impact.

Title: {title}

Abstract: {abstract}

Venue: {venue}
Year: {year}

Please evaluate the following aspects and provide scores from 0.0 to 1.0:

1. **Methodology Rigor**: How sound and well-designed is the research methodology?
2. **Novelty**: How novel and innovative is the contribution?
3. **Research Impact**: How significant is the potential impact on the PHM field?
4. **Technical Quality**: How technically sound and well-executed is the work?
5. **Clarity**: How clear and well-written is the research presentation?

For each aspect, provide:
- Score (0.0-1.0)
- Brief justification (1-2 sentences)

Also provide an overall quality score (0.0-1.0) and assessment.

Format your response as:
Methodology Rigor: [score] - [justification]
Novelty: [score] - [justification]
Research Impact: [score] - [justification]
Technical Quality: [score] - [justification]
Clarity: [score] - [justification]
Overall Quality: [score] - [overall assessment]"""

        try:
            response = self.llm_manager.generate_text(prompt, max_tokens=600, temperature=0.3)
            if response:
                return self._parse_llm_quality_response(response)
        except Exception as e:
            self.logger.warning(f"LLM quality assessment failed: {e}")

        return None

    def _parse_llm_quality_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM quality assessment response."""
        metrics = {}

        try:
            lines = response.strip().split('\n')

            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()

                    # Extract score (first number in the value)
                    import re
                    score_match = re.search(r'(\d+\.?\d*)', value)
                    if score_match:
                        score = float(score_match.group(1))

                        # Normalize score to 0-1 range if needed
                        if score > 1.0:
                            score = score / 10.0 if score <= 10.0 else 1.0

                        metrics[f'llm_{key}_score'] = min(max(score, 0.0), 1.0)

                        # Extract justification (text after the score)
                        justification = value[score_match.end():].strip(' -')
                        if justification:
                            metrics[f'llm_{key}_justification'] = justification

            # Set overall LLM quality score
            if 'llm_overall_quality_score' in metrics:
                metrics['llm_quality_score'] = metrics['llm_overall_quality_score']
            else:
                # Calculate average if overall not provided
                score_keys = [k for k in metrics.keys() if k.endswith('_score') and k != 'llm_quality_score']
                if score_keys:
                    avg_score = sum(metrics[k] for k in score_keys) / len(score_keys)
                    metrics['llm_quality_score'] = avg_score

        except Exception as e:
            self.logger.error(f"Error parsing LLM quality response: {e}")
            return {}

        return metrics


if __name__ == "__main__":
    # Test the agent
    config = {
        'quality_filters': {
            'venue_whitelist': ['IEEE Transactions on Reliability', 'Mechanical Systems and Signal Processing'],
            'min_citations': 5,
            'venue_quartile': ['Q1', 'Q2'],
            'min_h5_index': 20,
            'min_publication_year': 2015
        }
    }
    
    agent = QualityCurationAgent(config)
    
    test_papers = [
        {
            'title': 'Test Paper 1',
            'venue': 'IEEE Transactions on Reliability',
            'year': 2023,
            'citation_count': 15,
            'type': 'journal',
            'relevance_score': 0.8
        },
        {
            'title': 'Test Paper 2',
            'venue': 'Unknown Journal',
            'year': 2023,
            'citation_count': 2,
            'type': 'journal',
            'relevance_score': 0.6
        }
    ]
    
    result = agent.run(test_papers)
    print(f"Curated {len(result)} papers from {len(test_papers)} input papers")
