"""
Content Analysis Agent for APPA system.

This agent generates structured summaries and extracts metadata from papers.

Single Responsibility: Generate structured summaries and extract metadata
Input: Paper metadata with abstracts
Output: Three-tier analysis documents with validated metadata
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentError
from ..models import AnalysisResult
from ..utils.llm_client import LLMManager


class ContentAnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing paper content and generating structured summaries.
    
    Generates three-tier analysis: TL;DR, Key Points, and Deep Analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "ContentAnalysisAgent")
        
        # Analysis configuration
        self.output_config = self.get_config_value('output_preferences', {})
        self.summary_length = self.output_config.get('summary_length', 'medium')
        self.include_reproducibility = self.output_config.get('include_reproducibility', True)
        
        # PHM domain knowledge
        self.phm_concepts = self._load_phm_concepts()
        self.methodology_keywords = self._load_methodology_keywords()

        # Initialize LLM manager
        self.llm_manager = LLMManager(config)

        self.logger.info("Initialized Content Analysis Agent")
        if self.llm_manager.is_enabled():
            self.logger.info("LLM-enhanced analysis enabled")
        else:
            self.logger.info("Using traditional analysis methods")
    
    def process(self, input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze paper content and generate structured summaries.
        
        Args:
            input_data: List of paper metadata dictionaries with abstracts
        
        Returns:
            List of papers with analysis results added
        """
        if not isinstance(input_data, list):
            raise AgentError("Input must be a list of paper metadata dictionaries")
        
        self.logger.info(f"Starting content analysis for {len(input_data)} papers")
        
        analyzed_papers = []
        
        for i, paper in enumerate(input_data):
            try:
                self.logger.debug(f"Analyzing paper {i+1}/{len(input_data)}: {paper.get('title', 'Unknown')}")
                
                # Generate analysis
                analysis = self._analyze_paper(paper)
                
                # Add analysis to paper
                paper['analysis'] = analysis
                paper['analysis_timestamp'] = datetime.now().isoformat()
                
                analyzed_papers.append(paper)
                
            except Exception as e:
                self.logger.error(f"Error analyzing paper '{paper.get('title', 'Unknown')}': {e}")
                # Add empty analysis to maintain structure
                paper['analysis'] = self._create_empty_analysis()
                paper['analysis_error'] = str(e)
                analyzed_papers.append(paper)
        
        self.logger.info(f"Content analysis completed for {len(analyzed_papers)} papers")
        return analyzed_papers
    
    def _analyze_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze individual paper and generate structured summary.
        
        Args:
            paper: Paper metadata dictionary
            
        Returns:
            Analysis results dictionary
        """
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        keywords = paper.get('keywords', [])
        
        if not abstract:
            raise ValueError("Paper abstract is required for analysis")
        
        # Generate TL;DR (≤50 words)
        tldr = self._generate_tldr(title, abstract)
        
        # Generate Key Points (4-6 bullets)
        key_points = self._generate_key_points(title, abstract, keywords)
        
        # Generate Deep Analysis (500-800 words)
        deep_analysis = self._generate_deep_analysis(paper)
        
        # Extract topics
        extracted_topics = self._extract_topics(title, abstract, keywords)
        
        # Calculate reproducibility score
        reproducibility_score = self._assess_reproducibility(abstract) if self.include_reproducibility else 0.0
        
        return {
            'tldr': tldr,
            'key_points': key_points,
            'deep_analysis': deep_analysis,
            'extracted_topics': extracted_topics,
            'reproducibility_score': reproducibility_score
        }
    
    def _generate_tldr(self, title: str, abstract: str) -> str:
        """
        Generate TL;DR summary (≤50 words).

        Args:
            title: Paper title
            abstract: Paper abstract

        Returns:
            TL;DR summary string
        """
        # Try LLM-enhanced generation first
        if self.llm_manager.get_feature_enabled('enhanced_analysis'):
            llm_tldr = self._generate_llm_tldr(title, abstract)
            if llm_tldr:
                return llm_tldr

        # Fallback to traditional method
        return self._generate_traditional_tldr(title, abstract)

    def _generate_llm_tldr(self, title: str, abstract: str) -> str:
        """Generate TL;DR using LLM."""
        prompt = f"""
