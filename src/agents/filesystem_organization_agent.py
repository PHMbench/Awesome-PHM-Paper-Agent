"""
File System Organization Agent for APPA system.

This agent creates and maintains standardized directory structure and file organization.

Single Responsibility: Create and maintain standardized directory structure
Input: Analyzed paper data with metadata
Output: Organized file system with consistent naming and structure
"""

import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import shutil

from .base_agent import BaseAgent, AgentError


class FileSystemOrganizationAgent(BaseAgent):
    """
    Agent responsible for organizing papers into standardized file system structure.
    
    Creates year-based organization with consistent naming conventions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, "FileSystemOrganizationAgent")
        
        # File system configuration
        self.fs_config = self.get_config_value('filesystem', {})
        self.max_folder_name_length = self.fs_config.get('max_folder_name_length', 100)
        self.invalid_chars_replacement = self.fs_config.get('invalid_chars_replacement', '-')
        self.create_backups = self.fs_config.get('create_backups', True)
        
        # Base directories using configured output directory
        self.base_dir = self.output_dir
        self.papers_dir = self.get_output_path('papers')
        self.topics_dir = self.get_output_path('topics')
        self.venues_dir = self.get_output_path('venues')
        self.authors_dir = self.get_output_path('authors')
        self.indices_dir = self.get_output_path('indices')
        
        self.logger.info("Initialized File System Organization Agent")
    
    def process(self, input_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Organize papers into file system structure.
        
        Args:
            input_data: List of analyzed paper data with metadata
        
        Returns:
            Dictionary with organization results and statistics
        """
        if not isinstance(input_data, list):
            raise AgentError("Input must be a list of analyzed paper dictionaries")
        
        self.logger.info(f"Starting file system organization for {len(input_data)} papers")
        
        organization_stats = {
            'total_papers': len(input_data),
            'organized_papers': 0,
            'failed_papers': 0,
            'created_directories': 0,
            'updated_files': 0,
            'errors': []
        }
        
        # Ensure base directories exist
        self._ensure_base_directories()
        
        # Organize each paper
        for paper in input_data:
            try:
                self._organize_paper(paper)
                organization_stats['organized_papers'] += 1
            except Exception as e:
                self.logger.error(f"Error organizing paper '{paper.get('title', 'Unknown')}': {e}")
                organization_stats['failed_papers'] += 1
                organization_stats['errors'].append({
                    'paper': paper.get('title', 'Unknown'),
                    'error': str(e)
                })
        
        # Update indices and cross-references
        self._update_indices(input_data)
        
        self.logger.info(f"File system organization completed: {organization_stats['organized_papers']} papers organized")
        
        return organization_stats
    
    def _ensure_base_directories(self) -> None:
        """Ensure all base directories exist."""
        directories = [
            self.papers_dir,
            self.topics_dir,
            self.venues_dir,
            self.authors_dir,
            self.indices_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _organize_paper(self, paper: Dict[str, Any]) -> None:
        """
        Organize individual paper into file system.
        
        Args:
            paper: Paper data with metadata and analysis
        """
        # Generate folder name
        folder_name = self._generate_folder_name(paper)
        year = paper.get('year', 0)
        
        # Create year directory
        year_dir = os.path.join(self.papers_dir, str(year))
        os.makedirs(year_dir, exist_ok=True)
        
        # Create paper directory
        paper_dir = os.path.join(year_dir, folder_name)
        os.makedirs(paper_dir, exist_ok=True)
        
        # Create paper files
        self._create_paper_index(paper, paper_dir)
        self._create_bibtex_file(paper, paper_dir)
        
        # Update topic organization
        self._update_topic_organization(paper)
        
        # Update venue organization
        self._update_venue_organization(paper)
        
        # Update author organization
        self._update_author_organization(paper)
    
    def _generate_folder_name(self, paper: Dict[str, Any]) -> str:
        """
        Generate standardized folder name for paper.
        
        Format: YYYY-VENUE-FirstAuthor-ShortTitle
        
        Args:
            paper: Paper metadata
            
        Returns:
            Sanitized folder name
        """
        year = paper.get('year', 0)
        venue = paper.get('venue', 'Unknown')
        authors = paper.get('authors', [])
        title = paper.get('title', 'Unknown')
        
        # Extract first author last name
        first_author = 'Unknown'
        if authors:
            first_author_full = authors[0]
            if ',' in first_author_full:
                first_author = first_author_full.split(',')[0].strip()
            else:
                parts = first_author_full.split()
                first_author = parts[-1] if parts else 'Unknown'
        
        # Abbreviate venue name
        venue_abbrev = self._abbreviate_venue(venue)
        
        # Create short title
        short_title = self._create_short_title(title)
        
        # Combine components
        folder_name = f"{year}-{venue_abbrev}-{first_author}-{short_title}"
        
        # Sanitize folder name
        folder_name = self._sanitize_filename(folder_name)
        
        # Ensure length limit
        if len(folder_name) > self.max_folder_name_length:
            folder_name = folder_name[:self.max_folder_name_length-3] + "..."
        
        return folder_name
    
    def _abbreviate_venue(self, venue: str) -> str:
        """Create abbreviated venue name."""
        # Common abbreviations
        abbreviations = {
            'IEEE Transactions on Reliability': 'IEEE-TR',
            'Mechanical Systems and Signal Processing': 'MSSP',
            'Reliability Engineering & System Safety': 'RESS',
            'IEEE Transactions on Industrial Electronics': 'IEEE-TIE',
            'IEEE Transactions on Instrumentation and Measurement': 'IEEE-TIM',
            'Journal of Sound and Vibration': 'JSV',
            'Expert Systems with Applications': 'ESA',
            'Engineering Applications of Artificial Intelligence': 'EAAI',
            'Computers & Industrial Engineering': 'CIE',
            'International Journal of Prognostics and Health Management': 'IJPHM'
        }
        
        # Check for exact match
        if venue in abbreviations:
            return abbreviations[venue]
        
        # Create abbreviation from first letters
        words = venue.split()
        if len(words) <= 3:
            return ''.join(word[:3] for word in words)
        else:
            return ''.join(word[0].upper() for word in words if len(word) > 2)[:6]
    
    def _create_short_title(self, title: str) -> str:
        """Create shortened title for folder name."""
        # Remove common words
        stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'using', 'based'}
        
        words = title.lower().split()
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Take first 4 meaningful words
        short_words = meaningful_words[:4]
        short_title = ''.join(word.capitalize() for word in short_words)
        
        return short_title[:30]  # Limit length
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters."""
        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*\s]'
        sanitized = re.sub(invalid_chars, self.invalid_chars_replacement, filename)
        
        # Remove multiple consecutive replacement characters
        sanitized = re.sub(f'{re.escape(self.invalid_chars_replacement)}+', self.invalid_chars_replacement, sanitized)
        
        # Remove leading/trailing replacement characters
        sanitized = sanitized.strip(self.invalid_chars_replacement)
        
        return sanitized
    
    def _create_paper_index(self, paper: Dict[str, Any], paper_dir: str) -> None:
        """Create index.md file for paper."""
        index_path = os.path.join(paper_dir, 'index.md')
        
        # Generate paper index content
        content = self._generate_paper_index_content(paper)
        
        # Write to file
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _create_bibtex_file(self, paper: Dict[str, Any], paper_dir: str) -> None:
        """Create refs.bib file for paper."""
        bibtex_path = os.path.join(paper_dir, 'refs.bib')
        
        # Generate BibTeX content
        bibtex_content = self._generate_bibtex_content(paper)
        
        # Write to file
        with open(bibtex_path, 'w', encoding='utf-8') as f:
            f.write(bibtex_content)
    
    def _generate_paper_index_content(self, paper: Dict[str, Any]) -> str:
        """Generate content for paper index.md file."""
        title = paper.get('title', 'Unknown Title')
        authors = paper.get('authors', [])
        affiliations = paper.get('affiliations', [])
        year = paper.get('year', 0)
        venue = paper.get('venue', 'Unknown Venue')
        doi = paper.get('doi', '')
        urls = paper.get('urls', {})
        keywords = paper.get('keywords', [])
        citation_count = paper.get('citation_count', 0)
        analysis = paper.get('analysis', {})
        
        # Build content
        content = f"# {title}\n\n"
        
        # Metadata section
        content += "## Metadata\n\n"
        content += f"- **Authors**: {', '.join(authors)}\n"
        if affiliations:
            content += f"- **Affiliations**: {', '.join(affiliations)}\n"
        content += f"- **Year**: {year}\n"
        content += f"- **Venue**: {venue}\n"
        content += f"- **Citations**: {citation_count}\n"
        if doi:
            content += f"- **DOI**: [{doi}](https://doi.org/{doi})\n"
        content += f"- **Keywords**: {', '.join(keywords)}\n\n"
        
        # Links section
        if urls:
            content += "## Links\n\n"
            for link_type, url in urls.items():
                if url:
                    content += f"- [{link_type.replace('_', ' ').title()}]({url})\n"
            content += "\n"
        
        # Analysis sections
        if analysis:
            # TL;DR
            tldr = analysis.get('tldr', '')
            if tldr:
                content += f"## TL;DR\n\n{tldr}\n\n"
            
            # Key Points
            key_points = analysis.get('key_points', [])
            if key_points:
                content += "## Key Points\n\n"
                for point in key_points:
                    content += f"- {point}\n"
                content += "\n"
            
            # Deep Analysis
            deep_analysis = analysis.get('deep_analysis', '')
            if deep_analysis:
                content += f"## Deep Analysis\n\n{deep_analysis}\n\n"
            
            # Topics
            topics = analysis.get('extracted_topics', [])
            if topics:
                content += "## Research Topics\n\n"
                topic_links = []
                for topic in topics:
                    topic_normalized = topic.replace(' ', '-').lower()
                    topic_links.append(f"[[../../topics/{topic_normalized}/README.md|{topic}]]")
                content += ', '.join(topic_links) + "\n\n"
            
            # Reproducibility
            repro_score = analysis.get('reproducibility_score', 0)
            if repro_score > 0:
                content += f"## Reproducibility Score\n\n{repro_score:.2f}/1.0\n\n"
        
        # Navigation
        content += "## Navigation\n\n"
        content += f"- [[../../indices/by-year.md|Browse by Year]]\n"
        content += f"- [[../../indices/by-topic.md|Browse by Topic]]\n"
        content += f"- [[../../indices/by-venue.md|Browse by Venue]]\n"
        content += f"- [[../../indices/by-citations.md|Browse by Citations]]\n"
        content += f"- [[../../venues/{self._sanitize_filename(venue.lower())}/README.md|More from {venue}]]\n\n"
        
        # Footer
        content += "---\n\n"
        content += f"*Generated by APPA on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        
        return content

    def _generate_bibtex_content(self, paper: Dict[str, Any]) -> str:
        """Generate BibTeX content for paper."""
        title = paper.get('title', '')
        authors = paper.get('authors', [])
        year = paper.get('year', 0)
        venue = paper.get('venue', '')
        doi = paper.get('doi', '')
        paper_type = paper.get('type', 'journal')

        # Generate citation key
        first_author = 'Unknown'
        if authors:
            first_author_full = authors[0]
            if ',' in first_author_full:
                first_author = first_author_full.split(',')[0].strip()
            else:
                parts = first_author_full.split()
                first_author = parts[-1] if parts else 'Unknown'

        key = f"{first_author}{year}"

        # Determine entry type
        entry_type = "article" if paper_type == "journal" else "inproceedings"

        # Build BibTeX entry
        bibtex_lines = [f"@{entry_type}{{{key},"]
        bibtex_lines.append(f"  title = {{{title}}},")
        bibtex_lines.append(f"  author = {{{' and '.join(authors)}}},")
        bibtex_lines.append(f"  year = {{{year}}},")

        if paper_type == "journal":
            bibtex_lines.append(f"  journal = {{{venue}}},")
        else:
            bibtex_lines.append(f"  booktitle = {{{venue}}},")

        if doi:
            bibtex_lines.append(f"  doi = {{{doi}}},")

        urls = paper.get('urls', {})
        if urls.get('pdf'):
            bibtex_lines.append(f"  url = {{{urls['pdf']}}},")

        bibtex_lines.append("}")

        return '\n'.join(bibtex_lines)

    def _update_topic_organization(self, paper: Dict[str, Any]) -> None:
        """Update topic-based organization."""
        analysis = paper.get('analysis', {})
        topics = analysis.get('extracted_topics', [])

        for topic in topics:
            topic_normalized = topic.replace(' ', '-').lower()
            topic_dir = os.path.join(self.topics_dir, topic_normalized)
            os.makedirs(topic_dir, exist_ok=True)

            # Update topic README
            self._update_topic_readme(topic, topic_dir, paper)

    def _update_venue_organization(self, paper: Dict[str, Any]) -> None:
        """Update venue-based organization."""
        venue = paper.get('venue', '')
        if venue:
            venue_normalized = self._sanitize_filename(venue.lower())
            venue_dir = os.path.join(self.venues_dir, venue_normalized)
            os.makedirs(venue_dir, exist_ok=True)

            # Update venue README
            self._update_venue_readme(venue, venue_dir, paper)

    def _update_author_organization(self, paper: Dict[str, Any]) -> None:
        """Update author-based organization."""
        authors = paper.get('authors', [])

        for author in authors:
            author_normalized = self._sanitize_filename(author.lower().replace(', ', '-'))
            author_dir = os.path.join(self.authors_dir, author_normalized)
            os.makedirs(author_dir, exist_ok=True)

            # Update author README
            self._update_author_readme(author, author_dir, paper)

    def _update_topic_readme(self, topic: str, topic_dir: str, paper: Dict[str, Any]) -> None:
        """Update topic README file."""
        readme_path = os.path.join(topic_dir, 'README.md')

        # Read existing content or create new
        existing_papers = []
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract existing paper references (simplified)
                existing_papers = re.findall(r'\[\[([^\]]+)\]\]', content)

        # Add new paper reference
        year = paper.get('year', 0)
        folder_name = self._generate_folder_name(paper)
        paper_link = f"../papers/{year}/{folder_name}/index.md"

        if paper_link not in existing_papers:
            # Generate new content
            content = self._generate_topic_readme_content(topic, existing_papers + [paper_link])

            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def _update_venue_readme(self, venue: str, venue_dir: str, paper: Dict[str, Any]) -> None:
        """Update venue README file."""
        readme_path = os.path.join(venue_dir, 'README.md')

        # Similar implementation to topic README
        # For brevity, using simplified version
        content = f"# {venue}\n\nPapers published in this venue:\n\n"
        content += f"- [[../papers/{paper.get('year', 0)}/{self._generate_folder_name(paper)}/index.md|{paper.get('title', 'Unknown')}]]\n"

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _update_author_readme(self, author: str, author_dir: str, paper: Dict[str, Any]) -> None:
        """Update author README file."""
        readme_path = os.path.join(author_dir, 'README.md')

        # Similar implementation to topic README
        # For brevity, using simplified version
        content = f"# {author}\n\nPapers by this author:\n\n"
        content += f"- [[../papers/{paper.get('year', 0)}/{self._generate_folder_name(paper)}/index.md|{paper.get('title', 'Unknown')}]]\n"

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_topic_readme_content(self, topic: str, paper_links: List[str]) -> str:
        """Generate content for topic README file."""
        content = f"# {topic.title()}\n\n"
        content += f"Research papers related to {topic}:\n\n"

        for link in paper_links:
            # Extract title from link (simplified)
            title = link.split('/')[-2].replace('-', ' ')
            content += f"- [[{link}|{title}]]\n"

        content += f"\n---\n\n*Updated on {datetime.now().strftime('%Y-%m-%d')}*"

        return content

    def _update_indices(self, papers: List[Dict[str, Any]]) -> None:
        """Update all index files."""
        self._update_year_index(papers)
        self._update_topic_index(papers)
        self._update_venue_index(papers)
        self._update_citation_index(papers)

    def _update_year_index(self, papers: List[Dict[str, Any]]) -> None:
        """Update by-year index."""
        index_path = os.path.join(self.indices_dir, 'by-year.md')

        # Group papers by year
        papers_by_year = {}
        for paper in papers:
            year = paper.get('year', 0)
            if year not in papers_by_year:
                papers_by_year[year] = []
            papers_by_year[year].append(paper)

        # Generate content
        content = "# Papers by Year\n\n"
        content += f"Total papers: {len(papers)}\n\n"

        for year in sorted(papers_by_year.keys(), reverse=True):
            content += f"## {year}\n\n"
            for paper in papers_by_year[year]:
                folder_name = self._generate_folder_name(paper)
                title = paper.get('title', 'Unknown')
                content += f"- [[../papers/{year}/{folder_name}/index.md|{title}]]\n"
            content += "\n"

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _update_topic_index(self, papers: List[Dict[str, Any]]) -> None:
        """Update by-topic index."""
        # Implementation similar to year index
        pass

    def _update_venue_index(self, papers: List[Dict[str, Any]]) -> None:
        """Update by-venue index."""
        # Implementation similar to year index
        pass

    def _update_citation_index(self, papers: List[Dict[str, Any]]) -> None:
        """Update by-citation index."""
        # Implementation similar to year index
        pass


if __name__ == "__main__":
    # Test the agent
    config = {
        'filesystem': {
            'max_folder_name_length': 100,
            'invalid_chars_replacement': '-',
            'create_backups': True
        }
    }
    
    agent = FileSystemOrganizationAgent(config)
    
    test_paper = {
        'title': 'Deep Learning for Bearing Fault Diagnosis',
        'authors': ['Smith, John', 'Doe, Jane'],
        'affiliations': ['University A', 'University B'],
        'year': 2023,
        'venue': 'IEEE Transactions on Industrial Electronics',
        'doi': '10.1109/test.2023.123456',
        'urls': {'pdf': 'https://example.com/paper.pdf'},
        'keywords': ['deep learning', 'fault diagnosis'],
        'citation_count': 25,
        'analysis': {
            'tldr': 'This paper presents deep learning for bearing fault diagnosis.',
            'key_points': ['Novel CNN approach', 'High accuracy results'],
            'deep_analysis': 'Detailed analysis of the methodology...',
            'extracted_topics': ['deep learning', 'fault diagnosis'],
            'reproducibility_score': 0.8
        }
    }
    
    result = agent.run([test_paper])
    print(f"Organization completed: {result}")
