"""
Enhanced Content Analysis Agent for APPA system.

This agent generates comprehensive structured analysis using advanced LLM techniques
and MCP integration for deep paper understanding.

Key Features:
- Multi-tier analysis (TL;DR, Key Points, Deep Analysis, Research Context)
- LLM-enhanced content understanding
- PHM domain-specific analysis
- Reproducibility assessment
- Technical methodology extraction
- Impact and novelty evaluation
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentError
from ..models import AnalysisResult
from ..utils.llm_client import LLMManager
from ..utils.mcp_integration import MCPAcademicTools
from ..utils.paper_utils import (
    calculate_phm_relevance_score, classify_methodology, 
    identify_application_domains, assess_venue_quality
)
from ..utils.phm_constants import (
    PHM_CONCEPTS, METHODOLOGY_KEYWORDS, APPLICATION_DOMAINS,
    VENUE_QUALITY_MAPPING, RELEVANCE_THRESHOLDS
)


class ContentAnalysisAgent(BaseAgent):
    """
    Enhanced Content Analysis Agent with advanced LLM and MCP integration.
    
    Provides comprehensive multi-tier analysis:
    - Automated TL;DR generation
    - Key contributions extraction
    - Deep technical analysis
    - Research context and impact assessment
    - Reproducibility evaluation
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "EnhancedContentAnalysisAgent")
        
        # Analysis configuration
        self.analysis_config = self.get_config_value('content_analysis', {})
        self.output_config = self.get_config_value('output_preferences', {})
        
        # Analysis settings
        self.summary_length = self.output_config.get('summary_length', 'medium')
        self.include_reproducibility = self.analysis_config.get('include_reproducibility', True)
        self.include_impact_analysis = self.analysis_config.get('include_impact_analysis', True)
        self.include_methodology_extraction = self.analysis_config.get('include_methodology_extraction', True)
        self.enable_multilingual = self.analysis_config.get('enable_multilingual', True)
        
        # PHM domain knowledge from centralized constants
        self.phm_concepts = PHM_CONCEPTS
        self.methodology_keywords = METHODOLOGY_KEYWORDS
        self.application_domains = APPLICATION_DOMAINS

        # Initialize LLM manager and MCP tools
        self.llm_manager = LLMManager(config)
        self.mcp_tools = MCPAcademicTools(config)

        self.logger.info("Enhanced Content Analysis Agent initialized")
        if self.llm_manager.is_enabled():
            self.logger.info("Advanced LLM analysis enabled")
        else:
            self.logger.info("Using traditional analysis methods")
    
    def process(self, input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhanced analysis of paper content with comprehensive multi-tier summaries.
        
        Args:
            input_data: List of paper metadata dictionaries
            
        Returns:
            List of papers with enhanced analysis including:
            - TL;DR summaries (Chinese and English)
            - Key contributions and methodology
            - Deep technical analysis
            - Research context and impact
            - Reproducibility assessment
        """
        if not isinstance(input_data, list):
            raise AgentError("Input must be a list of paper metadata dictionaries")
        
        self.logger.info(f"Starting enhanced content analysis for {len(input_data)} papers")
        
        analyzed_papers = []
        
        for i, paper in enumerate(input_data):
            try:
                paper_title = paper.get('title', 'Unknown')[:50]
                self.logger.debug(f"Analyzing paper {i+1}/{len(input_data)}: {paper_title}")
                
                # Generate comprehensive analysis
                analysis = self._generate_comprehensive_analysis(paper)
                
                # Add analysis to paper
                paper['analysis'] = analysis
                paper['analysis_timestamp'] = datetime.now().isoformat()
                paper['analysis_agent'] = 'enhanced_content_analysis'
                
                analyzed_papers.append(paper)
                
            except Exception as e:
                self.logger.error(f"Error analyzing paper '{paper.get('title', 'Unknown')}': {e}")
                # Add fallback analysis
                paper['analysis'] = self._create_fallback_analysis(paper, str(e))
                paper['analysis_error'] = str(e)
                analyzed_papers.append(paper)
        
        self.logger.info(f"Enhanced analysis completed for {len(analyzed_papers)} papers")
        return analyzed_papers
    
    def _generate_comprehensive_analysis(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive multi-tier analysis of a paper.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Comprehensive analysis results dictionary
        """
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        keywords = paper.get('keywords', [])
        
        if not title or not abstract:
            return self._create_fallback_analysis(paper, "Missing title or abstract")
        
        analysis = {
            'analysis_version': '2.0',
            'analysis_date': datetime.now().isoformat(),
            'paper_id': paper.get('doi', title[:50])
        }
        
        try:
            # Tier 1: TL;DR Generation using centralized function
            paper_dict = {'title': title, 'abstract': abstract}
            tldr_chinese = generate_tldr_summary(paper_dict, self.llm_manager, 'chinese')
            tldr_english = generate_tldr_summary(paper_dict, self.llm_manager, 'english')
            analysis['tldr'] = {
                'chinese_summary': tldr_chinese or 'TL;DR generation not available',
                'english_summary': tldr_english or 'TL;DR generation not available'
            }
            
            # Tier 2: Key Points Extraction
            analysis['key_points'] = self._extract_key_points(title, abstract, keywords)
            
            # Tier 3: Deep Technical Analysis
            analysis['deep_analysis'] = self._generate_deep_analysis(paper)
            
            # Tier 4: Research Context and Impact
            if self.include_impact_analysis:
                analysis['research_context'] = self._analyze_research_context(paper)
            
            # Tier 5: Reproducibility Assessment
            if self.include_reproducibility:
                analysis['reproducibility'] = self._assess_reproducibility(paper)
            
            # Additional enhancements
            analysis['methodology_classification'] = classify_methodology(paper)
            analysis['application_domain'] = identify_application_domains(paper)
            analysis['phm_relevance'] = self._calculate_phm_relevance_detailed(paper)
            
            # Quality indicators
            analysis['analysis_quality'] = self._calculate_analysis_quality(analysis)
            analysis['analysis_status'] = 'complete'
            
        except Exception as e:
            self.logger.warning(f"Partial analysis failure: {e}")
            analysis['analysis_error'] = str(e)
            analysis['analysis_status'] = 'partial'
        
        return analysis
    
    
    def _extract_key_points(self, title: str, abstract: str, keywords: List[str]) -> Dict[str, Any]:
        """Extract key points including objectives, methods, and contributions."""
        key_points = {
            'research_objective': '',
            'methodology': [],
            'main_contributions': [],
            'technical_novelty': '',
            'experimental_validation': ''
        }
        
        if self.llm_manager.is_enabled():
            points_prompt = f"""
Analyze this PHM research paper and extract key points:

Title: {title}
Abstract: {abstract}
Keywords: {', '.join(keywords)}

Please extract:
1. Research objective (1 sentence)
2. Methodology (list 2-3 key methods)
3. Main contributions (list 2-4 contributions)
4. Technical novelty (what makes it innovative)
5. Experimental validation (how it was tested)

Return as structured text with clear sections.
"""
            try:
                response = self.llm_manager.generate_text(points_prompt, max_tokens=400, temperature=0.3)
                if response:
                    key_points = self._parse_key_points_response(response)
            except Exception as e:
                self.logger.warning(f"Key points extraction failed: {e}")
        
        # Enhance with traditional analysis
        if not key_points['methodology']:
            key_points['methodology'] = self._extract_methodologies_traditional(title, abstract)
        
        return key_points
    
    def _generate_deep_analysis(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deep technical analysis."""
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        deep_analysis = {
            'technical_approach': '',
            'innovation_analysis': '',
            'limitations_discussion': '',
            'future_work_potential': '',
            'practical_applications': [],
            'comparison_with_existing': ''
        }
        
        if self.llm_manager.is_enabled():
            deep_prompt = f"""
Provide a deep technical analysis of this PHM research paper:

Title: {title}
Abstract: {abstract}

Please analyze:
1. Technical approach and methodology details
2. What makes this work innovative compared to existing approaches
3. Potential limitations or challenges
4. Future work possibilities
5. Practical applications in industry
6. How it compares with existing solutions

Provide detailed analysis for each aspect.
"""
            try:
                response = self.llm_manager.generate_text(deep_prompt, max_tokens=600, temperature=0.4)
                if response:
                    deep_analysis = self._parse_deep_analysis_response(response)
            except Exception as e:
                self.logger.warning(f"Deep analysis generation failed: {e}")
        
        return deep_analysis
    
    def _analyze_research_context(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze research context and impact."""
        context = {
            'field_positioning': '',
            'research_gap_addressed': '',
            'potential_impact': '',
            'citation_context': {},
            'trend_alignment': '',
            'interdisciplinary_connections': []
        }
        
        # Analyze citation metrics
        citation_count = paper.get('citation_count', 0)
        year = paper.get('year', datetime.now().year)
        venue = paper.get('venue', '')
        
        context['citation_context'] = {
            'citation_count': citation_count,
            'years_since_publication': datetime.now().year - year,
            'citations_per_year': citation_count / max(1, datetime.now().year - year),
            'venue_quality': self._assess_venue_quality(venue)
        }
        
        # Use LLM for context analysis if available
        if self.llm_manager.is_enabled():
            context_prompt = f"""
Analyze the research context and impact of this PHM paper:

Title: {paper.get('title', '')}
Abstract: {paper.get('abstract', '')}
Venue: {venue}
Year: {year}
Citations: {citation_count}

Please analyze:
1. How this work positions itself in the PHM field
2. What research gap it addresses
3. Potential impact on the field and industry
4. How it aligns with current PHM trends
5. Interdisciplinary connections

Provide insightful analysis for each aspect.
"""
            try:
                response = self.llm_manager.generate_text(context_prompt, max_tokens=500, temperature=0.4)
                if response:
                    parsed_context = self._parse_context_response(response)
                    context.update(parsed_context)
            except Exception as e:
                self.logger.warning(f"Research context analysis failed: {e}")
        
        return context
    
    def _assess_reproducibility(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Assess reproducibility of the research."""
        reproducibility = {
            'reproducibility_score': 0.0,
            'code_availability': 'unknown',
            'data_availability': 'unknown',
            'methodology_detail': 'medium',
            'experimental_setup_clarity': 'medium',
            'reproducibility_indicators': [],
            'improvement_suggestions': []
        }
        
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        urls = paper.get('urls', {})
        
        # Check for reproducibility indicators
        score = 0.0
        
        # Code availability indicators
        code_indicators = ['github', 'code', 'implementation', 'software', 'toolkit']
        if any(indicator in title + ' ' + abstract for indicator in code_indicators):
            reproducibility['code_availability'] = 'likely'
            score += 0.3
        
        # Data availability indicators
        data_indicators = ['dataset', 'benchmark', 'open data', 'public data', 'available data']
        if any(indicator in title + ' ' + abstract for indicator in data_indicators):
            reproducibility['data_availability'] = 'likely'
            score += 0.3
        
        # Methodology detail assessment
        method_indicators = ['algorithm', 'procedure', 'steps', 'implementation', 'parameters']
        method_count = sum(1 for indicator in method_indicators if indicator in abstract)
        if method_count >= 3:
            reproducibility['methodology_detail'] = 'high'
            score += 0.2
        elif method_count >= 1:
            reproducibility['methodology_detail'] = 'medium'
            score += 0.1
        
        # Experimental validation
        exp_indicators = ['experiment', 'validation', 'evaluation', 'comparison', 'benchmark']
        exp_count = sum(1 for indicator in exp_indicators if indicator in abstract)
        if exp_count >= 2:
            reproducibility['experimental_setup_clarity'] = 'high'
            score += 0.2
        
        reproducibility['reproducibility_score'] = min(score, 1.0)
        
        # Generate improvement suggestions
        if reproducibility['code_availability'] == 'unknown':
            reproducibility['improvement_suggestions'].append("Consider making code available")
        if reproducibility['data_availability'] == 'unknown':
            reproducibility['improvement_suggestions'].append("Consider sharing datasets or benchmarks")
        
        return reproducibility
    
    
    
    def _calculate_phm_relevance_detailed(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed PHM relevance score."""
        title = paper.get('title', '').lower()
        abstract = paper.get('abstract', '').lower()
        keywords = [kw.lower() for kw in paper.get('keywords', [])]
        
        relevance = {
            'overall_score': 0.0,
            'title_relevance': 0.0,
            'abstract_relevance': 0.0,
            'keyword_relevance': 0.0,
            'domain_alignment': 0.0,
            'phm_concepts_found': [],
            'relevance_explanation': ''
        }
        
        # Use centralized PHM relevance calculation
        overall_score, detailed_scores = calculate_phm_relevance_score(paper)
        
        # Map to expected format for backward compatibility
        relevance['title_relevance'] = detailed_scores.get('title_score', 0.0)
        relevance['abstract_relevance'] = detailed_scores.get('abstract_score', 0.0)
        relevance['keyword_relevance'] = detailed_scores.get('keyword_score', 0.0)
        relevance['domain_alignment'] = detailed_scores.get('venue_score', 0.0)
        relevance['phm_concepts_found'] = list(detailed_scores.get('concept_scores', {}).keys())
        relevance['overall_score'] = overall_score
        overall = overall_score  # For explanation generation below
        
        # Generate explanation
        if overall >= 0.8:
            relevance['relevance_explanation'] = "Highly relevant to PHM research"
        elif overall >= 0.6:
            relevance['relevance_explanation'] = "Moderately relevant to PHM"
        elif overall >= 0.4:
            relevance['relevance_explanation'] = "Somewhat relevant to PHM"
        else:
            relevance['relevance_explanation'] = "Limited PHM relevance"
        
        return relevance
    
    def _calculate_analysis_quality(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate quality metrics for the analysis."""
        quality = {
            'completeness_score': 0.0,
            'depth_score': 0.0,
            'accuracy_indicators': [],
            'overall_quality': 'medium'
        }
        
        # Completeness assessment
        required_sections = ['tldr', 'key_points', 'methodology_classification', 'phm_relevance']
        present_sections = sum(1 for section in required_sections if section in analysis and analysis[section])
        quality['completeness_score'] = present_sections / len(required_sections)
        
        # Depth assessment
        depth_indicators = []
        if analysis.get('deep_analysis') and len(str(analysis['deep_analysis'])) > 200:
            depth_indicators.append('detailed_technical_analysis')
        if analysis.get('research_context'):
            depth_indicators.append('research_context_provided')
        if analysis.get('reproducibility'):
            depth_indicators.append('reproducibility_assessment')
        
        quality['depth_score'] = len(depth_indicators) / 3
        quality['accuracy_indicators'] = depth_indicators
        
        # Overall quality
        overall_score = (quality['completeness_score'] + quality['depth_score']) / 2
        if overall_score >= 0.8:
            quality['overall_quality'] = 'high'
        elif overall_score >= 0.6:
            quality['overall_quality'] = 'medium'
        else:
            quality['overall_quality'] = 'basic'
        
        return quality
    
    def _create_fallback_analysis(self, paper: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Create fallback analysis when enhanced analysis fails."""
        return {
            'analysis_version': '2.0_fallback',
            'analysis_date': datetime.now().isoformat(),
            'analysis_status': 'fallback',
            'error_message': error_msg,
            'tldr': {
                'chinese': '分析失败，请检查论文内容',
                'english': 'Analysis failed, please check paper content'
            },
            'key_points': {
                'research_objective': '无法提取',
                'methodology': ['传统方法'],
                'main_contributions': ['需要人工分析']
            },
            'methodology_classification': {
                'primary_category': 'Unknown',
                'confidence_score': 0.0
            },
            'phm_relevance': {
                'overall_score': 0.5,
                'relevance_explanation': '需要进一步评估'
            }
        }
    
    # Helper methods for parsing LLM responses
    
    def _parse_key_points_response(self, response: str) -> Dict[str, Any]:
        """Parse key points from LLM response."""
        key_points = {
            'research_objective': '',
            'methodology': [],
            'main_contributions': [],
            'technical_novelty': '',
            'experimental_validation': ''
        }
        
        # Simple parsing logic - can be enhanced
        lines = response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if 'objective' in line.lower():
                current_section = 'research_objective'
            elif 'methodology' in line.lower() or 'method' in line.lower():
                current_section = 'methodology'
            elif 'contribution' in line.lower():
                current_section = 'main_contributions'
            elif 'novelty' in line.lower() or 'innovation' in line.lower():
                current_section = 'technical_novelty'
            elif 'validation' in line.lower() or 'experiment' in line.lower():
                current_section = 'experimental_validation'
            else:
                # Content line
                if current_section:
                    if current_section in ['methodology', 'main_contributions']:
                        # List items
                        clean_line = re.sub(r'^[-*•\d\.)\s]+', '', line)
                        if clean_line:
                            key_points[current_section].append(clean_line)
                    else:
                        # Single text
                        if not key_points[current_section]:
                            key_points[current_section] = line
                        else:
                            key_points[current_section] += ' ' + line
        
        return key_points
    
    def _parse_deep_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse deep analysis from LLM response."""
        deep_analysis = {
            'technical_approach': '',
            'innovation_analysis': '',
            'limitations_discussion': '',
            'future_work_potential': '',
            'practical_applications': [],
            'comparison_with_existing': ''
        }
        
        # Simple parsing - extract paragraphs
        paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
        
        if len(paragraphs) >= 1:
            deep_analysis['technical_approach'] = paragraphs[0]
        if len(paragraphs) >= 2:
            deep_analysis['innovation_analysis'] = paragraphs[1]
        if len(paragraphs) >= 3:
            deep_analysis['limitations_discussion'] = paragraphs[2]
        if len(paragraphs) >= 4:
            deep_analysis['future_work_potential'] = paragraphs[3]
        
        return deep_analysis
    
    def _parse_context_response(self, response: str) -> Dict[str, Any]:
        """Parse research context from LLM response."""
        context = {
            'field_positioning': '',
            'research_gap_addressed': '',
            'potential_impact': '',
            'trend_alignment': '',
            'interdisciplinary_connections': []
        }
        
        # Simple parsing
        sentences = response.split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            if 'position' in sentence.lower() or 'field' in sentence.lower():
                context['field_positioning'] = sentence
            elif 'gap' in sentence.lower():
                context['research_gap_addressed'] = sentence
            elif 'impact' in sentence.lower():
                context['potential_impact'] = sentence
            elif 'trend' in sentence.lower():
                context['trend_alignment'] = sentence
        
        return context
    
    def _generate_keyword_tldr(self, title: str, abstract: str) -> Dict[str, str]:
        """Generate basic TL;DR using keyword extraction."""
        # Extract key phrases
        text = (title + ' ' + abstract).lower()
        
        # Simple keyword-based summary
        method_found = False
        result_found = False
        
        methods = ['deep learning', 'machine learning', 'neural network', 'algorithm']
        results = ['accuracy', 'improvement', 'performance', 'effective']
        
        method_word = 'advanced method'
        for method in methods:
            if method in text:
                method_word = method
                method_found = True
                break
        
        result_word = 'good results'
        for result in results:
            if result in text:
                result_word = f'improved {result}'
                result_found = True
                break
        
        chinese_tldr = f"使用{method_word}进行PHM研究，取得{result_word}"
        english_tldr = f"PHM research using {method_word} achieves {result_word}"
        
        return {
            'chinese': chinese_tldr,
            'english': english_tldr
        }
    
    def _extract_methodologies_traditional(self, title: str, abstract: str) -> List[str]:
        """Extract methodologies using traditional keyword matching."""
        text = (title + ' ' + abstract).lower()
        methodologies = []
        
        method_keywords = {
            'Deep Learning': ['deep learning', 'neural network', 'cnn', 'lstm'],
            'Machine Learning': ['machine learning', 'svm', 'random forest'],
            'Signal Processing': ['signal processing', 'wavelet', 'fft'],
            'Statistical Analysis': ['statistical', 'bayesian', 'regression']
        }
        
        for category, keywords in method_keywords.items():
            if any(kw in text for kw in keywords):
                methodologies.append(category)
        
        return methodologies[:3]  # Limit to 3
    
    def _assess_venue_quality(self, venue: str) -> str:
        """Assess venue quality based on known journals/conferences."""
        if not venue:
            return 'unknown'
        
        venue_lower = venue.lower()
        
        # High-quality PHM venues
        high_quality = [
            'mechanical systems and signal processing',
            'ieee transactions on industrial electronics',
            'reliability engineering & system safety',
            'expert systems with applications',
            'ieee transactions on reliability'
        ]
        
        medium_quality = [
            'journal of sound and vibration',
            'measurement',
            'sensors',
            'applied sciences'
        ]
        
        for hq_venue in high_quality:
            if hq_venue in venue_lower:
                return 'high'
        
        for mq_venue in medium_quality:
            if mq_venue in venue_lower:
                return 'medium'
        
        return 'unknown'
    
    # Domain knowledge loading methods
    
    # PHM concepts moved to phm_constants.PHM_CONCEPTS
    
    # Methodology keywords moved to phm_constants.METHODOLOGY_KEYWORDS
    
    # Application domains moved to phm_constants.APPLICATION_DOMAINS


# Export functions for external use

def create_enhanced_analysis_summary(analysis: Dict[str, Any]) -> Dict[str, str]:
    """Create a summary of the enhanced analysis for display."""
    summary = {}
    
    if analysis.get('tldr'):
        summary['TL;DR'] = analysis['tldr'].get('chinese', 'N/A')
    
    if analysis.get('methodology_classification'):
        method = analysis['methodology_classification']
        summary['方法类别'] = method.get('primary_category', 'Unknown')
    
    if analysis.get('phm_relevance'):
        relevance = analysis['phm_relevance']
        score = relevance.get('overall_score', 0)
        summary['PHM相关性'] = f"{score:.2f} - {relevance.get('relevance_explanation', '')}"
    
    if analysis.get('analysis_quality'):
        quality = analysis['analysis_quality']
        summary['分析质量'] = quality.get('overall_quality', 'medium')
    
    return summary