Please create a concise TL;DR summary (maximum 50 words) for this PHM research paper.

Title: {title}

Abstract: {abstract}

Requirements:
- Maximum 50 words
- Focus on the main contribution and methodology
- Use clear, accessible language
- Highlight the PHM application domain
- Do not include citations or references

TL;DR:"""

        try:
            response = self.llm_manager.generate_text(prompt, max_tokens=100, temperature=0.3)
            if response:
                # Clean and validate response
                tldr = response.strip()
                if tldr.startswith("TL;DR:"):
                    tldr = tldr[6:].strip()

                # Ensure word limit
                words = tldr.split()
                if len(words) <= 50:
                    return tldr
                else:
                    return ' '.join(words[:47]) + "..."
        except Exception as e:
            self.logger.warning(f"LLM TL;DR generation failed: {e}")

        return ""

    def _generate_traditional_tldr(self, title: str, abstract: str) -> str:
        """Generate TL;DR using traditional methods."""
        # Extract key sentences from abstract
        sentences = self._split_sentences(abstract)

        # Find the most informative sentence (usually the first or last)
        key_sentence = ""
        if sentences:
            # Prefer sentences with methodology or results keywords
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in ['propose', 'develop', 'demonstrate', 'show', 'achieve']):
                    key_sentence = sentence
                    break

            if not key_sentence:
                key_sentence = sentences[0]  # Fallback to first sentence

        # Extract main contribution from title and key sentence
        main_method = self._extract_main_method(title + " " + key_sentence)
        main_application = self._extract_main_application(title + " " + key_sentence)

        # Construct TL;DR
        if main_method and main_application:
            tldr = f"This paper presents {main_method} for {main_application} in PHM applications."
        elif main_method:
            tldr = f"This paper proposes {main_method} for prognostics and health management."
        else:
            # Fallback: use first 50 words of abstract
            words = abstract.split()[:45]
            tldr = ' '.join(words) + "..."

        # Ensure word limit
        tldr_words = tldr.split()
        if len(tldr_words) > 50:
            tldr = ' '.join(tldr_words[:47]) + "..."

        return tldr.strip()
    
    def _generate_key_points(self, title: str, abstract: str, keywords: List[str]) -> List[str]:
        """
        Generate 4-6 key points summarizing the paper.

        Args:
            title: Paper title
            abstract: Paper abstract
            keywords: Paper keywords

        Returns:
            List of key points
        """
        # Try LLM-enhanced generation first
        if self.llm_manager.get_feature_enabled('enhanced_analysis'):
            llm_points = self._generate_llm_key_points(title, abstract, keywords)
            if llm_points:
                return llm_points

        # Fallback to traditional method
        return self._generate_traditional_key_points(title, abstract, keywords)

    def _generate_llm_key_points(self, title: str, abstract: str, keywords: List[str]) -> List[str]:
        """Generate key points using LLM."""
        prompt = f"""
Please extract 4-6 key points from this PHM research paper. Each point should be a single sentence with a bold category label.

Title: {title}

Abstract: {abstract}

Keywords: {', '.join(keywords)}

Please structure the key points as follows:
- **Objective**: [What problem does this paper address?]
- **Methodology**: [What approach/method is used?]
- **Results**: [What are the main findings/performance?]
- **Application**: [What is the specific PHM application domain?]
- **Significance**: [Why is this work important/novel?]
- **Limitations**: [Any limitations mentioned, if applicable]

Provide exactly 4-6 points, each starting with a bold category label followed by a colon.

