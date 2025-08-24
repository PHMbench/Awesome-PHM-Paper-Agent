"""
Knowledge Organizer for APPA System

This module organizes real PHM papers into a GitHub-friendly knowledge base
with bidirectional linking, categorization, and awesome-list structure.

Features:
- Category-based organization (deep learning, fault diagnosis, etc.)
- Bidirectional linking between papers, authors, and topics
- GitHub Awesome project structure
- Multi-dimensional indexing (by year, venue, author, citations)
- README generation for each category and subcategory
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from collections import defaultdict

from .logging_config import get_logger
from .paper_utils import create_paper_fingerprint


class AwesomePHMKnowledgeOrganizer:
    """
    Organizes real PHM papers into an Awesome GitHub project structure
    with comprehensive categorization and bidirectional linking.
    """
    
    def __init__(self, base_path: str, config: Dict[str, Any] = None):
        self.base_path = Path(base_path)
        self.config = config or {}
        self.logger = get_logger(__name__)
        
        # PHM category definitions
        self.categories = {
            'deep-learning': {
                'title': '🧠 Deep Learning in PHM',
                'description': 'Neural networks, CNNs, LSTMs, and Transformers for prognostics and health management',
                'keywords': ['deep learning', 'neural network', 'CNN', 'LSTM', 'transformer', 'autoencoder'],
                'subcategories': {
                    'cnn-fault-diagnosis': 'CNN-based Fault Diagnosis',
                    'lstm-rul-prediction': 'LSTM for RUL Prediction',
                    'transformer-phm': 'Transformer Applications',
                    'gan-data-augmentation': 'GAN for Data Augmentation'
                }
            },
            'fault-diagnosis': {
                'title': '🔍 Fault Diagnosis & Detection',
                'description': 'Methods and techniques for identifying and classifying equipment faults',
                'keywords': ['fault diagnosis', 'fault detection', 'anomaly detection', 'classification'],
                'subcategories': {
                    'bearing-faults': 'Bearing Fault Diagnosis',
                    'gearbox-diagnosis': 'Gearbox Fault Detection',
                    'motor-faults': 'Motor Fault Diagnosis',
                    'multi-fault-diagnosis': 'Multi-fault Systems'
                }
            },
            'rul-prediction': {
                'title': '📈 Remaining Useful Life (RUL) Prediction',
                'description': 'Prognostic methods for predicting component and system remaining useful life',
                'keywords': ['RUL', 'remaining useful life', 'prognostics', 'degradation', 'time to failure'],
                'subcategories': {
                    'model-based-rul': 'Model-based RUL Methods',
                    'data-driven-rul': 'Data-driven RUL Prediction',
                    'hybrid-rul': 'Hybrid RUL Approaches',
                    'uncertainty-quantification': 'Uncertainty in RUL'
                }
            },
            'digital-twin': {
                'title': '👯 Digital Twin for PHM',
                'description': 'Digital twin technologies for predictive maintenance and health management',
                'keywords': ['digital twin', 'cyber-physical system', 'virtual sensor', 'simulation'],
                'subcategories': {
                    'dt-frameworks': 'Digital Twin Frameworks',
                    'real-time-dt': 'Real-time Digital Twins',
                    'dt-maintenance': 'DT for Maintenance',
                    'iot-integration': 'IoT and Edge Computing'
                }
            },
            'transfer-learning': {
                'title': '🔄 Transfer Learning & Domain Adaptation',
                'description': 'Cross-domain knowledge transfer for PHM applications',
                'keywords': ['transfer learning', 'domain adaptation', 'few-shot learning', 'meta-learning'],
                'subcategories': {
                    'cross-machine-transfer': 'Cross-machine Transfer',
                    'cross-condition-adaptation': 'Cross-condition Adaptation',
                    'few-shot-diagnosis': 'Few-shot Fault Diagnosis',
                    'unsupervised-adaptation': 'Unsupervised Domain Adaptation'
                }
            },
            'signal-processing': {
                'title': '📊 Signal Processing & Feature Extraction',
                'description': 'Signal analysis techniques for condition monitoring and PHM',
                'keywords': ['signal processing', 'feature extraction', 'spectral analysis', 'time-frequency'],
                'subcategories': {
                    'vibration-analysis': 'Vibration Signal Analysis',
                    'acoustic-monitoring': 'Acoustic Emission Analysis',
                    'thermal-monitoring': 'Thermal Analysis',
                    'multi-sensor-fusion': 'Multi-sensor Data Fusion'
                }
            }
        }
        
        # Initialize directory structure
        self._initialize_directory_structure()
        
        self.logger.info("Awesome PHM Knowledge Organizer initialized")
    
    def organize_papers(self, papers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Organize papers into the Awesome PHM structure.
        
        Args:
            papers: List of paper metadata dictionaries
            
        Returns:
            Organization summary and statistics
        """
        self.logger.info(f"Organizing {len(papers)} papers into Awesome PHM structure")
        
        # Step 1: Categorize papers
        categorized_papers = self._categorize_papers(papers)
        
        # Step 2: Generate paper detail pages
        paper_files = self._generate_paper_pages(papers)
        
        # Step 3: Generate category README files
        category_files = self._generate_category_readmes(categorized_papers)
        
        # Step 4: Generate indexes
        index_files = self._generate_indexes(papers)
        
        # Step 5: Generate main README
        main_readme = self._generate_main_readme(papers, categorized_papers)
        
        # Step 6: Build bidirectional links
        self._build_bidirectional_links(papers, categorized_papers)
        
        # Step 7: Generate additional resources
        resource_files = self._generate_resources(papers)
        
        summary = {
            'total_papers': len(papers),
            'categories': len(categorized_papers),
            'paper_files_created': len(paper_files),
            'category_files_created': len(category_files),
            'index_files_created': len(index_files),
            'resource_files_created': len(resource_files),
            'main_readme_created': bool(main_readme),
            'organization_date': datetime.now().isoformat(),
            'base_path': str(self.base_path)
        }
        
        self.logger.info(f"Organization complete: {summary}")
        return summary
    
    def _initialize_directory_structure(self):
        """Initialize the Awesome PHM directory structure."""
        
        directories = [
            'categories',
            'by-year',
            'by-venue', 
            'by-author',
            'by-citations',
            'papers',
            'resources',
            'assets/images',
            'scripts',
            '.github/workflows'
        ]
        
        # Create category subdirectories
        for category in self.categories:
            directories.append(f'categories/{category}')
            directories.append(f'categories/{category}/papers')
            
            # Create subcategory directories
            for subcat in self.categories[category].get('subcategories', {}):
                directories.append(f'categories/{category}/{subcat}')
        
        # Create all directories
        for dir_path in directories:
            full_path = self.base_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Created {len(directories)} directories")
    
    def _categorize_papers(self, papers: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize papers based on content analysis."""
        
        categorized = defaultdict(list)
        
        for paper in papers:
            # Get paper categories from tags or analyze content
            paper_categories = self._analyze_paper_categories(paper)
            
            # Assign to primary category
            primary_category = paper_categories[0] if paper_categories else 'uncategorized'
            categorized[primary_category].append(paper)
            
            # Store all categories for cross-referencing
            paper['categories'] = paper_categories
            paper['primary_category'] = primary_category
        
        # Sort papers within each category by quality score
        for category in categorized:
            categorized[category].sort(
                key=lambda p: p.get('final_score', 0), 
                reverse=True
            )
        
        return dict(categorized)
    
    def _analyze_paper_categories(self, paper: Dict[str, Any]) -> List[str]:
        """Analyze paper content to determine categories."""
        
        categories = []
        
        # Get paper text for analysis
        text_content = (
            paper.get('title', '') + ' ' +
            paper.get('abstract', '') + ' ' +
            ' '.join(paper.get('keywords', []))
        ).lower()
        
        # Check against each category
        for category_id, category_info in self.categories.items():
            score = 0
            
            # Check keywords
            for keyword in category_info['keywords']:
                if keyword.lower() in text_content:
                    score += 1
            
            # Check existing tags
            paper_tags = paper.get('search_tags', [])
            for tag in paper_tags:
                if any(kw in tag for kw in category_info['keywords']):
                    score += 0.5
            
            # Add to categories if score threshold met
            if score >= 1.0:  # At least 1 keyword match
                categories.append(category_id)
        
        # Fallback to most likely category if none found
        if not categories:
            categories = ['fault-diagnosis']  # Default category
        
        return categories
    
    def _generate_paper_pages(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Generate individual paper detail pages."""
        
        created_files = []
        
        for paper in papers:
            # Create paper directory name
            paper_dir_name = self._create_paper_directory_name(paper)
            paper_dir = self.base_path / 'papers' / paper_dir_name
            paper_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate paper README
            paper_readme_path = paper_dir / 'README.md'
            paper_readme_content = self._generate_paper_readme(paper)
            
            with open(paper_readme_path, 'w', encoding='utf-8') as f:
                f.write(paper_readme_content)
            
            created_files.append(str(paper_readme_path))
            
            # Generate BibTeX file if DOI available
            if paper.get('doi'):
                bibtex_path = paper_dir / 'paper.bib'
                bibtex_content = self._generate_bibtex(paper)
                
                with open(bibtex_path, 'w', encoding='utf-8') as f:
                    f.write(bibtex_content)
                
                created_files.append(str(bibtex_path))
        
        return created_files
    
    def _create_paper_directory_name(self, paper: Dict[str, Any]) -> str:
        """Create standardized paper directory name."""
        
        year = paper.get('year', 'unknown')
        
        # Get first author surname
        authors = paper.get('authors', [])
        first_author = authors[0] if authors else 'Unknown'
        author_surname = first_author.split()[-1] if ' ' in first_author else first_author
        
        # Clean title for directory name
        title = paper.get('title', 'Unknown Title')
        title_words = re.findall(r'\b\w+\b', title)[:4]  # First 4 words
        title_clean = ''.join(word.capitalize() for word in title_words)
        
        # Create directory name
        dir_name = f"{year}-{author_surname}-{title_clean}"
        
        # Clean and truncate
        dir_name = re.sub(r'[^\w\-_.]', '', dir_name)
        return dir_name[:50]  # Limit length
    
    def _generate_paper_readme(self, paper: Dict[str, Any]) -> str:
        """Generate README content for individual paper."""
        
        # Extract paper information
        title = paper.get('title', 'Unknown Title')
        authors = paper.get('authors', [])
        year = paper.get('year', 'Unknown')
        venue = paper.get('venue', 'Unknown Venue')
        doi = paper.get('doi', '')
        abstract = paper.get('abstract', 'No abstract available')
        keywords = paper.get('keywords', [])
        categories = paper.get('categories', [])
        
        # Build author links
        author_links = []
        for author in authors[:5]:  # Limit to first 5 authors
            author_slug = re.sub(r'[^\w\-_.]', '', author.lower().replace(' ', '-'))
            author_links.append(f"[{author}](../../by-author/{author_slug}.md)")
        
        # Build category links
        category_links = []
        for cat in categories:
            if cat in self.categories:
                category_links.append(f"[{self.categories[cat]['title']}](../../categories/{cat}/README.md)")
        
        # Generate content
        content = f"""# {title}

## 📝 Paper Information

- **Authors**: {', '.join(author_links)}
- **Year**: {year}
- **Venue**: {venue}
- **Categories**: {', '.join(category_links) if category_links else 'Uncategorized'}

{'- **DOI**: [' + doi + '](https://doi.org/' + doi + ')' if doi else ''}

## 📄 Abstract

{abstract}

## 🏷️ Keywords

{', '.join(f'`{kw}`' for kw in keywords) if keywords else 'No keywords available'}

## 📊 Metadata

- **Publication Type**: {paper.get('paper_type', 'Unknown')}
- **Citation Count**: {paper.get('citation_count', 0)}
- **PHM Relevance Score**: {paper.get('phm_relevance_score', 0):.2f}
- **Quality Score**: {paper.get('quality_score', 0):.2f}

## 🔗 Related Papers

<!-- This section will be populated by the bidirectional linking system -->

## 📚 Citation

```bibtex
{self._generate_bibtex_entry(paper)}
```

## 🏠 Navigation

- [🏠 Main Index](../../README.md)
- [📚 All Papers](../../papers/README.md)
- [📅 Papers by Year](../../by-year/{year}.md)
{'- [🏢 Papers by Venue](../../by-venue/' + self._slugify(venue) + '.md)' if venue != 'Unknown Venue' else ''}

---

*Page generated on {datetime.now().strftime('%Y-%m-%d')} by APPA Knowledge Organizer*
"""
        
        return content
    
    def _generate_category_readmes(self, categorized_papers: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate README files for each category."""
        
        created_files = []
        
        for category_id, papers in categorized_papers.items():
            if category_id not in self.categories:
                continue  # Skip unknown categories
            
            category_info = self.categories[category_id]
            category_dir = self.base_path / 'categories' / category_id
            readme_path = category_dir / 'README.md'
            
            # Generate category README content
            readme_content = self._generate_category_readme_content(category_id, category_info, papers)
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            created_files.append(str(readme_path))
        
        return created_files
    
    def _generate_category_readme_content(self, 
                                        category_id: str, 
                                        category_info: Dict[str, Any], 
                                        papers: List[Dict[str, Any]]) -> str:
        """Generate README content for a specific category."""
        
        title = category_info['title']
        description = category_info['description']
        subcategories = category_info.get('subcategories', {})
        
        # Statistics
        total_papers = len(papers)
        years_covered = set(p.get('year') for p in papers if p.get('year'))
        year_range = f"{min(years_covered)}-{max(years_covered)}" if years_covered else "Unknown"
        
        # Top papers by quality score
        top_papers = sorted(papers, key=lambda p: p.get('final_score', 0), reverse=True)[:10]
        
        # Papers by year
        papers_by_year = defaultdict(list)
        for paper in papers:
            year = paper.get('year', 'Unknown')
            papers_by_year[year].append(paper)
        
        # Generate content
        content = f"""# {title}

{description}

## 📊 Category Statistics

- **Total Papers**: {total_papers}
- **Year Range**: {year_range}
- **Average Quality Score**: {sum(p.get('quality_score', 0) for p in papers) / total_papers:.2f if papers else 0:.2f}
- **High Impact Papers** (>50 citations): {len([p for p in papers if p.get('citation_count', 0) > 50])}

## 📑 Paper Categories

{self._format_subcategories(subcategories)}

## 🏆 Featured Papers

{self._format_paper_list(top_papers[:5], show_scores=True)}

## 📅 Papers by Year

{self._format_papers_by_year(papers_by_year)}

## 🔍 All Papers

{self._format_paper_list(papers)}

## 🔗 Related Categories

{self._format_related_categories(category_id)}

## 🏠 Navigation

- [🏠 Main Index](../../README.md)
- [📚 All Papers](../../papers/README.md)
- [📊 All Categories](../README.md)

---

*Last updated: {datetime.now().strftime('%Y-%m-%d')} | Papers: {total_papers}*
"""
        
        return content
    
    def _format_subcategories(self, subcategories: Dict[str, str]) -> str:
        """Format subcategories list."""
        if not subcategories:
            return "*No subcategories defined*"
        
        lines = []
        for subcat_id, subcat_title in subcategories.items():
            lines.append(f"- **[{subcat_title}]({subcat_id}/README.md)**")
        
        return '\n'.join(lines)
    
    def _format_paper_list(self, papers: List[Dict[str, Any]], show_scores: bool = False) -> str:
        """Format a list of papers for display."""
        if not papers:
            return "*No papers in this category*"
        
        lines = []
        for i, paper in enumerate(papers, 1):
            title = paper.get('title', 'Unknown Title')
            authors = paper.get('authors', [])
            year = paper.get('year', 'Unknown')
            venue = paper.get('venue', 'Unknown')
            citations = paper.get('citation_count', 0)
            
            # Create paper link
            paper_dir = self._create_paper_directory_name(paper)
            paper_link = f"[{title}](../../papers/{paper_dir}/README.md)"
            
            # Format authors (first 3)
            author_str = ', '.join(authors[:3])
            if len(authors) > 3:
                author_str += ' et al.'
            
            # Build line
            line = f"{i}. **{paper_link}**"
            line += f"\n   - *{author_str}* ({year})"
            line += f"\n   - Published in: {venue}"
            line += f"\n   - Citations: {citations}"
            
            if show_scores:
                quality_score = paper.get('quality_score', 0)
                relevance_score = paper.get('phm_relevance_score', 0)
                line += f"\n   - Quality Score: {quality_score:.2f} | PHM Relevance: {relevance_score:.2f}"
            
            lines.append(line)
        
        return '\n\n'.join(lines)
    
    def _format_papers_by_year(self, papers_by_year: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format papers organized by year."""
        if not papers_by_year:
            return "*No papers available*"
        
        lines = []
        for year in sorted(papers_by_year.keys(), reverse=True):
            year_papers = papers_by_year[year]
            lines.append(f"### {year} ({len(year_papers)} papers)")
            lines.append("")
            
            for paper in year_papers[:5]:  # Show top 5 per year
                title = paper.get('title', 'Unknown Title')
                paper_dir = self._create_paper_directory_name(paper)
                paper_link = f"[{title}](../../papers/{paper_dir}/README.md)"
                
                authors = paper.get('authors', [])
                author_str = authors[0] if authors else 'Unknown Author'
                if len(authors) > 1:
                    author_str += ' et al.'
                
                lines.append(f"- **{paper_link}** - *{author_str}*")
            
            if len(year_papers) > 5:
                lines.append(f"- ... and {len(year_papers) - 5} more papers")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_related_categories(self, current_category: str) -> str:
        """Format related categories."""
        related = []
        
        # Simple relatedness based on keyword overlap
        current_keywords = set(self.categories[current_category]['keywords'])
        
        for cat_id, cat_info in self.categories.items():
            if cat_id == current_category:
                continue
            
            cat_keywords = set(cat_info['keywords'])
            overlap = len(current_keywords & cat_keywords)
            
            if overlap > 0:
                related.append((cat_id, cat_info['title'], overlap))
        
        # Sort by overlap
        related.sort(key=lambda x: x[2], reverse=True)
        
        if not related:
            return "*No directly related categories*"
        
        lines = []
        for cat_id, title, overlap in related[:3]:  # Top 3
            lines.append(f"- [{title}](../{cat_id}/README.md)")
        
        return '\n'.join(lines)
    
    def _generate_indexes(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Generate various index files."""
        created_files = []
        
        # By year index
        year_index = self._generate_year_index(papers)
        year_file = self.base_path / 'by-year' / 'README.md'
        with open(year_file, 'w', encoding='utf-8') as f:
            f.write(year_index)
        created_files.append(str(year_file))
        
        # By venue index
        venue_index = self._generate_venue_index(papers)
        venue_file = self.base_path / 'by-venue' / 'README.md'
        with open(venue_file, 'w', encoding='utf-8') as f:
            f.write(venue_index)
        created_files.append(str(venue_file))
        
        # By citations index
        citation_index = self._generate_citation_index(papers)
        citation_file = self.base_path / 'by-citations' / 'README.md'
        with open(citation_file, 'w', encoding='utf-8') as f:
            f.write(citation_index)
        created_files.append(str(citation_file))
        
        return created_files
    
    def _generate_year_index(self, papers: List[Dict[str, Any]]) -> str:
        """Generate index organized by publication year."""
        
        papers_by_year = defaultdict(list)
        for paper in papers:
            year = paper.get('year', 'Unknown')
            papers_by_year[year].append(paper)
        
        # Sort each year's papers by quality score
        for year in papers_by_year:
            papers_by_year[year].sort(key=lambda p: p.get('final_score', 0), reverse=True)
        
        content = f"""# 📅 Papers by Year

Index of all PHM papers organized by publication year.

## 📊 Year Statistics

- **Total Papers**: {len(papers)}
- **Year Range**: {min(papers_by_year.keys())}-{max(papers_by_year.keys()) if papers_by_year else 'Unknown'}
- **Most Productive Year**: {max(papers_by_year.keys(), key=lambda y: len(papers_by_year[y])) if papers_by_year else 'Unknown'} ({max(len(papers_by_year[y]) for y in papers_by_year) if papers_by_year else 0} papers)

## 📚 Papers by Year

"""
        
        for year in sorted(papers_by_year.keys(), reverse=True):
            year_papers = papers_by_year[year]
            content += f"\n### {year} ({len(year_papers)} papers)\n\n"
            content += self._format_paper_list(year_papers)
            content += "\n"
        
        content += f"""

## 🏠 Navigation

- [🏠 Main Index](../README.md)
- [📊 All Categories](../categories/README.md)
- [🏢 By Venue](../by-venue/README.md)
- [📈 By Citations](../by-citations/README.md)

---

*Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        return content
    
    def _generate_venue_index(self, papers: List[Dict[str, Any]]) -> str:
        """Generate index organized by publication venue."""
        
        papers_by_venue = defaultdict(list)
        for paper in papers:
            venue = paper.get('venue', 'Unknown Venue')
            papers_by_venue[venue].append(paper)
        
        content = f"""# 🏢 Papers by Venue

Index of all PHM papers organized by publication venue (journals and conferences).

## 📊 Venue Statistics

- **Total Venues**: {len(papers_by_venue)}
- **Total Papers**: {len(papers)}
- **Most Published Venue**: {max(papers_by_venue.keys(), key=lambda v: len(papers_by_venue[v])) if papers_by_venue else 'Unknown'}

## 📚 Papers by Venue

"""
        
        # Sort venues by number of papers
        sorted_venues = sorted(papers_by_venue.keys(), key=lambda v: len(papers_by_venue[v]), reverse=True)
        
        for venue in sorted_venues:
            venue_papers = papers_by_venue[venue]
            venue_slug = self._slugify(venue)
            
            content += f"\n### {venue} ({len(venue_papers)} papers)\n\n"
            
            # Show top 5 papers per venue
            for paper in venue_papers[:5]:
                title = paper.get('title', 'Unknown Title')
                paper_dir = self._create_paper_directory_name(paper)
                paper_link = f"[{title}](../papers/{paper_dir}/README.md)"
                
                authors = paper.get('authors', [])
                author_str = authors[0] if authors else 'Unknown'
                year = paper.get('year', 'Unknown')
                
                content += f"- **{paper_link}** - *{author_str}* ({year})\n"
            
            if len(venue_papers) > 5:
                content += f"- ... and {len(venue_papers) - 5} more papers\n"
            
            content += "\n"
        
        content += f"""

## 🏠 Navigation

- [🏠 Main Index](../README.md)
- [📊 All Categories](../categories/README.md)
- [📅 By Year](../by-year/README.md)
- [📈 By Citations](../by-citations/README.md)

---

*Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        return content
    
    def _generate_citation_index(self, papers: List[Dict[str, Any]]) -> str:
        """Generate index organized by citation count."""
        
        # Sort papers by citation count
        sorted_papers = sorted(papers, key=lambda p: p.get('citation_count', 0), reverse=True)
        
        # Group by citation ranges
        high_impact = [p for p in sorted_papers if p.get('citation_count', 0) >= 100]
        medium_impact = [p for p in sorted_papers if 20 <= p.get('citation_count', 0) < 100]
        emerging = [p for p in sorted_papers if 5 <= p.get('citation_count', 0) < 20]
        recent = [p for p in sorted_papers if p.get('citation_count', 0) < 5]
        
        content = f"""# 📈 Papers by Citations

Index of all PHM papers organized by citation impact.

## 📊 Citation Statistics

- **Total Papers**: {len(papers)}
- **High Impact** (≥100 citations): {len(high_impact)}
- **Medium Impact** (20-99 citations): {len(medium_impact)}  
- **Emerging Impact** (5-19 citations): {len(emerging)}
- **Recent/Low Impact** (<5 citations): {len(recent)}

## 🏆 High Impact Papers (≥100 citations)

{self._format_paper_list(high_impact, show_scores=True) if high_impact else '*No high impact papers yet*'}

## 📊 Medium Impact Papers (20-99 citations)

{self._format_paper_list(medium_impact[:10]) if medium_impact else '*No medium impact papers yet*'}

## 🌟 Emerging Papers (5-19 citations)

{self._format_paper_list(emerging[:10]) if emerging else '*No emerging papers yet*'}

## 🆕 Recent Papers (<5 citations)

{self._format_paper_list(recent[:10]) if recent else '*No recent papers*'}

## 🏠 Navigation

- [🏠 Main Index](../README.md)
- [📊 All Categories](../categories/README.md)
- [📅 By Year](../by-year/README.md)
- [🏢 By Venue](../by-venue/README.md)

---

*Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""
        
        return content
    
    def _generate_main_readme(self, 
                            papers: List[Dict[str, Any]], 
                            categorized_papers: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate the main README file for the Awesome PHM repository."""
        
        # Calculate statistics
        total_papers = len(papers)
        total_categories = len(categorized_papers)
        years_covered = set(p.get('year') for p in papers if p.get('year'))
        year_range = f"{min(years_covered)}-{max(years_covered)}" if years_covered else "Unknown"
        
        # Top venues
        venue_counts = defaultdict(int)
        for paper in papers:
            venue_counts[paper.get('venue', 'Unknown')] += 1
        top_venues = sorted(venue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Featured papers (top 5 by composite score)
        featured_papers = sorted(papers, key=lambda p: p.get('final_score', 0), reverse=True)[:5]
        
        content = f"""# 🔧 Awesome PHM Papers [![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> A curated list of awesome research papers in **Prognostics and Health Management (PHM)** with real academic data

*Systematically organized collection of high-quality PHM research papers from leading academic databases*

## 📊 Repository Statistics

- **📚 Total Papers**: {total_papers}
- **🏷️ Categories**: {total_categories}
- **📅 Year Coverage**: {year_range}
- **🔄 Last Updated**: {datetime.now().strftime('%Y-%m-%d')}
- **🤖 Data Source**: Real academic databases (ArXiv, IEEE, Google Scholar, PubMed)

## 🎯 What is PHM?

**Prognostics and Health Management (PHM)** is an engineering discipline focused on predicting the future performance of components and systems, enabling proactive maintenance decisions and improving system reliability. This repository collects cutting-edge research in:

- 🔍 **Fault Diagnosis & Detection**
- 📈 **Remaining Useful Life (RUL) Prediction** 
- 🧠 **Machine Learning & AI Applications**
- 👯 **Digital Twin Technologies**
- 📊 **Signal Processing & Analytics**
- 🔄 **Transfer Learning & Domain Adaptation**

## 📚 Paper Categories

{self._format_main_category_list(categorized_papers)}

## 🏆 Featured Papers

{self._format_paper_list(featured_papers, show_scores=True)}

## 🏢 Top Venues

{self._format_venue_list(top_venues)}

## 📖 Browse Papers

### 🗂️ By Organization
- [📊 **By Category**](categories/README.md) - Browse by research area
- [📅 **By Year**](by-year/README.md) - Chronological organization
- [🏢 **By Venue**](by-venue/README.md) - Journal and conference papers
- [👥 **By Author**](by-author/README.md) - Author-centric view
- [📈 **By Citations**](by-citations/README.md) - Impact-ranked papers

### 🔍 Quick Access
- [🆕 **Latest Papers**](by-year/README.md) - Most recent research
- [🏆 **High Impact**](by-citations/README.md) - Highly cited works
- [🌟 **Trending Topics**](categories/README.md) - Hot research areas
- [📱 **All Papers**](papers/README.md) - Complete paper list

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Adding Papers
1. **Real papers only** - No fictitious or generated content
2. **PHM relevance** - Must be related to prognostics and health management
3. **Quality threshold** - Peer-reviewed publications preferred
4. **Complete metadata** - Title, authors, abstract, DOI, etc.

### Automated Updates
This repository uses automated agents to discover and organize new papers:
- 🤖 **academic-researcher** - Searches real academic databases
- 📊 **Quality curation** - Filters papers based on relevance and impact
- 🔗 **Auto-linking** - Maintains bidirectional references
- 📈 **Impact tracking** - Updates citation counts and metrics

## 🛠️ Technical Details

### Data Sources
- [ArXiv](https://arxiv.org/) - Preprints and cutting-edge research
- [IEEE Xplore](https://ieeexplore.ieee.org/) - Engineering publications
- [Google Scholar](https://scholar.google.com/) - Comprehensive academic search
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/) - Biomedical applications
- [Semantic Scholar](https://www.semanticscholar.org/) - AI-powered paper discovery

### Organization System
- **Categorization**: Automatic content-based classification
- **Quality scoring**: Multi-factor relevance and impact assessment
- **Bidirectional linking**: Cross-references between papers, authors, and topics
- **Standardized format**: Consistent metadata and citation formats

## 📄 License

This repository is licensed under [CC BY 4.0](LICENSE) - you are free to use, share, and adapt the content with attribution.

## 📞 Contact & Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/awesome-phm-papers/issues)
- 💡 **Suggestions**: [GitHub Discussions](https://github.com/your-username/awesome-phm-papers/discussions)
- 📧 **Email**: your-email@domain.com

## 🔄 Update Frequency

- **Automated updates**: Weekly via GitHub Actions
- **Manual curation**: Monthly quality reviews
- **Community contributions**: Reviewed within 48 hours

---

⭐ **Star this repository** if you find it useful for your PHM research!

*Generated by [APPA (Awesome PHM Paper Agent)](https://github.com/your-username/appa) - An intelligent academic paper management system*
"""
        
        # Write main README
        main_readme_path = self.base_path / 'README.md'
        with open(main_readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(main_readme_path)
    
    def _format_main_category_list(self, categorized_papers: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format category list for main README."""
        
        lines = []
        
        for category_id, papers in categorized_papers.items():
            if category_id not in self.categories:
                continue
            
            category_info = self.categories[category_id]
            title = category_info['title']
            description = category_info['description']
            
            lines.append(f"### [{title}](categories/{category_id}/README.md)")
            lines.append(f"*{description}*")
            lines.append(f"- **{len(papers)} papers**")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _format_venue_list(self, top_venues: List[tuple]) -> str:
        """Format top venues list."""
        
        lines = []
        
        for venue, count in top_venues:
            venue_slug = self._slugify(venue)
            lines.append(f"- **[{venue}](by-venue/{venue_slug}.md)** ({count} papers)")
        
        return '\n'.join(lines)
    
    def _build_bidirectional_links(self, 
                                 papers: List[Dict[str, Any]], 
                                 categorized_papers: Dict[str, List[Dict[str, Any]]]):
        """Build bidirectional links between papers based on various criteria."""
        
        self.logger.info("Building bidirectional links between papers")
        
        # Build similarity index
        paper_similarities = self._calculate_paper_similarities(papers)
        
        # Update each paper's README with related papers
        for paper in papers:
            paper_dir_name = self._create_paper_directory_name(paper)
            paper_readme_path = self.base_path / 'papers' / paper_dir_name / 'README.md'
            
            if paper_readme_path.exists():
                # Get related papers
                related_papers = self._get_related_papers(paper, papers, paper_similarities)
                
                # Update README with related papers section
                self._update_paper_readme_with_links(paper_readme_path, related_papers)
    
    def _calculate_paper_similarities(self, papers: List[Dict[str, Any]]) -> Dict[str, List[tuple]]:
        """Calculate similarities between papers for bidirectional linking."""
        
        similarities = defaultdict(list)
        
        for i, paper1 in enumerate(papers):
            paper1_id = create_paper_fingerprint(paper1, method='advanced')
            
            for j, paper2 in enumerate(papers[i+1:], i+1):
                paper2_id = create_paper_fingerprint(paper2, method='advanced')
                
                # Calculate similarity score
                similarity = self._calculate_similarity_score(paper1, paper2)
                
                if similarity > 0.3:  # Minimum threshold for relatedness
                    similarities[paper1_id].append((paper2, similarity))
                    similarities[paper2_id].append((paper1, similarity))
        
        # Sort by similarity score
        for paper_id in similarities:
            similarities[paper_id].sort(key=lambda x: x[1], reverse=True)
        
        return similarities
    
    def _calculate_similarity_score(self, paper1: Dict[str, Any], paper2: Dict[str, Any]) -> float:
        """Calculate similarity score between two papers."""
        
        score = 0.0
        
        # Author overlap (weight: 30%)
        authors1 = set(paper1.get('authors', []))
        authors2 = set(paper2.get('authors', []))
        if authors1 and authors2:
            author_jaccard = len(authors1 & authors2) / len(authors1 | authors2)
            score += author_jaccard * 0.3
        
        # Keyword overlap (weight: 25%)
        keywords1 = set(paper1.get('keywords', []))
        keywords2 = set(paper2.get('keywords', []))
        if keywords1 and keywords2:
            keyword_jaccard = len(keywords1 & keywords2) / len(keywords1 | keywords2)
            score += keyword_jaccard * 0.25
        
        # Category overlap (weight: 20%)
        cats1 = set(paper1.get('categories', []))
        cats2 = set(paper2.get('categories', []))
        if cats1 and cats2:
            category_jaccard = len(cats1 & cats2) / len(cats1 | cats2)
            score += category_jaccard * 0.2
        
        # Title similarity (weight: 15%)
        title1 = paper1.get('title', '').lower()
        title2 = paper2.get('title', '').lower()
        if title1 and title2:
            title_words1 = set(re.findall(r'\w+', title1))
            title_words2 = set(re.findall(r'\w+', title2))
            if title_words1 and title_words2:
                title_jaccard = len(title_words1 & title_words2) / len(title_words1 | title_words2)
                score += title_jaccard * 0.15
        
        # Venue similarity (weight: 10%)
        venue1 = paper1.get('venue', '')
        venue2 = paper2.get('venue', '')
        if venue1 == venue2 and venue1 != 'Unknown Venue':
            score += 0.1
        
        return score
    
    def _get_related_papers(self, 
                          paper: Dict[str, Any], 
                          all_papers: List[Dict[str, Any]], 
                          similarities: Dict[str, List[tuple]]) -> List[Dict[str, Any]]:
        """Get related papers for a given paper."""
        
        paper_id = create_paper_fingerprint(paper, method='advanced')
        related = similarities.get(paper_id, [])
        
        # Return top 5 most similar papers
        return [related_paper for related_paper, score in related[:5]]
    
    def _update_paper_readme_with_links(self, readme_path: Path, related_papers: List[Dict[str, Any]]):
        """Update paper README with related papers section."""
        
        if not related_papers:
            return
        
        # Read existing content
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Build related papers section
        related_section = "\n## 🔗 Related Papers\n\n"
        
        for i, related_paper in enumerate(related_papers, 1):
            title = related_paper.get('title', 'Unknown Title')
            authors = related_paper.get('authors', [])
            year = related_paper.get('year', 'Unknown')
            
            # Create link to related paper
            related_dir_name = self._create_paper_directory_name(related_paper)
            related_link = f"[{title}](../{related_dir_name}/README.md)"
            
            # Format authors
            author_str = ', '.join(authors[:2])
            if len(authors) > 2:
                author_str += ' et al.'
            
            related_section += f"{i}. **{related_link}**\n"
            related_section += f"   - *{author_str}* ({year})\n\n"
        
        # Replace or insert related papers section
        if "## 🔗 Related Papers" in content:
            # Replace existing section
            pattern = r"## 🔗 Related Papers.*?(?=## |\Z)"
            content = re.sub(pattern, related_section.strip() + "\n\n", content, flags=re.DOTALL)
        else:
            # Insert before citation section
            citation_index = content.find("## 📚 Citation")
            if citation_index != -1:
                content = content[:citation_index] + related_section + content[citation_index:]
            else:
                # Insert before navigation section
                nav_index = content.find("## 🏠 Navigation")
                if nav_index != -1:
                    content = content[:nav_index] + related_section + content[nav_index:]
        
        # Write updated content
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _generate_resources(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Generate additional resource files."""
        created_files = []
        
        # Generate CONTRIBUTING.md
        contributing_content = self._generate_contributing_guide()
        contributing_path = self.base_path / 'CONTRIBUTING.md'
        with open(contributing_path, 'w', encoding='utf-8') as f:
            f.write(contributing_content)
        created_files.append(str(contributing_path))
        
        # Generate update script
        update_script = self._generate_update_script()
        script_path = self.base_path / 'scripts' / 'update_papers.py'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(update_script)
        created_files.append(str(script_path))
        
        return created_files
    
    def _generate_contributing_guide(self) -> str:
        """Generate CONTRIBUTING.md content."""
        return """# Contributing to Awesome PHM Papers

Thank you for your interest in contributing to this curated collection of PHM research papers!

## 🎯 Contribution Guidelines

### Paper Submission Criteria

1. **Real Academic Papers Only**
   - Must be published or preprinted papers from legitimate academic sources
   - No fictitious, generated, or hypothetical papers
   - DOI or academic URL required for verification

2. **PHM Relevance**
   - Must be directly relevant to Prognostics and Health Management
   - Should address fault diagnosis, RUL prediction, condition monitoring, or related topics
   - Industrial applications and case studies welcome

3. **Quality Standards**
   - Peer-reviewed publications strongly preferred
   - High-quality preprints from reputable sources (arXiv, etc.) acceptable
   - Must include complete abstract for categorization

### How to Contribute

#### Method 1: GitHub Issue (Recommended)
1. Create a new [GitHub Issue](https://github.com/your-username/awesome-phm-papers/issues)
2. Use the "New Paper Submission" template
3. Provide complete paper information:
   - Title, authors, year, venue
   - DOI or academic URL
   - Abstract (full text)
   - Suggested category
   - Brief relevance explanation

#### Method 2: Pull Request
1. Fork this repository
2. Add paper information to the appropriate category
3. Follow existing format and structure
4. Submit pull request with clear description

### Automated Processing

Our system uses academic-researcher agents to:
- Verify paper authenticity and metadata
- Extract complete abstracts and bibliographic information  
- Automatically categorize papers by content analysis
- Generate bidirectional links and cross-references
- Update citation counts and impact metrics

### Review Process

1. **Automated Validation** (< 1 hour)
   - Verify paper exists in academic databases
   - Check PHM relevance score
   - Validate metadata completeness

2. **Manual Review** (24-48 hours)
   - Quality assessment by maintainers
   - Category assignment verification
   - Integration with existing content

3. **Publication** (< 1 week)
   - Generate paper pages and links
   - Update category indexes
   - Rebuild bidirectional references

## 📝 Formatting Guidelines

### Paper Information Format
```
- **Title**: Complete paper title
- **Authors**: All authors with affiliations
- **Year**: Publication year
- **Venue**: Journal/Conference name
- **DOI**: Digital Object Identifier
- **Abstract**: Complete abstract text
- **Categories**: Primary and secondary categories
```

### File Naming
- Paper directories: `YEAR-FirstAuthor-TitleWords`
- Category files: `category-name/README.md`
- Index files: `by-type/README.md`

## 🚫 What Not to Submit

- Conference abstracts or workshop papers (unless substantial)
- Papers outside PHM scope (pure ML, generic IoT, etc.)
- Duplicate submissions of existing papers
- Papers without accessible abstracts or metadata
- Non-English papers (translation may be considered)

## 🔍 Quality Assurance

We maintain high standards through:
- Real-time academic database verification
- PHM relevance scoring algorithms
- Citation impact tracking
- Community peer review process
- Regular automated updates and maintenance

## 💡 Suggestions & Improvements

We welcome suggestions for:
- New paper categories or subcategories
- Improved organization or navigation
- Additional indexing dimensions
- Enhanced paper discovery methods
- Community features and tools

## 📞 Questions?

- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/awesome-phm-papers/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/awesome-phm-papers/discussions)
- 📧 **Email**: maintainer@domain.com

---

Thank you for helping build the most comprehensive collection of PHM research papers! 🙏
"""
    
    def _generate_update_script(self) -> str:
        """Generate automated update script."""
        return '''#!/usr/bin/env python3
"""
Automated Paper Discovery and Update Script for Awesome PHM Papers

This script uses the APPA system to discover new PHM papers and update
the repository with fresh content.
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add APPA system to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Note: Import AwesomePHMKnowledgeOrganizer when needed in external scripts


def discover_new_papers(config=None):
    """Discover new PHM papers using academic-researcher agent via Task tool."""
    
    # Note: This function should use the academic-researcher agent via Task tool
    # For now, return empty list - implement with actual academic search integration
    print("🔍 Paper discovery requires academic-researcher agent integration...")
    print("📚 Use academic-researcher agent via Task tool for real paper discovery")
    return []


def update_knowledge_base(papers):
    """Update the knowledge base with new papers."""
    
    if not papers:
        print("ℹ️  No papers to organize")
        return {"total_papers": 0, "categories": [], "paper_files_created": 0}
    
    # Use the organizer instance within this module
    # This should be called as a method of AwesomePHMKnowledgeOrganizer
    print("📁 This function should be called as part of the organizer workflow")
    print("   Use UpdateManager for paper updates with user confirmation")
    
    return {"total_papers": len(papers), "categories": ["placeholder"], "paper_files_created": 0}


def generate_update_report(papers, summary):
    """Generate update report for logging."""
    
    report = {
        'update_date': datetime.now().isoformat(),
        'papers_discovered': len(papers),
        'organization_summary': summary,
        'new_papers': [
            {
                'title': paper.get('title', 'Unknown'),
                'authors': paper.get('authors', [])[:3],
                'year': paper.get('year'),
                'quality_score': paper.get('quality_score', 0)
            }
            for paper in papers[:10]  # Top 10 papers
        ]
    }
    
    # Save report
    report_path = os.path.join('logs', f'update_report_{datetime.now().strftime("%Y%m%d")}.json')
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📊 Update report saved to: {report_path}")
    return report


def main():
    """Main update process."""
    
    print("🚀 Starting Awesome PHM Papers update process...")
    
    try:
        # Step 1: Discover new papers
        papers = discover_new_papers()
        
        if not papers:
            print("ℹ️  No new papers found. Repository is up to date.")
            return
        
        # Step 2: Update knowledge base
        summary = update_knowledge_base(papers)
        
        # Step 3: Generate report
        report = generate_update_report(papers, summary)
        
        print("🎉 Update process completed successfully!")
        
    except Exception as e:
        print(f"❌ Update process failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''
    
    def _generate_bibtex_entry(self, paper: Dict[str, Any]) -> str:
        """Generate a BibTeX entry for a paper using Paper model."""
        # Use the Paper model's BibTeX generation if available
        # For backward compatibility, include minimal BibTeX generation here
        try:
            from ..models import Paper, VenueType
            paper_obj = Paper(
                title=paper.get('title', 'Unknown Title'),
                authors=paper.get('authors', []),
                year=paper.get('year', datetime.now().year),
                venue=paper.get('venue', ''),
                doi=paper.get('doi', ''),
                type=VenueType.JOURNAL if paper.get('paper_type') == 'journal' else VenueType.CONFERENCE
            )
            return paper_obj.to_bibtex()
        except ImportError:
            # Fallback to simple BibTeX generation
            authors = paper.get('authors', [])
            first_author = authors[0].split()[-1] if authors else 'Unknown'
            year = paper.get('year', datetime.now().year)
            title = paper.get('title', 'Unknown Title')
            
            citation_key = f"{first_author}{year}"
            entry_type = "article" if paper.get('paper_type') == 'journal' else "inproceedings"
            
            bibtex = f"@{entry_type}{{{citation_key},\n"
            bibtex += f'  title = {{{title}}},\n'
            bibtex += f'  author = {{{" and ".join(authors[:5])}}},\n'
            bibtex += f"  year = {{{year}}},\n"
            bibtex += "}\n"
            
            return bibtex
    
    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-')


if __name__ == "__main__":
    # Test the knowledge organizer
    import tempfile
    import shutil
    
    # Create temporary directory for testing
    test_dir = tempfile.mkdtemp()
    print(f"Testing in directory: {test_dir}")
    
    try:
        # Initialize organizer
        organizer = AwesomePHMKnowledgeOrganizer(test_dir)
        
        # Create sample papers
        sample_papers = [
            {
                'title': 'Deep Learning for Bearing Fault Diagnosis',
                'authors': ['Zhang, Wei', 'Liu, Ming', 'Smith, John'],
                'year': 2024,
                'venue': 'Mechanical Systems and Signal Processing',
                'doi': '10.1016/j.ymssp.2024.123456',
                'abstract': 'This paper presents a novel deep learning approach for bearing fault diagnosis using convolutional neural networks...',
                'keywords': ['deep learning', 'fault diagnosis', 'bearing', 'CNN'],
                'paper_type': 'journal',
                'citation_count': 25,
                'phm_relevance_score': 0.95,
                'quality_score': 0.85,
                'final_score': 0.87
            },
            {
                'title': 'RUL Prediction Using LSTM Networks',
                'authors': ['Chen, Li', 'Wang, Jun'],
                'year': 2023,
                'venue': 'IEEE Transactions on Industrial Electronics',
                'doi': '10.1109/TIE.2023.654321',
                'abstract': 'Long Short-Term Memory networks are applied to remaining useful life prediction of mechanical components...',
                'keywords': ['RUL prediction', 'LSTM', 'prognostics'],
                'paper_type': 'journal',
                'citation_count': 18,
                'phm_relevance_score': 0.92,
                'quality_score': 0.82,
                'final_score': 0.84
            }
        ]
        
        # Test organization
        summary = organizer.organize_papers(sample_papers)
        
        print("✅ Test completed successfully!")
        print(f"Summary: {json.dumps(summary, indent=2)}")
        
        # List created files
        print("\n📁 Created files:")
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), test_dir)
                print(f"  {rel_path}")
        
    finally:
        # Clean up
        shutil.rmtree(test_dir)
        print(f"\n🧹 Cleaned up test directory: {test_dir}")