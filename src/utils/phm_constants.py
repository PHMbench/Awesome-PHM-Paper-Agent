"""
PHM Constants - Centralized constants for Prognostics and Health Management system.

This module consolidates all PHM-related constants that were previously duplicated
across multiple files in the enhanced APPA system.

Created during redundancy removal refactoring - 2025-08-23
"""

from typing import Dict, List, Set, Any
from enum import Enum

# PHM Core Concepts and Keywords
PHM_CONCEPTS = {
    'prognostics': {
        'keywords': [
            'prognostics', 'prognosis', 'remaining useful life', 'rul', 'life prediction',
            'degradation modeling', 'failure prediction', 'time to failure', 'ttf',
            'health prognosis', 'predictive maintenance', 'lifetime estimation'
        ],
        'weight': 0.4
    },
    'health_management': {
        'keywords': [
            'health management', 'condition monitoring', 'health assessment',
            'health state', 'system health', 'asset management', 'maintenance optimization',
            'health indicator', 'condition based maintenance', 'cbm'
        ],
        'weight': 0.3
    },
    'fault_diagnosis': {
        'keywords': [
            'fault diagnosis', 'fault detection', 'anomaly detection', 'defect detection',
            'failure diagnosis', 'condition diagnosis', 'diagnostic', 'fault identification',
            'failure mode', 'root cause analysis', 'troubleshooting'
        ],
        'weight': 0.25
    },
    'reliability': {
        'keywords': [
            'reliability', 'reliability analysis', 'reliability assessment', 'mtbf',
            'mean time between failures', 'availability', 'maintainability',
            'failure rate', 'hazard rate', 'survival analysis'
        ],
        'weight': 0.05
    }
}

# Methodology Classifications
METHODOLOGY_KEYWORDS = {
    'deep_learning': {
        'keywords': [
            'deep learning', 'neural network', 'cnn', 'convolutional neural network',
            'lstm', 'long short-term memory', 'rnn', 'recurrent neural network',
            'autoencoder', 'gan', 'generative adversarial network', 'transformer',
            'attention mechanism', 'deep neural network', 'dnn'
        ],
        'category': 'Deep Learning'
    },
    'machine_learning': {
        'keywords': [
            'machine learning', 'support vector machine', 'svm', 'random forest',
            'decision tree', 'k-means', 'clustering', 'classification',
            'regression', 'ensemble learning', 'boosting', 'bagging',
            'artificial intelligence', 'ai', 'pattern recognition'
        ],
        'category': 'Machine Learning'
    },
    'signal_processing': {
        'keywords': [
            'signal processing', 'fourier transform', 'fft', 'wavelet', 'stft',
            'time-frequency analysis', 'spectral analysis', 'frequency domain',
            'filtering', 'digital signal processing', 'dsp', 'envelope analysis',
            'hilbert transform', 'empirical mode decomposition', 'emd'
        ],
        'category': 'Signal Processing'
    },
    'statistical_methods': {
        'keywords': [
            'statistical', 'statistics', 'bayesian', 'monte carlo', 'hypothesis test',
            'confidence interval', 'regression analysis', 'time series',
            'stochastic process', 'markov', 'gaussian process', 'statistical inference'
        ],
        'category': 'Statistical Methods'
    },
    'physics_based': {
        'keywords': [
            'physics based', 'physical model', 'finite element', 'fem',
            'computational fluid dynamics', 'cfd', 'thermodynamics',
            'mechanics', 'structural analysis', 'mathematical model',
            'first principles', 'analytical model'
        ],
        'category': 'Physics-Based Modeling'
    },
    'hybrid_methods': {
        'keywords': [
            'hybrid', 'fusion', 'multi-modal', 'ensemble', 'combination',
            'integrated approach', 'data-physics fusion', 'grey box model',
            'semi-supervised', 'transfer learning', 'multi-source'
        ],
        'category': 'Hybrid Methods'
    }
}