Key Points:"""

        try:
            response = self.llm_manager.generate_text(prompt, max_tokens=400, temperature=0.3)
            if response:
                # Parse the response into key points
                lines = response.strip().split('\n')
                key_points = []

                for line in lines:
                    line = line.strip()
                    if line and ('**' in line or line.startswith('-')):
                        # Clean up the line
                        if line.startswith('-'):
                            line = line[1:].strip()
                        key_points.append(line)

                # Validate we have 4-6 points
                if 4 <= len(key_points) <= 6:
                    return key_points
        except Exception as e:
            self.logger.warning(f"LLM key points generation failed: {e}")

        return []

    def _generate_traditional_key_points(self, title: str, abstract: str, keywords: List[str]) -> List[str]:
        """Generate key points using traditional methods."""
        key_points = []

        # 1. Objective/Problem
        objective = self._extract_objective(abstract)
        if objective:
            key_points.append(f"**Objective**: {objective}")

        # 2. Methodology
        methodology = self._extract_methodology(title, abstract)
        if methodology:
            key_points.append(f"**Methodology**: {methodology}")

        # 3. Key Results
        results = self._extract_results(abstract)
        if results:
            key_points.append(f"**Results**: {results}")

        # 4. Application Domain
        application = self._extract_application_domain(title, abstract, keywords)
        if application:
            key_points.append(f"**Application**: {application}")

        # 5. Significance/Contribution
        significance = self._extract_significance(abstract)
        if significance:
            key_points.append(f"**Significance**: {significance}")

        # 6. Limitations (if identifiable)
        limitations = self._extract_limitations(abstract)
        if limitations and len(key_points) < 6:
            key_points.append(f"**Limitations**: {limitations}")

        # Ensure we have 4-6 points
        if len(key_points) < 4:
            # Add generic points if needed
            key_points.append("**Domain**: Prognostics and Health Management research")

        return key_points[:6]  # Limit to 6 points
    
    def _generate_deep_analysis(self, paper: Dict[str, Any]) -> str:
        """
        Generate deep analysis (500-800 words).
        
        Args:
            paper: Complete paper metadata
            
        Returns:
            Deep analysis string
        """
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        keywords = paper.get('keywords', [])
        venue = paper.get('venue', '')
        year = paper.get('year', 0)
        citation_count = paper.get('citation_count', 0)
        
        analysis_parts = []
        
        # 1. Background and Context (100-150 words)
        background = self._generate_background_section(title, abstract, keywords)
        analysis_parts.append(f"## Background and Context\n\n{background}")
        
        # 2. Methodology Analysis (150-200 words)
        methodology = self._generate_methodology_section(title, abstract)
        analysis_parts.append(f"## Methodology\n\n{methodology}")
        
        # 3. Contributions and Results (150-200 words)
        contributions = self._generate_contributions_section(abstract)
        analysis_parts.append(f"## Key Contributions\n\n{contributions}")
        
        # 4. Impact and Significance (100-150 words)
        impact = self._generate_impact_section(venue, year, citation_count, keywords)
        analysis_parts.append(f"## Impact and Significance\n\n{impact}")
        
        # 5. Reproducibility Assessment (if enabled)
        if self.include_reproducibility:
            reproducibility = self._generate_reproducibility_section(abstract)
            analysis_parts.append(f"## Reproducibility Assessment\n\n{reproducibility}")
        
        deep_analysis = '\n\n'.join(analysis_parts)
        
        # Ensure word count is within range
        word_count = len(deep_analysis.split())
        if word_count < 500:
            # Add more detail if too short
            additional_context = self._generate_additional_context(paper)
            deep_analysis += f"\n\n## Additional Context\n\n{additional_context}"
        elif word_count > 800:
            # Truncate if too long
            words = deep_analysis.split()[:800]
            deep_analysis = ' '.join(words) + "..."
        
        return deep_analysis
    
    def _extract_topics(self, title: str, abstract: str, keywords: List[str]) -> List[str]:
        """Extract research topics from paper content."""
        topics = set()
        
        # Add provided keywords
        topics.update(kw.lower() for kw in keywords)
        
        # Extract PHM concepts
        text = (title + " " + abstract).lower()
        for concept in self.phm_concepts:
            if concept in text:
                topics.add(concept)
        
        # Extract methodology topics
        for method in self.methodology_keywords:
            if method in text:
                topics.add(method)
        
        return sorted(list(topics))[:10]  # Limit to 10 topics
    
    def _assess_reproducibility(self, abstract: str) -> float:
        """Assess reproducibility based on abstract content."""
        score = 0.0
        abstract_lower = abstract.lower()
        
        # Check for data availability mentions
        if any(term in abstract_lower for term in ['dataset', 'data available', 'open source', 'github']):
            score += 0.3
        
        # Check for methodology detail
        if any(term in abstract_lower for term in ['algorithm', 'method', 'approach', 'procedure']):
            score += 0.2
        
        # Check for experimental setup
        if any(term in abstract_lower for term in ['experiment', 'validation', 'test', 'evaluation']):
            score += 0.2
        
        # Check for quantitative results
        if any(term in abstract_lower for term in ['accuracy', 'precision', 'recall', 'performance']):
            score += 0.2
        
        # Check for comparison
        if any(term in abstract_lower for term in ['compare', 'comparison', 'baseline', 'benchmark']):
            score += 0.1
        
        return min(score, 1.0)

    def _create_empty_analysis(self) -> Dict[str, Any]:
        """Create empty analysis structure for failed analyses."""
        return {
            'tldr': 'Analysis failed - unable to generate summary.',
            'key_points': ['Analysis could not be completed due to insufficient data.'],
            'deep_analysis': 'Deep analysis could not be generated for this paper.',
            'extracted_topics': [],
            'reproducibility_score': 0.0
        }

    def _load_phm_concepts(self) -> List[str]:
        """Load PHM domain concepts."""
        return [
            'prognostics', 'health management', 'fault diagnosis', 'condition monitoring',
            'predictive maintenance', 'remaining useful life', 'rul', 'anomaly detection',
            'failure prediction', 'degradation modeling', 'reliability analysis',
            'health assessment', 'system health', 'maintenance optimization',
            'fault detection', 'fault isolation', 'diagnostic', 'prognostic'
        ]

    def _load_methodology_keywords(self) -> List[str]:
        """Load methodology keywords."""
        return [
            'machine learning', 'deep learning', 'neural network', 'cnn', 'lstm', 'rnn',
            'support vector machine', 'svm', 'random forest', 'decision tree',
            'signal processing', 'feature extraction', 'time series analysis',
            'statistical analysis', 'bayesian', 'kalman filter', 'particle filter',
            'optimization', 'genetic algorithm', 'fuzzy logic', 'expert system'
        ]

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_main_method(self, text: str) -> str:
        """Extract main methodology from text."""
        text_lower = text.lower()

        # Look for methodology patterns
        method_patterns = [
            r'(deep learning|machine learning|neural network)',
            r'(support vector machine|svm)',
            r'(random forest|decision tree)',
            r'(bayesian|kalman filter|particle filter)',
            r'(genetic algorithm|optimization)',
            r'(signal processing|feature extraction)',
            r'(statistical analysis|time series)'
        ]

        for pattern in method_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1)

        return ""

    def _extract_main_application(self, text: str) -> str:
        """Extract main application domain from text."""
        text_lower = text.lower()

        # Look for application patterns
        app_patterns = [
            r'(bearing|gear|motor|engine|turbine|pump)',
            r'(fault diagnosis|condition monitoring|health assessment)',
            r'(predictive maintenance|remaining useful life)',
            r'(anomaly detection|failure prediction)',
            r'(vibration|acoustic|thermal|electrical)'
        ]

        for pattern in app_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(1)

        return "industrial systems"

    def _extract_objective(self, abstract: str) -> str:
        """Extract research objective from abstract."""
        sentences = self._split_sentences(abstract)

        # Look for objective indicators
        objective_indicators = ['aim', 'objective', 'goal', 'purpose', 'propose', 'present']

        for sentence in sentences[:3]:  # Check first 3 sentences
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in objective_indicators):
                return sentence.strip()

        # Fallback: return first sentence
        return sentences[0] if sentences else ""

    def _extract_methodology(self, title: str, abstract: str) -> str:
        """Extract methodology description."""
        text = title + " " + abstract
        method = self._extract_main_method(text)

        if method:
            return f"The paper employs {method} techniques for analysis and modeling."
        else:
            # Look for method descriptions in abstract
            sentences = self._split_sentences(abstract)
            for sentence in sentences:
                if any(word in sentence.lower() for word in ['method', 'approach', 'algorithm', 'technique']):
                    return sentence.strip()

        return "Methodology details are provided in the full paper."

    def _extract_results(self, abstract: str) -> str:
        """Extract key results from abstract."""
        sentences = self._split_sentences(abstract)

        # Look for result indicators
        result_indicators = ['result', 'show', 'demonstrate', 'achieve', 'accuracy', 'performance']

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in result_indicators):
                return sentence.strip()

        return "Experimental results validate the proposed approach."

    def _extract_application_domain(self, title: str, abstract: str, keywords: List[str]) -> str:
        """Extract application domain."""
        text = (title + " " + abstract + " " + " ".join(keywords)).lower()

        # Domain mapping
        domains = {
            'rotating machinery': ['bearing', 'gear', 'rotor', 'shaft', 'turbine'],
            'automotive': ['vehicle', 'car', 'automotive', 'engine', 'transmission'],
            'aerospace': ['aircraft', 'aerospace', 'flight', 'aviation', 'satellite'],
            'manufacturing': ['manufacturing', 'production', 'machining', 'tool'],
            'energy systems': ['power', 'energy', 'grid', 'renewable', 'battery'],
            'industrial equipment': ['pump', 'compressor', 'motor', 'valve', 'conveyor']
        }

        for domain, keywords_list in domains.items():
            if any(keyword in text for keyword in keywords_list):
                return domain

        return "industrial systems"

    def _extract_significance(self, abstract: str) -> str:
        """Extract significance or contribution."""
        sentences = self._split_sentences(abstract)

        # Look for significance indicators
        significance_indicators = ['significant', 'important', 'novel', 'contribution', 'advance']

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in significance_indicators):
                return sentence.strip()

        return "The work contributes to advancing PHM research and applications."

    def _extract_limitations(self, abstract: str) -> str:
        """Extract limitations if mentioned."""
        sentences = self._split_sentences(abstract)

        # Look for limitation indicators
        limitation_indicators = ['limitation', 'challenge', 'future work', 'however', 'but']

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(indicator in sentence_lower for indicator in limitation_indicators):
                return sentence.strip()

        return ""

    def _generate_background_section(self, title: str, abstract: str, keywords: List[str]) -> str:
        """Generate background and context section."""
        domain = self._extract_application_domain(title, abstract, keywords)
        method = self._extract_main_method(title + " " + abstract)

        background = f"This research addresses challenges in {domain} within the prognostics and health management (PHM) domain. "

        if method:
            background += f"The work leverages {method} approaches to tackle complex monitoring and diagnostic tasks. "

        background += "PHM systems are critical for ensuring operational safety, reducing maintenance costs, and optimizing system performance across various industrial applications."

        return background

    def _generate_methodology_section(self, title: str, abstract: str) -> str:
        """Generate methodology analysis section."""
        method = self._extract_main_method(title + " " + abstract)

        if method:
            methodology = f"The proposed approach is based on {method} techniques, which are well-suited for handling complex, high-dimensional data typical in PHM applications. "
        else:
            methodology = "The methodology combines established signal processing and analysis techniques with domain-specific knowledge. "

        methodology += "The approach addresses key challenges including feature extraction from sensor data, pattern recognition for fault identification, and predictive modeling for health assessment. "
        methodology += "The implementation considers practical constraints such as computational efficiency and real-time processing requirements."

        return methodology

    def _generate_contributions_section(self, abstract: str) -> str:
        """Generate contributions and results section."""
        results = self._extract_results(abstract)

        contributions = "The paper makes several key contributions to the PHM field: "
        contributions += "1) Development of an innovative approach for health monitoring and fault diagnosis, "
        contributions += "2) Validation through comprehensive experimental evaluation, and "
        contributions += "3) Demonstration of practical applicability in real-world scenarios. "

        if results:
            contributions += f"The experimental validation shows promising results: {results}"
        else:
            contributions += "The experimental results demonstrate the effectiveness of the proposed approach compared to existing methods."

        return contributions

    def _generate_impact_section(self, venue: str, year: int, citation_count: int, keywords: List[str]) -> str:
        """Generate impact and significance section."""
        impact = f"Published in {venue} ({year}), this work has garnered {citation_count} citations, "

        if citation_count > 50:
            impact += "indicating significant impact and recognition within the research community. "
        elif citation_count > 10:
            impact += "demonstrating moderate impact and relevance to the field. "
        else:
            impact += "representing emerging research with potential for future impact. "

        # Assess research trends
        if any(kw in ['deep learning', 'machine learning', 'ai'] for kw in keywords):
            impact += "The work aligns with current trends toward AI-driven PHM solutions, "

        impact += "contributing to the advancement of intelligent maintenance strategies and industrial IoT applications."

        return impact

    def _generate_reproducibility_section(self, abstract: str) -> str:
        """Generate reproducibility assessment section."""
        score = self._assess_reproducibility(abstract)

        if score >= 0.7:
            reproducibility = "The paper demonstrates good reproducibility potential with detailed methodology description and experimental validation. "
        elif score >= 0.4:
            reproducibility = "The work shows moderate reproducibility with some methodological details provided. "
        else:
            reproducibility = "Reproducibility may be challenging due to limited methodological details in the abstract. "

        reproducibility += "For full reproducibility assessment, access to the complete paper, code, and datasets would be required. "
        reproducibility += f"Based on available information, the reproducibility score is {score:.2f}/1.0."

        return reproducibility

    def _generate_additional_context(self, paper: Dict[str, Any]) -> str:
        """Generate additional context to meet word count requirements."""
        title = paper.get('title', '')
        venue = paper.get('venue', '')
        year = paper.get('year', 0)

        context = f"This research, titled '{title}', represents a valuable contribution to the PHM literature. "
        context += f"The publication in {venue} ({year}) places it within the context of high-quality research venues in the field. "
        context += "The work addresses fundamental challenges in prognostics and health management, "
        context += "including the need for accurate fault detection, reliable health assessment, and effective predictive maintenance strategies. "
        context += "Such research is essential for advancing the state-of-the-art in industrial monitoring and maintenance optimization."

        return context


if __name__ == "__main__":
    # Test the agent
    config = {
        'output_preferences': {
            'summary_length': 'medium',
            'include_reproducibility': True
        }
    }
    
    agent = ContentAnalysisAgent(config)
    
    test_paper = {
        'title': 'Deep Learning for Bearing Fault Diagnosis',
        'abstract': 'This paper proposes a deep learning approach for bearing fault diagnosis in rotating machinery. The method uses convolutional neural networks to analyze vibration signals and classify different fault types. Experimental results show 95% accuracy on a benchmark dataset.',
        'keywords': ['deep learning', 'fault diagnosis', 'bearing', 'CNN'],
        'venue': 'IEEE Transactions on Industrial Electronics',
        'year': 2023,
        'citation_count': 25
    }
    
    result = agent.run([test_paper])
    print("Analysis completed successfully")