# Application Domains
APPLICATION_DOMAINS = {
    'rotating_machinery': {
        'keywords': [
            'bearing', 'gear', 'rotor', 'shaft', 'motor', 'pump', 'compressor',
            'turbine', 'fan', 'generator', 'spindle', 'rotating machinery',
            'rotating equipment', 'mechanical drive', 'drivetrain'
        ],
        'domain': 'Rotating Machinery'
    },
    'aerospace': {
        'keywords': [
            'aircraft', 'airplane', 'helicopter', 'engine', 'turbofan',
            'aerospace', 'aviation', 'flight', 'propulsion', 'jet engine',
            'gas turbine', 'avionics', 'structural health monitoring'
        ],
        'domain': 'Aerospace'
    },
    'automotive': {
        'keywords': [
            'automotive', 'vehicle', 'car', 'truck', 'engine', 'transmission',
            'brake', 'suspension', 'tire', 'battery', 'electric vehicle',
            'hybrid vehicle', 'powertrain', 'chassis'
        ],
        'domain': 'Automotive'
    },
    'energy': {
        'keywords': [
            'wind turbine', 'solar panel', 'power plant', 'generator',
            'transformer', 'power grid', 'energy storage', 'battery',
            'fuel cell', 'nuclear', 'hydroelectric', 'renewable energy'
        ],
        'domain': 'Energy Systems'
    },
    'industrial_process': {
        'keywords': [
            'manufacturing', 'production', 'industrial', 'process',
            'chemical plant', 'refinery', 'pipeline', 'valve',
            'heat exchanger', 'boiler', 'reactor', 'distillation'
        ],
        'domain': 'Industrial Process'
    },
    'marine': {
        'keywords': [
            'ship', 'marine', 'offshore', 'naval', 'maritime',
            'propeller', 'hull', 'engine room', 'vessel',
            'underwater', 'subsea', 'ocean engineering'
        ],
        'domain': 'Marine Systems'
    },
    'railway': {
        'keywords': [
            'railway', 'train', 'rail', 'locomotive', 'wagon',
            'track', 'wheel', 'axle', 'pantograph', 'traction'
        ],
        'domain': 'Railway Systems'
    },
    'infrastructure': {
        'keywords': [
            'bridge', 'building', 'structure', 'civil engineering',
            'infrastructure', 'concrete', 'steel', 'foundation',
            'dam', 'tunnel', 'road', 'pavement'
        ],
        'domain': 'Infrastructure'
    }
}

# Research Areas for Enhanced Filtering
RESEARCH_AREAS = {
    'fault_diagnosis_and_detection',
    'prognostics_and_health_management',
    'condition_monitoring',
    'predictive_maintenance',
    'reliability_engineering',
    'signal_processing_for_phm',
    'machine_learning_for_phm',
    'deep_learning_applications',
    'digital_twin_technology',
    'iot_and_sensor_networks'
}

# Venue Quality Assessment
VENUE_QUALITY_MAPPING = {
    # Top-tier journals and conferences
    'mechanical systems and signal processing': {'impact_factor': 8.4, 'quartile': 'Q1', 'category': 'journal'},
    'ieee transactions on industrial electronics': {'impact_factor': 8.2, 'quartile': 'Q1', 'category': 'journal'},
    'reliability engineering & system safety': {'impact_factor': 7.6, 'quartile': 'Q1', 'category': 'journal'},
    'ieee transactions on reliability': {'impact_factor': 5.9, 'quartile': 'Q1', 'category': 'journal'},
    'expert systems with applications': {'impact_factor': 8.5, 'quartile': 'Q1', 'category': 'journal'},
    'engineering applications of artificial intelligence': {'impact_factor': 8.0, 'quartile': 'Q1', 'category': 'journal'},
    'ieee access': {'impact_factor': 3.9, 'quartile': 'Q2', 'category': 'journal'},
    'sensors': {'impact_factor': 3.8, 'quartile': 'Q2', 'category': 'journal'},
    'applied soft computing': {'impact_factor': 8.7, 'quartile': 'Q1', 'category': 'journal'},
    'knowledge-based systems': {'impact_factor': 8.8, 'quartile': 'Q1', 'category': 'journal'},
    
    # Conferences
    'phm': {'score': 0.9, 'category': 'conference'},
    'prognostics and health management': {'score': 0.9, 'category': 'conference'},
    'annual conference of the prognostics and health management society': {'score': 0.9, 'category': 'conference'},
    'ieee conference on prognostics and health management': {'score': 0.85, 'category': 'conference'},
    'international conference on condition monitoring and machinery failure prevention technologies': {'score': 0.8, 'category': 'conference'},
    'surveillance, vibrations, shock and noise': {'score': 0.75, 'category': 'conference'},
    'case western reserve university bearing data center': {'score': 0.7, 'category': 'dataset'},
    
    # Additional high-impact venues
    'journal of manufacturing systems': {'impact_factor': 9.3, 'quartile': 'Q1', 'category': 'journal'},
    'computers & industrial engineering': {'impact_factor': 7.9, 'quartile': 'Q1', 'category': 'journal'},
    'isa transactions': {'impact_factor': 7.3, 'quartile': 'Q1', 'category': 'journal'},
    'measurement': {'impact_factor': 5.6, 'quartile': 'Q1', 'category': 'journal'},
    'ieee transactions on instrumentation and measurement': {'impact_factor': 5.6, 'quartile': 'Q1', 'category': 'journal'},
    'neurocomputing': {'impact_factor': 6.0, 'quartile': 'Q1', 'category': 'journal'},
    'information sciences': {'impact_factor': 8.1, 'quartile': 'Q1', 'category': 'journal'},
    'pattern recognition': {'impact_factor': 8.0, 'quartile': 'Q1', 'category': 'journal'}
}

# Relevance Score Thresholds
RELEVANCE_THRESHOLDS = {
    'high': 0.7,
    'medium': 0.5,
    'low': 0.3,
    'minimum': 0.2
}

# Citation Impact Categories
CITATION_IMPACT_CATEGORIES = {
    'high_impact': 50,      # 50+ citations considered high impact
    'medium_impact': 20,    # 20-49 citations considered medium impact
    'emerging': 5,          # 5-19 citations considered emerging
    'new': 0               # 0-4 citations considered new
}

# Time Decay Factors for Relevance Scoring
TIME_DECAY_FACTORS = {
    'current_year': 1.0,
    'last_year': 0.9,
    'two_years': 0.8,
    'three_years': 0.7,
    'older': 0.6
}

# MCP Academic Tool Configuration
MCP_CONFIG = {
    'timeout_seconds': 30,
    'max_results_per_query': 100,
    'supported_databases': ['arxiv', 'pubmed', 'google_scholar', 'openalex'],
    'retry_attempts': 3,
    'rate_limit_delay': 1.0
}

# Search Query Enhancement Templates
SEARCH_TEMPLATES = {
    'basic_phm': 'prognostics OR "health management" OR "condition monitoring" OR "predictive maintenance"',
    'fault_diagnosis': '"fault diagnosis" OR "fault detection" OR "anomaly detection" OR "failure diagnosis"',
    'deep_learning_phm': '("deep learning" OR "neural network") AND (prognostics OR "health management" OR "fault diagnosis")',
    'rotating_machinery': '(bearing OR gear OR rotor OR motor) AND ("fault diagnosis" OR prognostics OR "condition monitoring")',
    'recent_advances': 'prognostics AND ("deep learning" OR "machine learning" OR "artificial intelligence")'
}

# Output Format Templates
OUTPUT_TEMPLATES = {
    'paper_summary': {
        'title': str,
        'authors': List[str],
        'year': int,
        'venue': str,
        'abstract': str,
        'keywords': List[str],
        'phm_relevance_score': float,
        'methodology_classification': List[str],
        'application_domains': List[str],
        'citation_count': int,
        'doi': str
    }
}

# Error Messages
ERROR_MESSAGES = {
    'mcp_connection_failed': 'Failed to connect to MCP academic research tools',
    'invalid_date_range': 'Invalid date range format. Expected YYYY-YYYY',
    'no_results_found': 'No papers found matching the search criteria',
    'relevance_threshold_error': 'Relevance score threshold must be between 0.0 and 1.0',
    'unsupported_database': 'Requested database is not supported by MCP tools'
}

# Default Configuration Values
DEFAULT_CONFIG = {
    'max_results': 100,
    'min_relevance_score': 0.2,
    'include_preprints': True,
    'enable_citation_enhancement': True,
    'enable_pdf_download': False,
    'output_format': 'detailed'
}